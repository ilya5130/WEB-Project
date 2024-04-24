import logging
import telebot
import sqlite3

# Включаем логирование для получения информации о возможных ошибках
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализируем бота с помощью токена
bot = telebot.TeleBot("7095480877:AAHet48wIKiuecFPkaTTL8FcabqJ5x_3bEY")

# Словарь для хранения показаний счетчиков
water_counters = {'hot': 0, 'cold': 0}

# Глобальные переменные для подключения к базе данных и курсора
conn = sqlite3.connect('water_readings.db')
cursor = conn.cursor()

# Создаем таблицу для квартир, если она не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS apartments
                  (id INTEGER PRIMARY KEY, number INTEGER)''')

# Создаем таблицу для хранения показаний счетчиков, если она не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS water_readings
                  (id INTEGER PRIMARY KEY, apartment_id INTEGER, hot_water INTEGER, cold_water INTEGER,
                   FOREIGN KEY(apartment_id) REFERENCES apartments(id))''')

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Привет! Я бот для записи показаний счетчиков воды. '
                          'Отправь /help, чтобы увидеть доступные команды.')

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, 'Доступные команды:\n'
                          '/status - получить текущие показания счетчиков\n'
                          '/register <номер квартиры> - зарегистрировать квартиру\n'
                          '/help - список доступных команд\n')


@bot.message_handler(commands=['hot'])
def hot_water(message):
    try:
        value = float(message.text.split()[1])
        user_id = message.from_user.id
        with sqlite3.connect('water_readings.db') as conn:
            cursor = conn.cursor()
            apartment_id = get_registered_apartment_id(cursor, user_id)
            if apartment_id:
                cursor.execute("INSERT INTO water_readings (apartment_id, hot_water) VALUES (?, ?)", (apartment_id, value))
                value = float(message.text.split()[1])
                water_counters['hot'] = value
                conn.commit()
                bot.reply_to(message, f'Показание счетчика горячей воды успешно записано: {value}')
            else:
                bot.reply_to(message, 'Сначала зарегистрируйте квартиру с помощью команды /register')
    except (IndexError, ValueError):
        bot.reply_to(message, 'Используйте команду в формате: /hot <показание>')


@bot.message_handler(commands=['cold'])
def cold_water(message):
    try:
        value = float(message.text.split()[1])
        user_id = message.from_user.id
        with sqlite3.connect('water_readings.db') as conn:
            cursor = conn.cursor()
            apartment_id = get_registered_apartment_id(cursor, user_id)
            if apartment_id:
                cursor.execute("INSERT INTO water_readings (apartment_id, cold_water) VALUES (?, ?)", (apartment_id, value))
                value = float(message.text.split()[1])
                water_counters['cold'] = value
                conn.commit()
                bot.reply_to(message, f'Показание счетчика холодной воды успешно записано: {value}')
            else:
                bot.reply_to(message, 'Сначала зарегистрируйте квартиру с помощью команды /register')
    except (IndexError, ValueError):
        bot.reply_to(message, 'Используйте команду в формате: /cold <показание>')



# Обработчик команды /status
@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, f'Текущие показания счетчиков:\n'
                          f'Горячая вода: {water_counters["hot"]}\n'
                          f'Холодная вода: {water_counters["cold"]}')

def get_registered_apartment_id(cursor, user_id):
    cursor.execute("SELECT number FROM apartments WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None


# Обработчик команды /register
@bot.message_handler(commands=['register'])
def register_apartment(message):
    try:
        user_id = message.from_user.id
        apartment_number = message.text.split()[1]
        with sqlite3.connect('water_readings.db') as conn:
            cursor = conn.cursor()
            registered_apartment = get_registered_apartment_id(cursor, user_id)
            if registered_apartment:
                bot.reply_to(message, f'Вы уже зарегистрировали квартиру {registered_apartment}.')
                bot.reply_to(message,
                             '/hot <показание> - записать показание счетчика горячей воды\n'
                             '/cold <показание> - записать показание счетчика холодной воды\n')
            else:
                cursor.execute("INSERT INTO apartments (id, number) VALUES (?, ?)", (user_id, apartment_number))
                conn.commit()
                bot.reply_to(message, f'Квартира {apartment_number} успешно зарегистрирована.')
                bot.reply_to(message,
                          '/hot <показание> - записать показание счетчика горячей воды\n'
                          '/cold <показание> - записать показание счетчика холодной воды\n')
    except IndexError:
        bot.reply_to(message, 'Используйте команду в формате: /register <номер квартиры>')


# Обработчик неизвестной команды
@bot.message_handler(func=lambda message: True)
def unknown(message):
    bot.reply_to(message, "Извините, я не понимаю эту команду.")

# Запускаем бота
bot.polling()
