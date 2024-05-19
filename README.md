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
    nano inventory
    ```

3. **Запустите playbook:**
    ```bash
    ansible-playbook playbook_tg_bot.yml
    ```
    
**P.s. Для повышения безопасности лучше будет, если на удаленных хостах имеются пользователи ansible:**
```bash
# Для начала создайте пользователя 
adduser ansible
```
    
 ```bash
 # Предоставьте созданному пользователю выполнять команды с повышенными привилегиями  
 visudo

 # Внутри открывшегося файла sudoers необходимо внести строку
 ansible ALL=(ALL:ALL) NOPASSWD:ALL
 ```

**P.s. возможно придётся создать и активировать виртуальное окружение для Python в Linux:**
```bash
cd devops_tg_bot    
```

```bash
python3 -m venv .venv
source .venv/bin/activate
```

```bash
# Далее выполняйте команду
ansible-playbook playbook_tg_bot.yml
```
