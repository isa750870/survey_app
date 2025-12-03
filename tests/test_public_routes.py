import models
from extensions import db


def setup_basic_survey():
    survey = models.Survey(title="Public Test", is_active=True)
    q1 = models.Question(text="Your age?", type="number", survey=survey)
    db.session.add(survey)
    db.session.commit()
    return survey


def test_index_page(client):
    rv = client.get("/")
    assert rv.status_code == 200


def test_survey_display(client, db_session):
    survey = setup_basic_survey()

    rv = client.get(f"/survey/{survey.id}")

    # должна открыться страница
    assert rv.status_code == 200

    # на странице должен быть HTML <form>
    assert b"<form" in rv.data



def test_survey_submit(client, db_session):
    survey = setup_basic_survey()

    rv = client.post(f"/survey/{survey.id}", data={
        f"question_{survey.questions.first().id}": "10"
    })

    # после отправки редирект на страницу "спасибо"
    assert rv.status_code == 302

    # ответ реально записан?
    resp = models.Response.query.first()
    assert resp is not None
    assert resp.answers.first().text_answer == "10"
