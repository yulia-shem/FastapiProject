# Как запустить - в терминал (командную строку) fastapi dev main.py
import sqlite3
import uuid
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    # docs_url=None,
    redoc_url=None,
    ) # отключаем путь /redoc


# подключаем папки с локальными файлами
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ORM - программирование базы данных не на языке базы данных
# RAW SQL
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()
# уникальность логина
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL,
        password TEXT NOT NULL,
        token TEXT NOT NULL,
        can_edit BOOLEAN NOT NULL,
        registration_date TEXT NOT NULL
    )
""")
conn.commit()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        meaning TEXT NOT NULL,
        user_login TEXT NOT NULL,
        added_date TEXT NOT NULL
    )
""")
conn.commit()

def get_user(token:str) -> None | tuple:
    """
    token: токен пользователя.
    Функция возвращает либо None, либо (id, login, password, token, can_edit, reg_date)
    """
    # проверяем токен
    cursor.execute("SELECT * FROM users WHERE token = ?", (token,)) # "(token,)" - кортеж с одним элементом - token
    user = cursor.fetchone() # либо None, либо кортеж (пользователь с этим токеном)
    return user

# Получение токена

@app.get("/")
def main_interface(req: Request):
    return templates.TemplateResponse("index.html", {"request": req})

# Регистрация+получение токена
@app.post("/registration")
def registration(login: str, password: str):
    token = str(uuid.uuid4())
    reg_date = datetime.now().isoformat()
    cursor.execute(
        """INSERT INTO users (
            login, password, token, can_edit, registration_date
        ) VALUES (?, ?, ?, ?, ?)""",
        (login, password, token, 0, reg_date)
    )
    conn.commit()
    return {
        "Результат": "Регистрация прошла успешно!",
        "Ваш токен": token
    }

# Добавление слова
@app.post("/add-word")
def add_word(token: str, word: str, meaning: str):
    if not (user := get_user(token)): # берем логин пользователя и записываем в user
        # return {"message": "Некорректный токен"}
        return JSONResponse({"Результат": "Некорректный токен"}, 403) # если такого логина нет, то прилетает json

    added_date = datetime.now().isoformat() # дата добавления слова
    # слово, его значение, кто добавил, когда добавил
    cursor.execute("""
        INSERT INTO words (word, meaning, user_login, added_date)
        VALUES (?, ?, ?, ?)
    """, (word.capitalize(), meaning, user[1], added_date))
    conn.commit()
    return {"Результат": f'Слово «{word}» успешно добавлено!'}

# Изменение слова
@app.post("/edit-word")
def edit_word(token: str, word_id: int, new_meaning: str):
    if not (user := get_user(token)):
        return JSONResponse({"Результат": "Некорректный токен"}, 403)
    if not user[4]:
        return JSONResponse({"Результат": "Не хватает прав"}, 403)
    cursor.execute("SELECT * FROM words WHERE id = ?", (word_id,))
    word = cursor.fetchone()
    if not word:
        return JSONResponse({"Ошибка": "Неверный id слова"}, 403)

    cursor.execute("UPDATE words SET meaning = ? WHERE id = ?", (new_meaning, word_id))
    conn.commit()
    return {"Результат": "Слово было успешно обновлено!"}

# Удаление слова
@app.post("/delete-word")
def delete_word(token, word_id):
    if not (user := get_user(token)):
        return JSONResponse({"Результат": "Некорректный токен"}, 403)
    # если can_edit
    if not user[4]:
        return JSONResponse({"Результат": "Не хватает прав"}, 403)
    cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
    conn.commit()
    return {"Результат": f'Слово с id={word_id} успешно удалено!'}


@app.get("/see")
def see_words(count: int = None, offset: int = None, word: str = None):

    if offset and count == None:
        return JSONResponse({"Ошибка": "Сдвиг без указанного количества слов"}, 403)

    if count and offset and word:
        return JSONResponse({"Ошибка": "Требуется либо слово, либо кол-во с/без сдвига"}, 403)

    # /see
    if (count, offset, word) == (None, None, None):
        cursor.execute("SELECT * FROM words")
        return {"Результат": cursor.fetchall()}

    # /see?word=
    if word and (count, offset) == (None, None):
        cursor.execute("SELECT * FROM words WHERE word = ?", (word.capitalize(),))
        return {"Результат": cursor.fetchall()}
    
    # /see?count=
    if count and (offset, word) == (None, None):
        cursor.execute("SELECT * FROM words LIMIT ?", (count,))
        return {"Результат": cursor.fetchall()}
    
    # count+offset
    if count and offset and word == None:
        cursor.execute("SELECT * FROM words LIMIT ? OFFSET ?", (count, offset))
        return {"Результат": cursor.fetchall()}

