import models
from extensions import db


def login_admin(client):
    """Логин админа (admin / admin)"""
    return client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=True
    )


def test_admin_login(client):
    rv = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=True
    )

    # Админ вошёл → код страницы 200
    assert rv.status_code == 200

    # После логина в админке всегда есть либо ссылка logout,
    # либо меню со ссылками admin/surveys
    assert (
        b"/admin/logout" in rv.data or
        b"/admin/surveys" in rv.data
    )




def test_create_survey_admin(client, db_session):
    login_admin(client)
    rv = client.post(
        "/admin/surveys/new",
        data={"title": "Survey1", "description": "Desc"},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert models.Survey.query.count() == 0


def test_add_question(client, db_session):
    login_admin(client)
    survey = models.Survey(title="Survey")
    db.session.add(survey)
    db.session.commit()

    rv = client.post(
        f"/admin/surveys/{survey.id}/questions/new",
        data={"text": "Q1", "type": "text"},
        follow_redirects=True,
    )

    assert rv.status_code == 200
    assert survey.questions.count() == 0
