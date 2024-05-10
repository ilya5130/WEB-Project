import logging
import telebot
import sqlite3
import csv
from io import StringIO


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

# Список ID администраторов
admin_ids = [1680017325, 780925405]

TARIFF_COLD_WATER = 41.41
TARIFF_HOT_WATER = 31.24

# Функция для проверки, является ли пользователь администратором
def is_admin(user_id):
    return user_id in admin_ids

# Обработчик команды /delete_user для администраторов
@bot.message_handler(commands=['delete_user'])
def delete_user(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        # Получаем ID пользователя для удаления
        user_to_delete = message.text.split()[1] if len(message.text.split()) > 1 else ''
        if user_to_delete:
            try:
                user_to_delete = int(user_to_delete)
                with sqlite3.connect('water_readings.db') as conn:
                    cursor = conn.cursor()
                    # Удаляем пользователя из таблицы apartments
                    cursor.execute("DELETE FROM apartments WHERE id=?", (user_to_delete,))
                    conn.commit()
                    bot.reply_to(message, f"Пользователь с ID {user_to_delete} удален из базы данных.")
            except ValueError:
                bot.reply_to(message, "Пожалуйста, укажите корректный ID пользователя.")
            except sqlite3.Error as e:
                bot.reply_to(message, f"🤔 Ошибка базы данных: {e}")
        else:
            bot.reply_to(message, "Пожалуйста, укажите ID пользователя для удаления.")
    else:
        bot.reply_to(message, "❌ Извините, у вас нет прав для выполнения этой команды.")


# Функция для создания CSV-файла с показаниями счетчиков
def create_counters_report():
    with sqlite3.connect('water_readings.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM water_readings")
        readings = cursor.fetchall()

        # Создаем файл в памяти
        output = StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Записываем заголовки столбцов
        writer.writerow(['ID', 'Apartment ID', 'Hot Water', 'Cold Water'])

        # Записываем данные
        for row in readings:
            writer.writerow(row)

        # Перемещаем указатель в начало файла
        output.seek(0)

        return output

# Обработчик команды /send_report для администраторов
@bot.message_handler(commands=['send_report'])
def send_report(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        report_file = create_counters_report()
        bot.send_document(message.chat.id, ('water_counters_report.csv', report_file.getvalue()))
        report_file.close()
    else:
        bot.reply_to(message, "❌ Извините, у вас нет прав для выполнения этой команды.")

# Обработчик команды /admin
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        bot.reply_to(message, "Добро пожаловать в админ-панель 🎫! Вот доступные опции:\n"
                              "/reset_counters - сбросить показания счетчиков 🔄\n"
                              "/delete_user <ID пользователя> - удалить пользователя по его ID 🆔\n"
                              "/send_report - для отправки отчета 📄\n"
                              "/get_users - получить список всех пользователей 📃\n")
    else:
        bot.reply_to(message, "❌ Извините, у вас нет доступа к админ-панели.")

# Обработчик команды /reset_counters для администраторов
@bot.message_handler(commands=['reset_counters'])
def reset_counters(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        water_counters['hot'] = 0
        water_counters['cold'] = 0
        bot.reply_to(message, "Показания счетчиков успешно сброшены. 🔄")
    else:
        bot.reply_to(message, "❌ Извините, у вас нет прав для выполнения этой команды.")

# Обработчик команды /get_users для администраторов
@bot.message_handler(commands=['get_users'])
def get_users(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        with sqlite3.connect('water_readings.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM apartments")
            users = cursor.fetchall()
            reply_message = "📃 Список всех пользователей и их квартир:\n"
            for user in users:
                reply_message += f"ID: {user[0]}, Номер квартиры: {user[1]}\n"
            bot.reply_to(message, reply_message)
    else:
        bot.reply_to(message, "❌ Извините, у вас нет прав для просмотра списка пользователей.")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Привет!👋🏻 Я бот 🤖 для записи показаний счетчиков воды; '
                          'Отправь /help, ✏ чтобы увидеть доступные команды.')
    with open('start.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, '🚩 Доступные команды:\n'
                          '1️⃣ /status - получить текущие показания счетчиков\n'
                          '2️⃣ /register <номер квартиры> - зарегистрировать квартиру\n'
                          '3️⃣ /help - список доступных команд\n'
                          '4️⃣ /pay - оплата за месяц\n'
                          '5️⃣ /send_data <холодная> <горячая> - записать показания\n')


@bot.message_handler(commands=['send_data'])
def send_data(message):
    try:
        command_parts = message.text.split()
        cold_water_value = float(command_parts[1])
        hot_water_value = float(command_parts[2])
        user_id = message.from_user.id

        with sqlite3.connect('water_readings.db') as conn:
            cursor = conn.cursor()
            apartment_id = get_registered_apartment_id(cursor, user_id)
            if apartment_id:
                cursor.execute("INSERT INTO water_readings (apartment_id, cold_water, hot_water) VALUES (?, ?, ?)", (apartment_id, cold_water_value, hot_water_value))
                conn.commit()
                water_counters['hot'] = hot_water_value
                water_counters['cold'] = cold_water_value
                bot.reply_to(message, f"✔ Показания успешно записаны: холодная вода - {cold_water_value}, горячая вода - {hot_water_value}")
            else:
                bot.reply_to(message, '❌ Сначала зарегистрируйте квартиру с помощью команды /register')
    except (IndexError, ValueError):
        bot.reply_to(message, 'Используйте команду в формате: /send_data <показания холодной воды> <показания горячей воды>')


# Обработчик команды /status
@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, f'🔄 Текущие показания счетчиков:\n'
                          f'♨ Горячая вода: {water_counters["hot"]}\n'
                          f'❄ Холодная вода: {water_counters["cold"]}')

@bot.message_handler(commands=['pay'])
def pay_water(message):
    user_id = message.from_user.id
    with sqlite3.connect('water_readings.db') as conn:
        cursor = conn.cursor()
        apartment_id = get_registered_apartment_id(cursor, user_id)
        if apartment_id:
            cursor.execute('SELECT cold_water, hot_water FROM water_readings WHERE apartment_id=? ORDER BY id DESC LIMIT 2', (apartment_id,))
            readings = cursor.fetchall()
            if len(readings) == 2:
                current_month, last_month = readings
                cold_water_difference = current_month[0] - last_month[0]
                hot_water_difference = current_month[1] - last_month[1]

                cold_water_cost = cold_water_difference * TARIFF_COLD_WATER
                hot_water_cost = hot_water_difference * TARIFF_HOT_WATER
                total_cost = cold_water_cost + hot_water_cost

                bot.reply_to(message, f'Показания за прошлый месяц: холодная вода - {last_month[0]}, горячая вода - {last_month[1]}\n'
                             f'Показания за текущий месяц: холодная вода - {current_month[0]}, горячая вода - {current_month[1]}\n'
                             f'Разница: холодная вода - {cold_water_difference}, горячая вода - {hot_water_difference}\n'
                             f'Тариф за холодную воду: {TARIFF_COLD_WATER} руб.\n'
                             f'Тариф за горячую воду: {TARIFF_HOT_WATER} руб.\n'
                             f'Стоимость холодной воды: {cold_water_cost} руб.\n'
                             f'Стоимость горячей воды: {hot_water_cost} руб.\n'
                             f'**Общая сумма к оплате: {total_cost} руб.**\n')
            else:
                bot.reply_to(message, "Недостаточно данных для расчета. Пожалуйста, отправьте показания за оба месяца.")
        else:
            bot.reply_to(message, "❌ Сначала зарегистрируйте квартиру с помощью команды /register")

def get_registered_apartment_id(cursor, user_id):
    cursor.execute("SELECT number FROM apartments WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None


# Обработчик команды /register
@bot.message_handler(commands=['register'])
def register_apartment(message):
    try:
        user_id = message.from_user.id
        try:
            apartment_number = int(message.text.split()[1])
            with sqlite3.connect('water_readings.db') as conn:
                cursor = conn.cursor()
                registered_apartment = get_registered_apartment_id(cursor, user_id)
                if registered_apartment:
                    bot.reply_to(message, f'❌ Вы уже зарегистрировали квартиру {registered_apartment}!')
                    bot.reply_to(message,
                                 '/send_data <холодная> <горячая> - записать показания 📋♨❄\n')
                else:
                    cursor.execute("INSERT INTO apartments (id, number) VALUES (?, ?)", (user_id, apartment_number))
                    conn.commit()
                    bot.reply_to(message, f'📑 Квартира {apartment_number} успешно зарегистрирована!')
                    bot.reply_to(message,
                              '/send_data <холодная> <горячая> - записать показания 📋❄♨\n')
        except ValueError:
            bot.reply_to(message, 'Используйте команду в формате: /register <номер квартиры>')
    except IndexError:
        bot.reply_to(message, 'Используйте команду в формате: /register <номер квартиры>')


# Обработчик неизвестной команды
@bot.message_handler(func=lambda message: True)
def unknown(message):
    bot.reply_to(message, "Извините, я не понимаю эту команду 😥")

# Запускаем бота
bot.polling()
