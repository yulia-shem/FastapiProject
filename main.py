# Как запустить - в терминал (командную строку) fastapi dev main.py
# Логин: Yulia Shem
# Пароль: project_2025

import sqlite3
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
import os
pwd_context = CryptContext(schemes=["bcrypt"])

app = FastAPI(
    # docs_url=None,
    redoc_url=None,
    ) # отключаем путь /redoc


# подключаем папки с локальными файлами
app.mount("/static", StaticFiles(directory=f"{os.path.dirname(os.path.realpath(__file__))}/static"), name="static")
templates = Jinja2Templates(directory="templates")

# ORM - программирование базы данных не на языке базы данных
# RAW SQL
conn = sqlite3.connect(f"{os.path.dirname(os.path.realpath(__file__))}/database.db", check_same_thread=False)
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
        language TEXT NOT NULL,
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
        (login, pwd_context.hash(password), token, 0, reg_date)
    )
    conn.commit()
    return {
        "Результат": "Регистрация прошла успешно!",
        "Ваш токен (СОХРАНИТЕ ЕГО ДЛЯ СЕБЯ!)": token
    }

# Добавление слова
@app.post("/add-word")
def add_word(token: str, word: str, meaning: str, language: str):
    if not (user := get_user(token)): # берем логин пользователя и записываем в user
        # return {"message": "Некорректный токен"}
        return JSONResponse({"Ошибка": "Некорректный токен"}, 403) # если такого логина нет, то прилетает json

    added_date = datetime.now().isoformat() # дата добавления слова
    # слово, его значение, кто добавил, когда добавил
    cursor.execute("""
        INSERT INTO words (word, meaning, language, user_login, added_date)
        VALUES (?, ?, ?, ?, ?)
    """, (word.capitalize(), meaning.capitalize(), language.capitalize(), user[1], added_date))
    conn.commit()
    return {"Результат": f'Слово «{word}» успешно добавлено!'}

# Изменение слова
@app.post("/edit-word")
def edit_word(token: str, word_id: int,
            new_meaning: str | None = Query(None),
            new_language: str | None = Query(None)):

    if not (user := get_user(token)):
        return JSONResponse({"Ошибка": "Некорректный токен"}, 403)
    if not user[4]:
        return JSONResponse({"Ошибка": "Не хватает прав"}, 403)
    cursor.execute("SELECT * FROM words WHERE id = ?", (word_id,))
    word = cursor.fetchone()
    if not word:
        return JSONResponse({"Ошибка": "Неверный id слова"}, 403)

    if new_meaning and new_language == None: # изменить только значение
        cursor.execute("UPDATE words SET meaning = ? WHERE id = ?", (new_meaning.capitalize(), word_id))

    if new_language and new_meaning == None: # изменить только язык заимствования
        cursor.execute("UPDATE words SET language = ? WHERE id = ?", (new_language.capitalize(), word_id))

    if new_meaning and new_language: # изменить и значение и язык заимствования
        cursor.execute("UPDATE words SET meaning = ?, language = ? WHERE id = ?", (new_meaning.capitalize(), new_language.capitalize(), word_id))

    conn.commit()
    return {"Результат": "Слово было успешно обновлено!"}

# Удаление слова
@app.post("/delete-word")
def delete_word(token, word_id):
    if not (user := get_user(token)):
        return JSONResponse({"Ошибка": "Некорректный токен"}, 403)
    # если can_edit
    if not user[4]:
        return JSONResponse({"Ошибка": "Не хватает прав"}, 403)
    cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
    conn.commit()
    return {"Результат": f'Слово с id={word_id} успешно удалено!'}


@app.get("/see")
def see_words(letter: str | None = Query(None),
            word: str | None = Query(None)):

    if letter and word == None:
        cursor.execute("SELECT * FROM words  WHERE word LIKE ? ORDER BY word ASC", (f"{letter.upper()}%",))
        return {"Результат": cursor.fetchall()}

    if letter and word:
        return JSONResponse({"Ошибка": "Требуется либо слово, либо буква, с которой начинаются слова"}, 403)

    # /see
    if (letter, word) == (None, None):
        cursor.execute("SELECT * FROM words ORDER BY word ASC")
        return {"Результат": cursor.fetchall()}

    # /see?word=
    if word and letter == None:
        cursor.execute("SELECT * FROM words WHERE word = ?", (word.capitalize(),))
        return {"Результат": cursor.fetchall()}
    
    # # /see?count=
    # if count and (letter, word) == (None, None):
    #     cursor.execute("SELECT * FROM words ORDER BY word ASC LIMIT ?", (count,))
    #     return {"Результат": cursor.fetchall()}
    
    # count+offset
    # if count and letter and word == None:
    #     return JSONResponse({"Ошибка": "Требуется либо буква, либо количество слов"}, 403)


@app.get("/get-token")
def get_token(login: str, password: str):
    cursor.execute("SELECT token, password FROM users WHERE login = ?", (login,))
    res = cursor.fetchone()
    if not res:
        return JSONResponse({"Ошибка": "Пользователь не найден"}, 403)
    if pwd_context.verify(password, res[1]): # сравниваем пароли
        if res[0]:
            return {"Ваш токен (СОХРАНИТЕ ЕГО!)": res[0]}
    else:
        return JSONResponse({"Ошибка": "Неверный пароль"}, 403)