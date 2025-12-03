import models
from extensions import db


def test_create_survey(db_session):
    survey = models.Survey(title="Test Survey", description="desc")
    db_session.add(survey)
    db_session.commit()

    assert survey.id is not None
    assert survey.title == "Test Survey"


def test_question_relationship(db_session):
    survey = models.Survey(title="Survey")
    q = models.Question(text="Q1", type="text", survey=survey)

    db_session.add(survey)
    db_session.commit()

    assert survey.questions.count() == 1
    assert survey.questions.first().text == "Q1"


def test_option_relationship(db_session):
    survey = models.Survey(title="Survey")
    q = models.Question(text="Q1", type="single_choice", survey=survey)
    opt = models.Option(text="Option 1", question=q)

    db_session.add(survey)
    db_session.commit()

    assert q.options.count() == 1
    assert q.options.first().text == "Option 1"


def test_response_and_answers(db_session):
    survey = models.Survey(title="Survey")
    q = models.Question(text="Q1", type="text", survey=survey)
    db_session.add(survey)
    db_session.commit()

    resp = models.Response(survey_id=survey.id, ip_address="127.0.0.1")
    ans = models.Answer(response=resp, question=q, text_answer="Hello")

    db_session.add(resp)
    db_session.commit()

    assert resp.id is not None
    assert resp.answers.count() == 1
    assert resp.answers.first().text_answer == "Hello"
