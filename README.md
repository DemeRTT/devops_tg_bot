# Развертывание проекта с использованием Ansible

Для развертывания проекта с помощью Ansible выполните следующие шаги (выполнить с правами администратора):

1. **Склонируйте репозиторий и перейдите в папку проекта:**
    ```bash
    git clone https://github.com/DemeRTT/devops_tg_bot.git -b ansible
    cd devops_tg_bot
    ```

2. **Измените файл hosts:**
    ```bash
    # Пропишите токен тг-бота, хосты, пользователей к хостам и их пароли
    nano hosts
    ```

3. **Запустите playbook:**
    ```bash
    
    ```

**P.s. возможно придётся создать и активировать виртуальное окружение для Python в Linux:**
```bash
cd devops_tg_bot    
```

```bash
python3 -m venv .venv
source .venv/bin/activate   
```
