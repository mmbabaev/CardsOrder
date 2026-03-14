#!/bin/bash
# Скрипт развертывания Card Kingdom Order Bot на сервер Яндекс Облака
# 
# Этот скрипт:
# 1. Создает архив с кодом бота
# 2. Копирует его на удаленный сервер
# 3. Распаковывает и устанавливает зависимости
# 4. Настраивает systemd сервис для автозапуска
# 5. Перезапускает бота

set -e  # Остановка при ошибке

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ====== НАСТРОЙКИ ======
# Заполните эти переменные перед использованием
SERVER="84.201.152.61"              # IP адрес или домен сервера
SSH_KEY="$HOME/.ssh/kara_ssh_key"           # Путь к SSH ключу
REMOTE_USER="kara"           # Пользователь на сервере
REMOTE_DIR="/home/kara/CardsOrder"  # Директория проекта на сервере

# Локальные переменные
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARCHIVE_NAME="cards-order-bot-$(date +%Y%m%d-%H%M%S).tar.gz"
TEMP_ARCHIVE="/tmp/$ARCHIVE_NAME"

# ====== ФУНКЦИИ ======
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Проверка, что скрипт запущен из правильной директории
check_directory() {
    if [[ ! -f "$SCRIPT_DIR/bot.py" ]]; then
        print_error "Скрипт должен находиться в директории bot/"
        exit 1
    fi
    print_success "Проверка директории пройдена"
}

# Проверка переменных
check_variables() {
    if [[ "$SERVER" == "your-server-ip" ]]; then
        print_error "Установите IP адрес сервера в переменной SERVER"
        exit 1
    fi
    if [[ "$SSH_KEY" == "~/.ssh/your_key" ]]; then
        print_error "Установите путь к SSH ключу в переменной SSH_KEY"
        exit 1
    fi
    print_success "Проверка переменных пройдена"
}

# Создание архива
create_archive() {
    print_info "Создание архива с кодом бота..."
    
    cd "$SCRIPT_DIR"
    
    # Создаем архив, исключая ненужные файлы
    tar -czf "$TEMP_ARCHIVE" \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='*.log' \
        --exclude='.pytest_cache' \
        --exclude='node_modules' \
        bot.py \
        bot_handlers.py \
        bot_parser_service.py \
        requirements-bot.txt \
        .env.example \
        systemd/
    
    print_success "Архив создан: $TEMP_ARCHIVE"
}

# Копирование на сервер
copy_to_server() {
    print_info "Копирование архива на сервер..."
    
    scp -i "$SSH_KEY" "$TEMP_ARCHIVE" "$REMOTE_USER@$SERVER:/tmp/" || {
        print_error "Не удалось скопировать архив на сервер"
        exit 1
    }
    
    print_success "Архив скопирован на сервер"
}

# Установка на сервере
install_on_server() {
    print_info "Установка на сервере..."
    
    ssh -i "$SSH_KEY" "$REMOTE_USER@$SERVER" << EOF
        set -e
        
        echo "→ Создание директорий..."
        mkdir -p $REMOTE_DIR/bot
        
        echo "→ Распаковка архива..."
        cd $REMOTE_DIR
        tar -xzf /tmp/$ARCHIVE_NAME -C bot/
        
        echo "→ Создание виртуального окружения..."
        if [ ! -d "$REMOTE_DIR/venv" ]; then
            python3 -m venv $REMOTE_DIR/venv
        fi
        
        echo "→ Установка зависимостей..."
        $REMOTE_DIR/venv/bin/pip install --upgrade pip
        $REMOTE_DIR/venv/bin/pip install -r $REMOTE_DIR/bot/requirements-bot.txt
        
        echo "→ Проверка .env файла..."
        if [ ! -f "$REMOTE_DIR/bot/.env" ]; then
            echo "ВНИМАНИЕ: Создайте .env файл на основе .env.example!"
            cp $REMOTE_DIR/bot/.env.example $REMOTE_DIR/bot/.env
        fi
        
        echo "→ Установка systemd сервиса..."
        sudo cp $REMOTE_DIR/bot/systemd/cards-order-bot.service /etc/systemd/system/
        sudo systemctl daemon-reload
        
        echo "→ Активация и запуск сервиса..."
        sudo systemctl enable cards-order-bot
        sudo systemctl restart cards-order-bot
        
        echo "→ Очистка временных файлов..."
        rm /tmp/$ARCHIVE_NAME
        
        echo "✓ Установка завершена"
EOF
    
    if [ $? -eq 0 ]; then
        print_success "Бот успешно установлен и запущен на сервере"
    else
        print_error "Произошла ошибка при установке на сервере"
        exit 1
    fi
}

# Проверка статуса бота
check_status() {
    print_info "Проверка статуса бота..."
    
    ssh -i "$SSH_KEY" "$REMOTE_USER@$SERVER" << EOF
        echo "=== Статус сервиса ==="
        sudo systemctl status cards-order-bot --no-pager
        echo ""
        echo "=== Последние 20 строк логов ==="
        sudo journalctl -u cards-order-bot -n 20 --no-pager
EOF
}

# Очистка локальных временных файлов
cleanup() {
    print_info "Очистка временных файлов..."
    rm -f "$TEMP_ARCHIVE"
    print_success "Временные файлы удалены"
}

# ====== ОСНОВНОЙ СЦЕНАРИЙ ======
main() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Card Kingdom Order Bot - Развертывание   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    
    check_directory
    check_variables
    
    # Запрос подтверждения
    echo -e "${YELLOW}Сервер: $SERVER${NC}"
    echo -e "${YELLOW}Пользователь: $REMOTE_USER${NC}"
    echo -e "${YELLOW}Директория: $REMOTE_DIR${NC}"
    echo ""
    read -p "Продолжить развертывание? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Развертывание отменено"
        exit 0
    fi
    
    # Выполнение развертывания
    create_archive
    copy_to_server
    install_on_server
    check_status
    cleanup
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║       Развертывание завершено успешно!    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Полезные команды:${NC}"
    echo -e "  Просмотр логов:     ${GREEN}ssh $REMOTE_USER@$SERVER 'sudo journalctl -u cards-order-bot -f'${NC}"
    echo -e "  Перезапуск бота:    ${GREEN}ssh $REMOTE_USER@$SERVER 'sudo systemctl restart cards-order-bot'${NC}"
    echo -e "  Остановка бота:     ${GREEN}ssh $REMOTE_USER@$SERVER 'sudo systemctl stop cards-order-bot'${NC}"
    echo -e "  Статус:             ${GREEN}ssh $REMOTE_USER@$SERVER 'sudo systemctl status cards-order-bot'${NC}"
    echo ""
}

# Запуск основного сценария
main