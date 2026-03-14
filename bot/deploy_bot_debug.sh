#!/bin/bash
# Скрипт развертывания Card Kingdom Order Bot
# По умолчанию — DEBUG. Передайте --release для production.
#
# Использование:
#   bash deploy_bot_debug.sh           # debug (default)
#   bash deploy_bot_debug.sh --release # production

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ====== РЕЖИМ ======
MODE="debug"
if [[ "$1" == "--release" ]]; then
    MODE="release"
fi

# ====== НАСТРОЙКИ ======
if [[ "$MODE" == "debug" ]]; then
    SERVER="158.160.9.28"
    SSH_KEY="$HOME/.ssh/ssh-key-kara"
    REMOTE_USER="mbabaev"
    REMOTE_DIR="/home/mbabaev/CardsOrderDebug"
    SERVICE_NAME="cards-order-bot-debug"
    ENV_FILE=".env.debug"
    SYSTEMD_SERVICE="cards-order-bot-debug.service"
    OTEL_SERVICE="otel-collector-debug.service"
    OTEL_SERVICE_NAME="otel-collector-debug"
else
    SERVER="84.201.152.61"
    SSH_KEY="$HOME/.ssh/kara_ssh_key"
    REMOTE_USER="kara"
    REMOTE_DIR="/home/kara/CardsOrder"
    SERVICE_NAME="cards-order-bot"
    ENV_FILE=".env"
    SYSTEMD_SERVICE="cards-order-bot.service"
    OTEL_SERVICE="otel-collector.service"
    OTEL_SERVICE_NAME="otel-collector"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE_NAME="cards-order-bot-${MODE}-$(date +%Y%m%d-%H%M%S).tar.gz"
TEMP_ARCHIVE="/tmp/$ARCHIVE_NAME"

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${YELLOW}→ $1${NC}"; }

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

check_directory() {
    if [[ ! -f "$PROJECT_ROOT/src/bot/bot.py" ]]; then
        print_error "src/bot/bot.py не найден. Запустите скрипт из директории bot/"
        exit 1
    fi
    print_success "Проверка директории пройдена"
}

check_variables() {
    if [[ ! -f "$SCRIPT_DIR/$ENV_FILE" ]]; then
        print_error "Файл $ENV_FILE не найден."
        exit 1
    fi
    print_success "Проверка переменных пройдена"
}

create_archive() {
    print_info "Создание архива..."

    cd "$PROJECT_ROOT"
    tar -czf "$TEMP_ARCHIVE" \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env*' \
        --exclude='*.log' \
        --exclude='.pytest_cache' \
        --exclude='tests/' \
        --exclude='venv/' \
        bot/requirements-bot.txt \
        bot/systemd/ \
        otel-collector.yaml \
        src/

    print_success "Архив создан: $TEMP_ARCHIVE"
}

copy_to_server() {
    print_info "Копирование на сервер..."

    scp -i "$SSH_KEY" "$TEMP_ARCHIVE" "$REMOTE_USER@$SERVER:/tmp/"
    scp -i "$SSH_KEY" "$SCRIPT_DIR/$ENV_FILE" "$REMOTE_USER@$SERVER:/tmp/.env.deploy"

    print_success "Файлы скопированы на сервер"
}

