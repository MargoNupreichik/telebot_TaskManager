# внешние библиотеки
import telebot
import telebot_calendar
from datetime import datetime
from dateutil.parser import parse

# доп. библиотеки
from local_settings import bot_access_data as b_ad

# работа с базами данных
import postgres_api as pg_db
import mongodb_api as m_db

# файл со всеми типовыми сообщениями пользователю
import helpful_messages as posts

# подключение к боту с помощью токена
bot = telebot.TeleBot(b_ad['access_token'])

# отлавливаем команду /start
@bot.message_handler(commands=['start'])
def getting_started(message):
    
    # пользователь впервые запустил бота - сохраняем id чата с ними в бд
    if not pg_db.find_user_by_chat_id(message.chat.id):
        pg_db.insert_new_user(message.chat.id, message.from_user.username)
        
    # приветственное сообщение.    
    bot.reply_to(message, posts.greetings)

# отлавливаем команду /help
@bot.message_handler(commands=['help'])
def getting_info(message):
    bot.reply_to(message, posts.help_inf)

# отлавливаем команду /new_task
@bot.message_handler(commands=['new_task'])
def getting_info(message):
    # уведомляем о начале заполнения карточки задачи
    bot.send_message(message.chat.id, posts.new_task_text_instruction1, parse_mode="Markdown")
    bot.register_next_step_handler(message, date_step1)

def date_step1(message):
    try:
        date = parse(message.text)
        bot.send_message(message.chat.id, 'Дата введена.')
        bot.send_message(message.chat.id, posts.new_task_text_instruction2)
        bot.register_next_step_handler(message, title_step2)
    except ValueError:
        bot.send_message(message.chat.id, 'Не верный формат даты, необходимо ДД-ММ-ГГГГ.')
        bot.register_next_step_handler(message, date_step1)

def title_step2(message):
    pass

# bot launching
bot.polling(none_stop=True, interval=0)