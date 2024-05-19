import paramiko
import psycopg2
import logging
import re
from dotenv import load_dotenv
import os
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv()

TOKEN = os.getenv('TOKEN')

SSH_HOST = os.getenv('RM_HOST')
SSH_PORT = os.getenv('RM_PORT')
SSH_USERNAME = os.getenv('RM_USERNAME')
SSH_PASSWORD = os.getenv('RM_PASSWORD')

DB_DATABASE = os.getenv('DB_DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')  
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

version = os.getenv('POSTGRES_VERSION')

phoneNumberList = []
emailAddrList = []

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет, {user.full_name}! Чтобы ознакомиться с функционалом бота, введите /help')


def helpCommand(update: Update, context):
    help_text = """
    Список доступных команд:
    /start - Начать взаимодействие с ботом
    /help - Получить справку о доступных командах
    /find_phone_number - Найти телефонные номера в тексте
    /find_email - Найти email-адреса в тексте
    /verify_password - Проверить сложность пароля
    
    Список команд при SSH-подключении:
    /get_release - Релиз системы
    /get_uname - Архитектура процессора и версия ядра 
    /get_uptime - Время работы
    /get_df - Состояние файловой системы
    /get_free - Состояние оперативной памяти 
    /get_mpstat - Производительность системы
    /get_w - Пользователи в системе
    /get_auths - Последние 10 входов в систему
    /get_critical - Последние 5 критических события
    /get_ps - Запущенные процессы 
    /get_ss - Используемые порты
    /get_apt_list - Установленные пакеты
    /get_services - Запущенные сервисы
    /get_repl_logs - Логи о репликации БД
    /get_phone_numbers - Телефонные номера из БД
    /get_emails - Электронные почты из БД
    """
    update.message.reply_text(help_text)

def echo(update: Update, context):
    update.message.reply_text('Введите любую из доступных команд, ознакомиться с которыми можно с помощью /help !')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'


def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r'(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}') 
    
    global phoneNumberList
    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END # Завершаем выполнение функции
    
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' # Записываем очередной номер

    update.message.reply_text('Найденные номера телефонов: ')      
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю

    update.message.reply_text("Записать найденные телефонные номера в базу данных? (да или нет)")
    return 'save_phone_number_to_db'

def findEmailAddrCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска Email-адресов: ')
    return 'find_email'


def findEmailAddr (update: Update, context):
    user_input = update.message.text # Получаем текст

    emailAddrRegex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b') 

    global emailAddrList
    emailAddrList = emailAddrRegex.findall(user_input) # Ищем Email-адреса

    if not emailAddrList: # Обрабатываем случай, когда Email-адресов нет
        update.message.reply_text('Email-адреса не найдены')
        return ConversationHandler.END # Завершаем выполнение функции
    
    emailAddr = '' # Создаем строку, в которую будем записывать Email-адреса
    for i in range(len(emailAddrList)):
        emailAddr += f'{i+1}. {emailAddrList[i]}\n' # Записываем очередной Email-адрес

    update.message.reply_text('Найденные Email-адреса: ')    
    update.message.reply_text(emailAddr) # Отправляем сообщение пользователю
    
    update.message.reply_text("Записать найденные Email-адреса в базу данных? (да или нет)")
    return 'save_email_to_db'

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки сложности: ')
    return 'verify_password'

def verifyPassword(update: Update, context):
    user_input = update.message.text

    if len(user_input) < 8:
        update.message.reply_text('Пароль простой') # Пароль должен содержать не менее восьми символов.
        return ConversationHandler.END

    if not re.search(r'[A-Z]', user_input):
        update.message.reply_text('Пароль простой') # Пароль должен включать как минимум одну заглавную букву
        return ConversationHandler.END

    if not re.search(r'[a-z]', user_input):
        update.message.reply_text('Пароль простой') # Пароль должен включать хотя бы одну строчную букву
        return ConversationHandler.END

    if not re.search(r'\d', user_input):
        update.message.reply_text('Пароль простой') # Пароль должен включать хотя бы одну цифру
        return ConversationHandler.END

    if not re.search(r'[!@#$%^&*()]', user_input):
        update.message.reply_text('Пароль простой') # Пароль должен включать хотя бы один специальный символ, такой как !@#$%^&*()
        return ConversationHandler.END

    update.message.reply_text('Пароль сложный')
    return ConversationHandler.END

