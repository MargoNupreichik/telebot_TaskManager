# внешние библиотеки
import telebot

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
    print(message.chat.id, message.from_user.username)
    # пользователь впервые запустил бота - сохраняем id чата с ними в бд
    if not pg_db.find_user_by_chat_id(message.chat.id):
        pg_db.insert_new_user(message.chat.id, message.from_user.username)
        
    # приветственное сообщение.    
    bot.reply_to(message, posts.greetings)

# отлавливаем команду /help
@bot.message_handler(commands=['help'])
def getting_info(message):
    bot.reply_to(message, posts.help_inf)

# bot launching
bot.polling(none_stop=True, interval=0)