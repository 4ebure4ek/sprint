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
