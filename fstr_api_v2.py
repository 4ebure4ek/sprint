import os
from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2 import sql

# Получаем данные для подключения к БД из переменных окружения
DB_HOST = os.getenv("FSTR_DB_HOST", "localhost")
DB_PORT = os.getenv("FSTR_DB_PORT", "5432")
DB_LOGIN = os.getenv("FSTR_DB_LOGIN", "user")
DB_PASS = os.getenv("FSTR_DB_PASS", "password")
DB_NAME = os.getenv("FSTR_DB_NAME", "fstr_db")

app = FastAPI()

class PassData(BaseModel):
    name: str
    latitude: float
    longitude: float
    height: int
    description: str

# Функция для подключения к БД
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_LOGIN,
        password=DB_PASS,
        dbname=DB_NAME
    )

@app.post("/submitData")
def submit_data(pass_data: PassData):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = sql.SQL("""
            INSERT INTO passes (name, latitude, longitude, height, description, status)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
        """)
        cursor.execute(insert_query, (
            pass_data.name,
            pass_data.latitude,
            pass_data.longitude,
            pass_data.height,
            pass_data.description,
            "new"
        ))
        pass_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Перевал успешно добавлен", "pass_id": pass_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении перевала: {str(e)}")


# Метод GET /submitData/{id} — Получение перевала по ID
@app.get("/submitData/{id}")
def get_submit_data(id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM passes WHERE id = %s;", (id,))
    pass_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if pass_data is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    return {
        "id": pass_data[0],
        "name": pass_data[1],
        "latitude": pass_data[2],
        "longitude": pass_data[3],
        "height": pass_data[4],
        "description": pass_data[5],
        "status": pass_data[6]
    }

# Метод PATCH /submitData/{id} — Редактирование перевала (только если статус new)
@app.patch("/submitData/{id}")
def update_submit_data(id: int, data: PassData):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT status FROM passes WHERE id = %s;", (id,))
    pass_status = cur.fetchone()
    
    if not pass_status:
        cur.close()
        conn.close()
        return {"state": 0, "message": "Запись не найдена"}
    
    if pass_status[0] != "new":
        cur.close()
        conn.close()
        return {"state": 0, "message": "Редактирование доступно только в статусе 'new'"}

    update_query = """
        UPDATE passes SET name=%s, latitude=%s, longitude=%s, height=%s, description=%s
        WHERE id = %s;
    """
    cur.execute(update_query, (data.name, data.latitude, data.longitude, data.height, data.description, id))

    conn.commit()
    cur.close()
    conn.close()

    return {"state": 1, "message": "Запись успешно обновлена"}

# Метод GET /submitData/?user__email=<email> — Получение всех перевалов пользователя
@app.get("/submitData/")
def get_user_submits(user__email: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM passes WHERE user_email = %s;", (user__email,))
    passes = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": p[0],
            "name": p[1],
            "latitude": p[2],
            "longitude": p[3],
            "height": p[4],
            "description": p[5],
            "status": p[6],
            "user_email": p[7]
        }
        for p in passes
    ]
