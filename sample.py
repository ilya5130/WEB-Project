import telebot
import sqlite3
from telebot import types

bot = telebot.TeleBot("6650052223:AAH0wnWOyGIJpov8k3fWLJ0btfal2vXO2Pg")



@bot.message_handler(commands=['start'])
def button(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    item1 = types.InlineKeyboardButton('Кто ты?', callback_data='question1')
    item2 = types.InlineKeyboardButton('Пока', callback_data='delete')
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Привет!", reply_markup=markup)



def start(message):
    connect = sqlite3.connect('users.db')
    cursor = connect.cursor()

    cursor.execute("""CREATE TABLE  IF NOT EXISTS login_id(id INTEGER)""")

    connect.commit()

    people_id = message.chat.id
    cursor.execute(f"SELECT id FROM login_id WHERE id = {people_id}")
    data = cursor.fetchone()
    if data is None:
        user_id = [message.chat.id]
        cursor.execute("INSERT INTO login_id VALUES(?);", user_id)
        connect.commit()
    else:
        bot.send_message(message.chat.id, "Пользователь с таким id уже существует в базе данных!")


@bot.message_handler(commands=['delete'])
def delete(message):
    connect = sqlite3.connect('users.db')
    cursor = connect.cursor()
    people_id = message.chat.id
    cursor.execute(f"DELETE FROM login_id WHERE id = {people_id}")
    connect.commit()


@bot.callback_query_handler(func=lambda call:True)
def callback(call):
    if call.message:
        if call.data == "question1":
            bot.send_message(call.message.chat.id, "Я бот")

bot.polling()
