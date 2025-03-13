from fastapi.testclient import TestClient
from fstr_api_v2 import app

client = TestClient(app)

def test_get_submit_data():
    response = client.get("/submitData/1")
    assert response.status_code in [200, 404]  # 404 если записи нет

def test_create_submit_data():
    new_data = {
        "name": "Тестовый перевал",
        "latitude": 50.123,
        "longitude": 45.321,
        "height": 900,
        "description": "Тестовое описание"
    }
    response = client.post("/submitData", json=new_data)
    assert response.status_code == 200
    assert "pass_id" in response.json()
