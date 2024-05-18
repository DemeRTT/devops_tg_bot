# Развертывание проекта с использованием контейнеров

Для развертывания проекта с помощью контейнеров выполните следующие шаги (выполнить с правами администратора):

1. **Склонируйте репозиторий и перейдите в папку проекта:**
    ```bash
    git clone https://github.com/DemeRTT/devops_tg_bot.git -b docker
    cd devops_tg_bot
    ```

2. **Создайте и заполните `.env` файл.**

3. **Создайте образы Docker:**
    ```bash
    # Перейдите в папку bot и создайте образ
    cd bot
    docker build -t bot_image .
    ```

    ```bash
    # Перейдите в папку db и создайте образ
    cd ../db
    docker build -t db_image .
    ```

    ```bash
    # Перейдите в папку db_repl и создайте образ
    cd ../db_repl
    docker build -t db_repl_image .
    ```

5. **Запустите контейнеры:**
    ```bash
    cd ..
    docker compose up -d
    ```
