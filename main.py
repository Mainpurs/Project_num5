import logging
import telebot
import sqlite3
import requests
from sql import prepare_database, add_user, update_row_value, delete_user, user_in, get_data_for_user
from gpt import ask_gpt
from telebot.types import KeyboardButton, ReplyKeyboardMarkup

TOKEN = "6907816424:AAFtptMbHmk8FH4w39qBW7Zy1533IKPiPEM"
bot = telebot.TeleBot(TOKEN)
db_file = 'sqliteData.db'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)


def menu_keyboard(text_1, text_2):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    # добавляем кнопочки с вариантами ответа
    answer_1 = KeyboardButton(text=text_1)
    answer_2 = KeyboardButton(text=text_2)
    keyboard.add(answer_1, answer_2)
    # возвращаем готовую клавиатуру с кнопочками
    return keyboard


MAX_PROJECT_TOKENS = 2500  # макс. количество токенов на весь проект
MAX_USERS = 2  # макс. количество пользователей на весь проект
MAX_SESSIONS = 3  # макс. количество сессий у пользователя
MAX_TOKENS_IN_SESSION = 500  # макс. количество токенов за сессию пользователя
tokens = 0

AIM_token = 't1.9euelZrOmZnNxpuKyIrIjJbIiYrMx-3rnpWakMyPl8-Xic6RxpyKnZmXjc3l8_dXcn9P-e8-SGYH_t3z9xchfU_57z5IZgf-zef1656Vms7HjIrOk5zHyZmSmJmQmsrM7_zF656Vms7HjIrOk5zHyZmSmJmQmsrMveuelZqSnseRjY6Tz56YxpyXyZOdkbXehpzRnJCSj4qLmtGLmdKckJKPioua0pKai56bnoue0oye.y_DzD7uzBGcKTSu36EuWLbCAeu1NeZ68XLt068OVn9_tH3vPsUUr54yERLTt8aVl8vHM2eh1fNsXNPwKfES0DA'
folder_id = 'b1gvnnljiqfne8s69smp'
GPT_MODEL = 'yandexgpt-lite'

CONTINUE_STORY = 'Продолжи сюжет в 1-3 предложения и оставь интригу. Не пиши никакой пояснительный текст от себя'
END_STORY = 'Напиши завершение истории c неожиданной развязкой. Не пиши никакой пояснительный текст от себя'

SYSTEM_PROMPT = (
    "Ты пишешь историю вместе с человеком. "
    "Историю вы пишете по очереди. Начинает человек, а ты продолжаешь. "
    "Если это уместно, ты можешь добавлять в историю диалог между персонажами. "
    "Диалоги пиши с новой строки и отделяй тире. "
    "Не пиши никакого пояснительного текста в начале, а просто логично продолжай историю"
)

# ----------------------------------------------------------------------------------------------------------------------


system1 = 'Portal2 - Вселенная где существует подземный комплекс Aperture laboratories под упревлением ИИ - GlaDOS'
system2 = 'Cyberpunk - Продвинутый город, где выживают сильнейшие, ну или очень верткие'


# ---------------------------------кол-во-токенов-в-тесте-(text)--------------------------------------------------------
def count_tokens(text):
    headers = {  # заголовок запроса, в котором передаем IAM-токен
        'Authorization': f'Bearer {AIM_token}',  # token - наш IAM-токен
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{folder_id}/{GPT_MODEL}/latest",  # указываем folder_id
        "maxTokens": MAX_PROJECT_TOKENS,
        "text": text  # text - тот текст, в котором мы хотим посчитать токены
    }
    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize",
            json=data,
            headers=headers
        ).json()['tokens']
    )  # здесь, после выполнения запроса, функция возвращает количество токенов в text


# ----------------------------------------------------------------------------------------------------------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    prepare_database()  # создаем таблицу

    # ------------------------------------------------------------------------------------------------------------------
    x = get_data_for_user(db_file, user_id)
    if x == False:
        add_user(db_file, user_id, status=0, admin=0, user_content='', Tema='', GG='', assisnant_content='', system_content='', tokens=0)
    else:
        update_row_value(db_file, user_id, column_name='user_content', new_value='')
        update_row_value(db_file, user_id, column_name='Tema', new_value='')
        update_row_value(db_file, user_id, column_name='GG', new_value='')
        update_row_value(db_file, user_id, column_name='assisnant_content', new_value='')
        update_row_value(db_file, user_id, column_name='system_content', new_value='')
        update_row_value(db_file, user_id, column_name='status', new_value=0)
    # ------------------------------------------------------------------------------------------------------------------

    bot.send_message(user_id, 'Привет, я генератор сценариев!')
    msg = bot.send_message(user_id, "Выбери сеттинг:\n"
                                    "Portal2 - Вселенная где существует подземный комплекс Aperture laboratories под упревлением ИИ\n"
                                    "Cyberpunk - Продвинутый город, где выживают сильнейшие, ну или очень верткие",
                           reply_markup=menu_keyboard('Portal2', 'Cyberpunk'))

    result = get_data_for_user(db_file, user_id)
    if result['GG'] != 1 or 2:
        bot.send_message(user_id, 'Ограниченное кол-во пользователей!')
        return
    if result['tokens'] >= MAX_TOKENS_IN_SESSION:
        bot.send_message(user_id, 'Ограниченное кол-во токенов!')
        logging.info(f'Закончелись токены у {user_id}')
        return

    if message.text == 'Portal2':
        Tema = system1
    elif message.text == 'Cyberpunk':
        Tema = system2
    else:
        return

    update_row_value(db_file, user_id, column_name='Tema', new_value=Tema)

    bot.register_next_step_handler(msg, GG)


