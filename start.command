#!/bin/bash
cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"

echo "=== Task Tracker Launcher ==="

# 1. Проверка Python 3
if ! command -v python3 &> /dev/null; then
    echo "ОШИБКА: Python 3 не найден."
    echo "Установите его с https://www.python.org/downloads/"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi
echo "Python: $(python3 --version)"

# 2. Виртуальное окружение
if [ ! -d "venv" ]; then
    echo "Создаю виртуальное окружение (первый запуск)..."
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Установка зависимостей
if [ ! -f "venv/.deps_installed" ]; then
    echo "Устанавливаю зависимости (может занять пару минут)..."
    pip install --upgrade pip

    echo "Устанавливаю psycopg2-binary..."
    pip install psycopg2-binary==2.9.10
    if [ $? -ne 0 ]; then
        echo ""
        echo "ОШИБКА: psycopg2-binary не установился."
        echo "Выполните в Терминале: brew install postgresql"
        echo "Затем запустите start.command снова."
        read -p "Нажмите Enter для выхода..."
        exit 1
    fi

    echo "Устанавливаю остальные зависимости..."
    pip install -r backend/requirements.txt
    if [ $? -ne 0 ]; then
        echo "ОШИБКА: зависимости из backend/requirements.txt не установились."
        read -p "Нажмите Enter для выхода..."
        exit 1
    fi

    touch venv/.deps_installed
    echo "Зависимости установлены."
fi

# 4. Переменные окружения
set -a
source "$PROJECT_ROOT/.env"
set +a
export STORAGE_PATH="$PROJECT_ROOT/data/uploads"
mkdir -p "$STORAGE_PATH"

# 5. Миграции (из папки backend, где лежит alembic.ini)
echo "Применяю миграции..."
cd "$PROJECT_ROOT/backend"
python -m alembic upgrade head
if [ $? -ne 0 ]; then
    echo "ОШИБКА: миграции не применились. Проверьте DATABASE_URL в .env"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi
cd "$PROJECT_ROOT"

# 6. Запуск сервера
echo "Запускаю сервер..."
cd "$PROJECT_ROOT/backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!
cd "$PROJECT_ROOT"

sleep 3
open "http://127.0.0.1:8000"

echo ""
echo "Сервер запущен. Браузер должен открыться автоматически."
echo "Чтобы остановить — закройте это окно Терминала."
echo ""

wait $SERVER_PID