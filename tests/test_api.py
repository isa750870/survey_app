import models
from extensions import db


API_TEST_TOKEN = "test-api-token"  # тот же, что в docker-compose для сервиса tests


def test_api_get_surveys(client, db_session):
    # готовим данные
    s = models.Survey(title="API Test", is_active=True)
    db.session.add(s)
    db.session.commit()

    # запрос к API с правильным токеном
    rv = client.get(
        "/api/surveys",
        headers={"X-API-TOKEN": API_TEST_TOKEN},
    )

    # должно быть ок
    assert rv.status_code == 200

    # ответ в JSON или просто строка — так надёжнее всего:
    # проверяем, что название опроса вообще есть в ответе
    assert b"API Test" in rv.data