install_on_server() {
    print_info "Установка на сервере..."

    ssh -i "$SSH_KEY" "$REMOTE_USER@$SERVER" << EOF
        set -e

        echo "→ Создание директорий..."
        mkdir -p $REMOTE_DIR

        echo "→ Распаковка архива..."
        tar -xzf /tmp/$ARCHIVE_NAME -C $REMOTE_DIR/

        echo "→ Установка .env..."
        cp /tmp/.env.deploy $REMOTE_DIR/bot/.env
        rm /tmp/.env.deploy

        echo "→ Установка python3-venv..."
        sudo apt-get update -q
        sudo apt-get install -y python3-venv -q

        echo "→ Создание виртуального окружения..."
        rm -rf $REMOTE_DIR/venv
        python3 -m venv $REMOTE_DIR/venv

        echo "→ Установка зависимостей..."
        $REMOTE_DIR/venv/bin/pip install --upgrade pip -q
        $REMOTE_DIR/venv/bin/pip install -r $REMOTE_DIR/bot/requirements-bot.txt -q

        echo "→ Установка otelcol (если не установлен)..."
        if [ ! -f /usr/local/bin/otelcol ]; then
            OTELCOL_VERSION="0.114.0"
            wget -q "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v\${OTELCOL_VERSION}/otelcol_\${OTELCOL_VERSION}_linux_amd64.tar.gz" -O /tmp/otelcol.tar.gz
            tar -xzf /tmp/otelcol.tar.gz -C /tmp otelcol
            sudo mv /tmp/otelcol /usr/local/bin/otelcol
            sudo chmod +x /usr/local/bin/otelcol
            rm /tmp/otelcol.tar.gz
            echo "  otelcol установлен: \$(otelcol --version)"
        else
            echo "  otelcol уже установлен: \$(otelcol --version)"
        fi

        echo "→ Установка systemd сервисов..."
        sudo cp $REMOTE_DIR/bot/systemd/$OTEL_SERVICE /etc/systemd/system/
        sudo cp $REMOTE_DIR/bot/systemd/$SYSTEMD_SERVICE /etc/systemd/system/
        sudo systemctl daemon-reload

        echo "→ Активация и запуск OTel Collector..."
        sudo systemctl enable $OTEL_SERVICE_NAME
        sudo systemctl restart $OTEL_SERVICE_NAME

        echo "→ Активация и запуск бота..."
        sudo systemctl enable $SERVICE_NAME
        sudo systemctl restart $SERVICE_NAME

        echo "→ Очистка временных файлов..."
        rm /tmp/$ARCHIVE_NAME

        echo "✓ Установка завершена"
EOF

    print_success "Бот успешно установлен и запущен"
}

check_status() {
    print_info "Проверка статуса бота..."

    ssh -i "$SSH_KEY" "$REMOTE_USER@$SERVER" << EOF
        echo "=== Статус сервиса ==="
        sudo systemctl status $SERVICE_NAME --no-pager
        echo ""
        echo "=== Последние 20 строк логов ==="
        sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
EOF
}

cleanup() {
    rm -f "$TEMP_ARCHIVE"
    print_success "Временные файлы удалены"
}

main() {
    echo ""
    if [[ "$MODE" == "debug" ]]; then
        echo -e "${YELLOW}╔════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║  Card Kingdom Order Bot - DEBUG Deploy    ║${NC}"
        echo -e "${YELLOW}╚════════════════════════════════════════════╝${NC}"
    else
        echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  Card Kingdom Order Bot - RELEASE Deploy  ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    fi
    echo ""

    check_directory
    check_variables

    echo -e "${YELLOW}Режим:      $MODE${NC}"
    echo -e "${YELLOW}Сервер:     $SERVER${NC}"
    echo -e "${YELLOW}Сервис:     $SERVICE_NAME${NC}"
    echo -e "${YELLOW}Директория: $REMOTE_DIR${NC}"
    echo ""
    read -p "Развернуть? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Развертывание отменено"
        exit 0
    fi

    create_archive
    copy_to_server
    install_on_server
    check_status
    cleanup

    echo ""
    echo -e "${YELLOW}Полезные команды:${NC}"
    echo -e "  Логи:      ${GREEN}ssh -i $SSH_KEY $REMOTE_USER@$SERVER 'sudo journalctl -u $SERVICE_NAME -f'${NC}"
    echo -e "  Рестарт:   ${GREEN}ssh -i $SSH_KEY $REMOTE_USER@$SERVER 'sudo systemctl restart $SERVICE_NAME'${NC}"
    echo -e "  Остановка: ${GREEN}ssh -i $SSH_KEY $REMOTE_USER@$SERVER 'sudo systemctl stop $SERVICE_NAME'${NC}"
    echo ""
}

main
