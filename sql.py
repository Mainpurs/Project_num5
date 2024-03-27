import sqlite3
from typing import List, Any


def prepare_database():
    try:
        # Установка соединения с базой данных
        con = sqlite3.connect('sqliteData.db')
        cur = con.cursor()

        # Создание таблицы students, если она не существует
        cur.execute('''CREATE TABLE IF NOT EXISTS data (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            status INTEGER,
                            admin INTEGER,
                            user_content TEXT,
                            Tema TEXT,
                            GG TEXT,
                            assistant_content TEXT,
                            system_content TEXT,
                            tokens INTEGER
                       )''')

        # Фиксация изменений и закрытие соединения
        con.commit()
    except sqlite3.Error as e:
        print("Ошибка при работе с SQLite:", e)
    finally:
        con.close()


prepare_database()
# ======================================================================================================================


def execute_query(db_file, query, data=None):
    try:
        con = sqlite3.connect(db_file)
        cursor = con.cursor()

        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)

        con.commit()
        con.close()

        return cursor

    except sqlite3.Error as e:
        print("Ошибка при выполнении запроса:", e)


def execute_selection_query(db_path, query, data=None):
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)

        rows = cursor.fetchall()
        connection.close()
        return rows

    except sqlite3.Error as e:
        print("Ошибка при выполнении запроса:", e)


# ----------------------------------------------Add---------------------------------------------------------------------
def add_user(db_file, user_id, status, admin, user_content, Tema, GG, assisnant_content, system_content, tokens):
    if user_id == 5932532601:
        admin = 1

    query = '''INSERT INTO data (user_id INTEGER,
                            status INTEGER,
                            admin INTEGER,
                            user_content TEXT,
                            Tema TEXT,
                            GG TEXT,
                            assistant_content TEXT,
                            system_content TEXT,
                            tokens INTEGER
                            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);'''

    data = (user_id, status, admin, user_content, Tema, GG, assisnant_content, system_content, tokens)

    execute_query(db_file, query, data)


# ----------------------------------------------Answer------------------------------------------------------------------
def update_row_value(db_file, user_id, column_name, new_value):
    if user_in(db_file, 'user_id', user_id):
        query = f'UPDATE data SET {column_name} = ? WHERE user_id = {user_id}'

        data = (new_value,)

        execute_query(db_file, query, data)
    else:
        print("Такого пользователя нет :(")


# -----------------------------------------------Delete-----------------------------------------------------------------
def delete_user(db_file, user_id):

    query = 'delete from data where user_id=?;'

    data = (user_id,)

    execute_query(db_file, query, data)


# --------------------------------------Проверка_на_наличие_пользователя------------------------------------------------
def user_in(db_file, column_name, value):
    query = f'SELECT {column_name} FROM data WHERE {column_name} = ?'
    data = (value,)
    row = execute_selection_query(db_file, query, data)
    print(row)
    return row


# -------------------------------------------Инфа_по_пользователю-------------------------------------------------------
def get_data_for_user(db_file, user_id):
    if user_in(db_file, 'user_id', user_id):
        query = f'SELECT user_id, user_content, assistant_content, system_content, status, tokens, Tema, GG, id' \
                    f'FROM data where user_id = ? limit 1'

        row = execute_selection_query(db_file, query, data=[user_id])[0]
        result = {
            'user_content': row[1],
            'assistant_content': row[2],
            'system_content': row[3],
            'status': row[4],
            'tokens': row[5],
            'Tema': row[6],
            'GG': row[7],
            'id': row[8]
        }
        print(result)
        return result
    else:
        print("Такого пользователя нет :(")
        return False