def get_release(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("lsb_release -a")
        release_info = stdout.read().decode("utf-8")
        update.message.reply_text(release_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_uname(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("uname -a")
        uname_info = stdout.read().decode("utf-8")
        update.message.reply_text(uname_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_uptime(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("uptime")
        uptime_info = stdout.read().decode("utf-8")
        update.message.reply_text(uptime_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_df(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("df -h")
        df_info = stdout.read().decode("utf-8")
        update.message.reply_text(df_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_free(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("free -m")
        free_info = stdout.read().decode("utf-8")
        update.message.reply_text(free_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_mpstat(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("mpstat")
        mpstat_info = stdout.read().decode("utf-8")
        update.message.reply_text(mpstat_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_w(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("w")
        w_info = stdout.read().decode("utf-8")
        update.message.reply_text(w_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_auths(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("last -n 10")
        auths_info = stdout.read().decode("utf-8")
        update.message.reply_text(auths_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_critical(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("journalctl -r -p crit -n 5 | head -n 10")
        critical_info = stdout.read().decode("utf-8")
        update.message.reply_text(critical_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_ps(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("ps aux | head -n 10")
        ps_info = stdout.read().decode("utf-8")
        update.message.reply_text(ps_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_ss(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("ss -tuln")
        ss_info = stdout.read().decode("utf-8")
        update.message.reply_text(ss_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_apt_list(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    update.message.reply_text("""Вывести все установленные пакеты или какой-то конкретный?
                              1.Все пакеты
                              2.Конкретный пакет
                              
                              !!!Введите 1 или 2!!!
                              """)
    return 'get_apt_list_command'


def get_apt_list_command(update: Update, context):
    user_input = update.message.text
    
    if user_input == '1':
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
            stdin, stdout, stderr = ssh_client.exec_command("apt list --installed | head -n 20")
            apt_list_info = stdout.read().decode("utf-8")
            update.message.reply_text(apt_list_info)
        except Exception as e:
            update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
        finally:
            ssh_client.close()
        return ConversationHandler.END
    
    elif user_input == '2': 
        update.message.reply_text('Введите название пакета:')
        return 'apt_list'
    
    else:
        update.message.reply_text('Неправильный ввод варианта!')
        return ConversationHandler.END
    
def apt_list(update: Update, context):
    packet = update.message.text
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command(f"apt list --installed {packet}")
        apt_list_info = stdout.read().decode("utf-8")
        update.message.reply_text(apt_list_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()
    return ConversationHandler.END

def get_services(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command("systemctl | head -n 20")
        services_info = stdout.read().decode("utf-8")
        update.message.reply_text(services_info)
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def get_repl_logs(update: Update, context):
    if SSH_HOST == "" or SSH_USERNAME == "" or SSH_PASSWORD == "":
        update.message.reply_text("Параметры SSH подключения не заданы.")
        return
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
        stdin, stdout, stderr = ssh_client.exec_command(f'cat /var/log/postgresql/postgresql-{version}-main.log | tail -n 20')
        data = stdout.read() + stderr.read()
        data = str(data.decode('utf-8')).replace('\\n', '\n').replace('\\t', '\t')[:-1]
        update.message.reply_text(data[-4000:])
    except Exception as e:
        update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    finally:
        ssh_client.close()

def connect_to_db():
    try:
        # Подключение к базе данных
        connection = psycopg2.connect(
            dbname=DB_DATABASE,  
            user=DB_USER, 
            password=DB_PASSWORD,  
            host=DB_HOST,  
            port=DB_PORT  
        )
        return connection
    except psycopg2.Error as e:
        print("Ошибка подключения к базе данных:", e)


# Функция для получения списка email-адресов из базы данных
def get_emails(update: Update, context):
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute("SELECT email FROM emails")  # Выборка email-адресов из таблицы emails
        emails = cursor.fetchall()
        if emails:
            email_list = "\n".join(email[0] for email in emails)
            update.message.reply_text("Email адреса:\n" + email_list)  # Отправка списка email-адресов пользователю
        else:
            update.message.reply_text("В базе данных нет email-адресов.")  # Если в базе нет email-адресов
    except psycopg2.Error as e:
        update.message.reply_text(f"Ошибка при получении электорнных почт из базы данных: {str(e)}")
    finally:
        cursor.close()
        connection.close()


# Функция для получения списка номеров телефонов из базы данных
def get_phone_numbers(update: Update, context):
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute("SELECT phone_number FROM phone_numbers")  # Выборка номеров телефонов из таблицы phone_numbers
        phone_numbers = cursor.fetchall()
        if phone_numbers:
            phone_number_list = "\n".join(phone_number[0] for phone_number in phone_numbers)
            update.message.reply_text("Телефонные номера:\n" + phone_number_list)  # Отправка списка номеров телефонов пользователю
        else:
            update.message.reply_text("В базе данных нет телефонных номеров.")  # Если в базе нет номеров телефонов
    except psycopg2.Error as e:
        update.message.reply_text(f"Ошибка при получении телефонных номеров из базы данных: {str(e)}")
    finally:
        cursor.close()
        connection.close()

def save_phone_number_to_db(update: Update, context):
    answer = update.message.text.lower()
    if answer in ["да", "yes"]:
        global phoneNumberList

        for phone_number in phoneNumberList:
            try:
                connection = connect_to_db()
                cursor = connection.cursor()

                # Проверяем, существует ли уже такой номер телефона в базе данных
                cursor.execute("SELECT * FROM phone_numbers WHERE phone_number = %s", (phone_number,))
                existing_phone = cursor.fetchone()
                if existing_phone:
                    update.message.reply_text(f"Номер телефона {phone_number} уже существует в базе данных.")
                    continue

                # Если номер телефона не существует, выполняем вставку
                cursor.execute("INSERT INTO phone_numbers (phone_number) VALUES (%s)", (phone_number,))
                connection.commit()
                update.message.reply_text(f"Номер телефона {phone_number} успешно записан в базу данных.")

            except psycopg2.Error as error:
                update.message.reply_text(f"Ошибка добавления телефонных номеров в базу данных: {str(error)}")
            finally:
                cursor.close()
                connection.close()

    return ConversationHandler.END

def save_email_to_db(update: Update, context):
    answer = update.message.text.lower()
    if answer in ["да", "yes"]:
        global emailAddrList

        for email in emailAddrList:
            try:
                connection = connect_to_db()
                cursor = connection.cursor()

                # Проверяем, существует ли уже такой email в базе данных
                cursor.execute("SELECT * FROM emails WHERE email = %s", (email,))
                existing_email = cursor.fetchone()
                if existing_email:
                    update.message.reply_text(f"Электронная почта {email} уже существует в базе данных.")
                    continue

                # Если email не существует, выполняем вставку
                cursor.execute("INSERT INTO emails (email) VALUES (%s)", (email,))
                connection.commit()
                update.message.reply_text(f"Электронная почта {email} успешно записана в базу данных.")

            except psycopg2.Error as error:
                update.message.reply_text(f"Ошибка добавления электронной почты в базу данных: {str(error)}")
            finally:
                cursor.close()
                connection.close()

    return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandler = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand),
                      CommandHandler('find_email', findEmailAddrCommand),
                      CommandHandler('verify_password', verifyPasswordCommand),
                      CommandHandler('get_apt_list', get_apt_list)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmailAddr)],
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
            'get_apt_list_command': [MessageHandler(Filters.text & ~Filters.command, get_apt_list_command)],
            'apt_list': [MessageHandler(Filters.text & ~Filters.command, apt_list)],
            'save_phone_number_to_db': [MessageHandler(Filters.text & ~Filters.command, save_phone_number_to_db)],
            'save_email_to_db': [MessageHandler(Filters.text & ~Filters.command, save_email_to_db)],
        },
        fallbacks=[]
    )
		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(convHandler)
		
	# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
