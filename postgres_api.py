
import sqlalchemy as alch
from sqlalchemy.orm import Session
from datetime import datetime

# здесь хранятся данные для подключения к бд
from local_settings import postgres_db as settings

def get_engine(user, passwd, host, port, db):

    """
    Функция get_engine, создающая движок для подключения к базе данных

    :param user: str
    :param passwd: str
    :param host: str
    :param port: str
    :param db: str
    
    """

    url: str = 'postgresql://' + user + ':' + passwd + '@' + host + ':' + port + '/' + db
    # echo=True - все запросы будут дублироваться в консоль
    # pool_size=5, max_overflow=10 - ограничения по пулингу подключения
    engine: alch.engine.Engine = alch.create_engine(url, pool_size=5, echo=True, max_overflow=10)
    return engine

def get_engine_from_session():

    """
    Функция get_engine_from_session, создающая движок для подключения к базе данных.
    Является оберткой для функции get_engine_from_session, в которой дополнительно берутся и проверяются данные о базе.
    
    """

    keys = ['pguser', 'pgpassword', 'pghost', 'pgport', 'pgdb']
    if not all(key in keys for key in settings.keys()):
        raise Exception('Bad config file.')
    return get_engine(settings['pguser'], settings['pgpassword'], settings['pghost'],
                      settings['pgport'], settings['pgdb'])

engine = get_engine_from_session()

# Описание таблиц
metadata_obj = alch.MetaData()

users = alch.Table('TelegramUsers', metadata_obj,
                   alch.Column('chatID', alch.BigInteger, primary_key=True),
                   alch.Column('username', alch.String))

todolist = alch.Table('UsersTODOList', metadata_obj,
                   alch.Column('chatID', alch.BigInteger),
                   alch.Column('deadline_date', alch.Date),
                   alch.Column('status', alch.Text),
                   alch.Column('description', alch.Text),
                   alch.Column('id', alch.Integer, primary_key=True, autoincrement=True))

# Объект для хранения задачи
class Task:
    
    # пользователь хочет ввести более подробные сведения о задаче    
    def __init__(self, deadline, title = 'none', chatID=-1) -> None:
        self.deadline = deadline
        self.title = title
        self.status = "in_process"
        if chatID == -1:
            self.description_filename = ''
        else:
            self.description_filename = str(chatID) + "." + str(deadline) + "." + title
        
    def console_print(self):
        print('дедлайн: {date}, тема: {title}, статус: {status}, название файла: {filename}'.format( 
                     date=self.deadline, title=self.title, status=self.status, filename=self.description_filename))
            
# Запросы к бд

def insert_new_user(users_id, users_nickname='none'):
    
    with Session(autoflush=False, bind=engine) as session:
        ins = users.insert().values(chatID=users_id, username=users_nickname)
        print(ins)
        result = session.execute(ins)
        session.commit()   

def find_user_by_chat_id(users_id):
    
    """
    Запрос к БД с целью выяснить, есть ли ID чата с этим пользователем.
    
    """
    with Session(autoflush=False, bind=engine) as session:
        sel = users.select().where(users.c.chatID == users_id)
        print(sel)
        result = session.execute(sel)
        
        # Найдена ли запись в бд с ID чата или нет.
        if result.first()==None:
            return False
        else:
            return True