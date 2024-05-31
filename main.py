# внешние библиотеки
import telebot
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import datetime, date, time, timedelta
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
    
    calendar, step = DetailedTelegramCalendar(min_date=date.today(), locale="ru").build()
    bot.send_message(message.chat.id, posts.new_task_text_instruction1, parse_mode="Markdown")
    bot.send_message(message.chat.id, 'Введите год', reply_markup=calendar)

@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(с):
    
    result, key, step = DetailedTelegramCalendar().process(с.data)
    if not result and key:
        step_ru = ""
        if LSTEP[step] == "year":
            step_ru = 'год'
        elif LSTEP[step] == "month":
            step_ru = 'месяц'
        elif LSTEP[step] == "day":
            step_ru = 'день'    
        bot.edit_message_text(f"Выберите {step_ru}",
                              с.message.chat.id,
                              с.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"Введена дата: {result}",
                              с.message.chat.id,
                              с.message.message_id)
        bot.send_message(с.message.chat.id, posts.new_task_text_instruction1_1)
        bot.register_next_step_handler(с.message, time_step1_1, result)
        

def time_step1_1(message, data):   
    try:        
        hours, minutes = int(message.text.split(':')[0]), int(message.text.split(':')[1])
        
        if hours < 0 or hours > 24 or minutes < 0 or minutes > 60:
            raise ValueError('hours or minutes are out of possible range')
        
        new_data = datetime.combine(data, time(hour=hours, minute=minutes))
        
        bot.send_message(message.chat.id, 'Время введено.')
        bot.send_message(message.chat.id, posts.new_task_text_instruction2)
        bot.register_next_step_handler(message, title_step2, new_data)
        
    except ValueError:
        bot.send_message(message.chat.id, 'Введите время без ошибок (часы в диапазоне от 0 до 24, минуты в диапазоне от 0 до 60).')
        bot.register_next_step_handler(message, time_step1_1, data)
    
    except TypeError:
        bot.send_message(message.chat.id, 'Введите данные согласно шаблону.')
        bot.register_next_step_handler(message, time_step1_1, data)

    
def title_step2(message, date):
    if message.content_type == 'text':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton("Да")
        btn2 = telebot.types.KeyboardButton("Нет")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, posts.new_task_text_instruction3, reply_markup=markup)
        bot.register_next_step_handler(message, notes_step3, date, message.text)             
    else:
        bot.send_message(message.chat.id, "Введите текст.")
        bot.register_next_step_handler(message, title_step2)     

def notes_step3(message, date, title):
    if message.text == "Да":
        bot.send_message(message.chat.id, posts.new_task_text_instruction4)
        bot.register_next_step_handler(message, media_step4, date, title)             
    elif message.text == "Нет":
        task = pg_db.Task(date, title=title)
        saving_step5(message, task)  
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton("Да")
        btn2 = telebot.types.KeyboardButton("Нет")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, "Команда не распознана. Воспользуйтесь кнопками.", reply_markup=markup)
         
def media_step4(message, date, title):
    task = pg_db.Task(date, title=title, chatID=message.chat.id)
    
    bot.send_message(message.chat.id, posts.new_task_text_instruction5)
    bot.register_next_step_handler(message, saving_step5, task)        

# Функции ввода дополнительных файлов
def input_json_files(message):
    pass


def saving_step5(message, task_obj):
    task_obj.console_print()
    bot.send_message(message.chat.id, posts.new_task_text_instruction6)
         
# bot launching
bot.polling(none_stop=True, interval=0)