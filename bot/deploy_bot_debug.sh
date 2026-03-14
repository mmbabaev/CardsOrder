#!/bin/bash
# Скрипт развертывания DEBUG версии Card Kingdom Order Bot
# Использует отдельный сервер и бота, не влияет на production

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ====== DEBUG НАСТРОЙКИ ======
SERVER="YOUR_DEBUG_SERVER_IP"       # IP адрес debug сервера
SSH_KEY="$HOME/.ssh/kara_ssh_key"   # SSH ключ (тот же или отдельный)
REMOTE_USER="kara"                  # Пользователь на debug сервере
REMOTE_DIR="/home/kara/CardsOrderDebug"  # Отдельная директория

SERVICE_NAME="cards-order-bot-debug"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARCHIVE_NAME="cards-order-bot-debug-$(date +%Y%m%d-%H%M%S).tar.gz"
TEMP_ARCHIVE="/tmp/$ARCHIVE_NAME"

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${YELLOW}→ $1${NC}"; }

check_directory() {
    if [[ ! -f "$SCRIPT_DIR/bot.py" ]]; then
        print_error "Скрипт должен находиться в директории bot/"
        exit 1
    fi
    print_success "Проверка директории пройдена"
}

check_variables() {
    if [[ "$SERVER" == "YOUR_DEBUG_SERVER_IP" ]]; then
        print_error "Установите IP адрес debug сервера в переменной SERVER"
        exit 1
    fi
    if [[ ! -f "$SCRIPT_DIR/.env.debug" ]]; then
        print_error "Файл .env.debug не найден. Создайте его на основе .env.debug.example"
        exit 1
    fi
    print_success "Проверка переменных пройдена"
}

create_archive() {
    print_info "Создание архива с кодом бота..."

    cd "$SCRIPT_DIR"
    tar -czf "$TEMP_ARCHIVE" \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='.env.debug' \
        --exclude='*.log' \
        --exclude='.pytest_cache' \
        bot.py \
        bot_handlers.py \
        bot_parser_service.py \
        requirements-bot.txt \
        systemd/

    print_success "Архив создан: $TEMP_ARCHIVE"
}

copy_to_server() {
    print_info "Копирование на debug сервер..."

    scp -i "$SSH_KEY" "$TEMP_ARCHIVE" "$REMOTE_USER@$SERVER:/tmp/"
    scp -i "$SSH_KEY" "$SCRIPT_DIR/.env.debug" "$REMOTE_USER@$SERVER:/tmp/.env.debug"

    print_success "Файлы скопированы на сервер"
}

install_on_server() {
    print_info "Установка на debug сервере..."

    ssh -i "$SSH_KEY" "$REMOTE_USER@$SERVER" << EOF
        set -e

        echo "→ Создание директорий..."
        mkdir -p $REMOTE_DIR/bot

        echo "→ Распаковка архива..."
        tar -xzf /tmp/$ARCHIVE_NAME -C $REMOTE_DIR/bot/

        echo "→ Установка .env.debug..."
        cp /tmp/.env.debug $REMOTE_DIR/bot/.env
        rm /tmp/.env.debug

        echo "→ Создание виртуального окружения..."
        if [ ! -d "$REMOTE_DIR/venv" ]; then
            python3 -m venv $REMOTE_DIR/venv
        fi

        echo "→ Установка зависимостей..."
        $REMOTE_DIR/venv/bin/pip install --upgrade pip -q
        $REMOTE_DIR/venv/bin/pip install -r $REMOTE_DIR/bot/requirements-bot.txt -q

        echo "→ Установка systemd сервиса..."
        sudo cp $REMOTE_DIR/bot/systemd/cards-order-bot-debug.service /etc/systemd/system/
        sudo systemctl daemon-reload

        echo "→ Активация и запуск сервиса..."
        sudo systemctl enable $SERVICE_NAME
        sudo systemctl restart $SERVICE_NAME

        echo "→ Очистка временных файлов..."
        rm /tmp/$ARCHIVE_NAME

        echo "✓ Установка завершена"
EOF

    print_success "Debug бот успешно установлен и запущен"
}

check_status() {
    print_info "Проверка статуса debug бота..."

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
    echo -e "${YELLOW}╔════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  Card Kingdom Order Bot - DEBUG Deploy    ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════╝${NC}"
    echo ""

    check_directory
    check_variables

    echo -e "${YELLOW}Сервер:     $SERVER${NC}"
    echo -e "${YELLOW}Сервис:     $SERVICE_NAME${NC}"
    echo -e "${YELLOW}Директория: $REMOTE_DIR${NC}"
    echo ""
    read -p "Развернуть DEBUG бота? (y/n) " -n 1 -r
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
    echo -e "  Логи:        ${GREEN}ssh $REMOTE_USER@$SERVER 'sudo journalctl -u $SERVICE_NAME -f'${NC}"
    echo -e "  Рестарт:     ${GREEN}ssh $REMOTE_USER@$SERVER 'sudo systemctl restart $SERVICE_NAME'${NC}"
    echo -e "  Остановка:   ${GREEN}ssh $REMOTE_USER@$SERVER 'sudo systemctl stop $SERVICE_NAME'${NC}"
    echo ""
}

main
