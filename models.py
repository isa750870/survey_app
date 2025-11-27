from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class Admin(db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Survey(db.Model):
    __tablename__ = "survey"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    questions = db.relationship(
        "Question",
        backref="survey",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    responses = db.relationship(
        "Response",
        backref="survey",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class Question(db.Model):
    __tablename__ = "question"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("survey.id"), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    # допустимые типы:
    #   single_choice   – один вариант из списка
    #   multiple_choice – несколько вариантов из списка
    #   text            – короткий свободный ответ (input)
    #   text_long       – длинный ответ (textarea)
    #   rating_1_5      – рейтинг 1–5
    type = db.Column(db.String(20), nullable=False, default="single_choice")

    options = db.relationship(
        "Option",
        backref="question",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    answers = db.relationship(
        "Answer",
        backref="question",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )



class Option(db.Model):
    __tablename__ = "option"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    text = db.Column(db.String(255), nullable=False)

    answers = db.relationship(
        "Answer",
        backref="option",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class Response(db.Model):
    __tablename__ = "response"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("survey.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    client_token = db.Column(db.String(128))

    answers = db.relationship(
        "Answer",
        backref="response",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class Answer(db.Model):
    __tablename__ = "answer"

    id = db.Column(db.Integer, primary_key=True)

    response_id = db.Column(db.Integer, db.ForeignKey("response.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)

    # для вопросов с вариантами
    option_id = db.Column(db.Integer, db.ForeignKey("option.id"), nullable=True)

    # для вопросов со свободным ответом
    text_answer = db.Column(db.Text, nullable=True)