def GG(message):
    user_id = message.chat.id
    result = get_data_for_user(db_file, user_id)

    if result['Tema'] == system1:
        msg = bot.send_message(user_id, 'Выбери Глав_Героя!',
                               reply_markup=menu_keyboard('Чел', 'Дагратмен'))
    else:
        msg = bot.send_message(user_id, 'Выбери Глав_Героя!',
                               reply_markup=menu_keyboard('Ви', 'Джеки'))

    GG = message.text  # GG == ГГ == Главный герой
    update_row_value(db_file, user_id, column_name='GG', new_value=GG)
    bot.register_next_step_handler(msg, new_story)


def new_story(message):
    user_id = message.chat.id

    msg = bot.send_message(user_id, 'Напиши начало истории!')

    start_history = message.text
    update_row_value(db_file, user_id, column_name='user_content', new_value=start_history)

    user_content = get_data_for_user(db_file, user_id)['user_content']
    system_content = get_data_for_user(db_file, user_id)['system_content']
    assistant_content = get_data_for_user(db_file, user_id)['assisntant_content']
    print(user_content)
    print(system_content)
    print(assistant_content)

    # -------------------------------------------------------------------------------
    text = user_content + system_content + assistant_content
    print(text)
    tokens = count_tokens(text)
    print(tokens)
    update_row_value(db_file, user_id, column_name=['tokens'], new_value=tokens)
    if tokens >= MAX_TOKENS_IN_SESSION:
        bot.send_message(user_id, 'У вас кончелись токены, приходите {дата обновления токенов}.')
        logging.info(f'Закончелись токены у {user_id}')
        return
    # -------------------------------------------------------------------------------

    bot.register_next_step_handler(msg, ask_gpt(user_content, system_content, assistant_content, user_id))  # tokens

# =====================================================Продолжение======================================================


@bot.message_handler(commands=['continue'])
def fcontinue(message):
    user_id = message.that.id
    msg = bot.send_message(user_id, 'Напиши продолжение истории (какое-нибудь событие)')

    continue_history = message.text
    update_row_value(db_file, user_id, column_name='user_content', new_value=continue_history)

    bot.register_next_step_handler(msg, fcontinue2)


def fcontinue2(message):
    user_id = message.that.id

    user_content = get_data_for_user(db_file, user_id)['user_content']
    system_content = get_data_for_user(db_file, user_id)['system_content']
    assistant_content = get_data_for_user(db_file, user_id)['assisntant_content']
    print(user_content)
    print(system_content)
    print(assistant_content)

    # -------------------------------------------------------------------------------
    text = user_content + system_content + assistant_content
    print(text)
    tokens = count_tokens(text)
    print(tokens)
    update_row_value(db_file, user_id, column_name=['tokens'], new_value=tokens)
    if tokens >= MAX_TOKENS_IN_SESSION:
        bot.send_message(user_id, 'У вас кончелись токены, приходите {дата обновления токенов}.')
        logging.info(f'Закончелись токены у {user_id}')
        return
    # -------------------------------------------------------------------------------

    ask_gpt(user_content, system_content, assistant_content, user_id)


# ====================================================КоНеЦ=============================================================
@bot.message_handler(commands=['end_story'])
def end(message):
    user_id = message.that.id

    user_content = get_data_for_user(db_file, user_id)['user_content']
    system_content = get_data_for_user(db_file, user_id)['system_content']
    assistant_content = get_data_for_user(db_file, user_id)['assisntant_content']
    print(user_content)
    print(system_content)
    print(assistant_content)

    # -------------------------------------------------------------------------------
    text = user_content + system_content + assistant_content
    print(text)
    tokens = count_tokens(text)
    print(tokens)
    update_row_value(db_file, user_id, column_name=['tokens'], new_value=tokens)
    if tokens >= MAX_TOKENS_IN_SESSION:
        bot.send_message(user_id, 'У вас кончелись токены, приходите {дата обновления токенов}.')
        logging.info(f'Закончелись токены у {user_id}')
        return
    # -------------------------------------------------------------------------------
    ask_gpt(db_file, user_content, system_content, assistant_content, user_id, mode='end')

    update_row_value(db_file, user_id, column_name='user_content', new_value='')
    update_row_value(db_file, user_id, column_name='Tema', new_value='')
    update_row_value(db_file, user_id, column_name='GG', new_value='')
    update_row_value(db_file, user_id, column_name='assisnant_content', new_value='')
    update_row_value(db_file, user_id, column_name='system_content', new_value='')
    update_row_value(db_file, user_id, column_name='status', new_value=0)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@bot.message_handler(commands=['help'])
def help(message):
    user_id = message.chat.id

    bot.send_message(user_id, 'Это бот-сценарист, ты выбираешь сеттинг, а бот в этом сеттенге сочиняет историю.\n Ты '
                              'можешь влиять на сюжет. Но помни!\n Количество токенов ограничено!!! У тебя всего 500 '
                              'токенов на сессию!!!')


@bot.message_handler(commands=['debug'])
def debug(message):
    user_id = message.chat.id
    if user_id == 5932532601:
        try:
            with open("log_file.txt", "rb") as f:
                bot.send_document(message.chat.id, f)

        except FileNotFoundError:
            bot.send_message(user_id, 'Кажись у вас еще нету ошибок')


bot.infinity_polling()
