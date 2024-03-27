import requests
from main import *
from sql import *

MAX_PROJECT_TOKENS = 8000  # макс. количество токенов на весь проект
MAX_USERS = 2  # макс. количество пользователей на весь проект
MAX_SESSIONS = 3  # макс. количество сессий у пользователя
MAX_TOKENS_IN_SESSION = 200  # макс. количество токенов за сессию пользователя


# Выполняем запрос к YandexGPT
def ask_gpt(user_content, system_content, assistant_content, user_id, mode='continue'):
    iam_token = AIM_token  # Токен для доступа к YandexGPT

    if mode == 'continue':
        assistant_content += '\n' + CONTINUE_STORY
        update_row_value(db_file, user_id, column_name='assistant_content', new_value=assistant_content)
    elif mode == 'end':
        assistant_content += '\n' + END_STORY
        update_row_value(db_file, user_id, column_name='assistant_content', new_value=assistant_content)

    headers = {
        'Authorization': f'Bearer {iam_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",  # модель для генерации текста
        "completionOptions": {
            "stream": False,  # потоковая передача частично сгенерированного текста выключена
            "temperature": 0.6,  # чем выше значение этого параметра, тем более креативными будут ответы модели (0-1)
            "maxTokens": MAX_TOKENS_IN_SESSION
        },
        "messages": [
            {
                "role": "user",  # пользователь спрашивает у модели
                "text": user_content  # передаём текст, на который модель будет отвечать
            },
            {
                "role": "assistant",
                "text": assistant_content
            },
            {
                "role": "system",
                "text": system_content
            }
        ]
    }

    # Выполняем запрос к YandexGPT
    response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                             headers=headers,
                             json=data)


    # Проверяем, не произошла ли ошибка при запросе
    if response.status_code == 200:
        # достаём ответ YandexGPT
        answer = response.json()["result"]["alternatives"][0]["message"]["text"]
        x = get_data_for_user(db_file, user_id)['assistant_content']  # x - это предыдущие ответы
        answer += x
        update_row_value(db_file, user_id, column_name='assistant_content', new_value=answer)
        return answer
    else:
        logging.error(f'Не удалось получить ответ от нейросети.\nЗапрос:\n{user_content, assistant_content, system_content}')
        raise RuntimeError(
            'Invalid response received: code: {}, message: {}'.format(
                {response.status_code}, {response.text}
            )
        )

