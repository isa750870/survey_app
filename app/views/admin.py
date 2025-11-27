from flask import (
    Blueprint, render_template, request,
    redirect, url_for, abort, session
)
from sqlalchemy import func
from functools import wraps

from extensions import db
from models import Survey, Question, Option, Answer, Response, Admin

admin_bp = Blueprint("admin", __name__)


# ---------- ДЕКОРАТОР ДЛЯ ЗАЩИТЫ АДМИН-МАРШРУТОВ ----------

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


# ---------- ЛОГИН / ЛОГАУТ ----------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session["admin_logged_in"] = True
            session["admin_username"] = admin.username
            next_url = request.args.get("next") or url_for("admin.surveys_list")
            return redirect(next_url)
        else:
            error = "Неверный логин или пароль"

    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


# ---------- ОПРОСЫ ----------

@admin_bp.route("/surveys")
@admin_required
def surveys_list():
    surveys = Survey.query.all()
    return render_template("admin/surveys_list.html", surveys=surveys)


@admin_bp.route("/surveys/new", methods=["GET", "POST"])
@admin_required
def survey_create():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        is_active = bool(request.form.get("is_active"))

        if not title:
            return render_template(
                "admin/survey_form.html",
                error="Название обязательно",
                survey=None,
            )

        survey = Survey(title=title, description=description, is_active=is_active)
        db.session.add(survey)
        db.session.commit()
        return redirect(url_for("admin.surveys_list"))

    return render_template("admin/survey_form.html", survey=None)


@admin_bp.route("/surveys/<int:survey_id>/edit", methods=["GET", "POST"])
@admin_required
def survey_edit(survey_id):
    survey = Survey.query.get_or_404(survey_id)

    if request.method == "POST":
        survey.title = request.form.get("title")
        survey.description = request.form.get("description")
        survey.is_active = bool(request.form.get("is_active"))
        db.session.commit()
        return redirect(url_for("admin.surveys_list"))

    return render_template("admin/survey_form.html", survey=survey)


@admin_bp.route("/surveys/<int:survey_id>/delete", methods=["POST"])
@admin_required
def survey_delete(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    db.session.delete(survey)
    db.session.commit()
    return redirect(url_for("admin.surveys_list"))


# ---------- ВОПРОСЫ ----------

@admin_bp.route("/surveys/<int:survey_id>/questions")
@admin_required
def questions_list(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    questions = survey.questions.all()
    return render_template(
        "admin/questions_list.html",
        survey=survey,
        questions=questions
    )


@admin_bp.route("/surveys/<int:survey_id>/questions/new", methods=["GET", "POST"])
@admin_required
def question_create(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if request.method == "POST":
        text = request.form.get("text")
        q_type = request.form.get("type", "single_choice")
        if not text:
            return render_template(
                "admin/question_form.html",
                survey=survey,
                question=None,
                error="Текст вопроса обязателен",
            )
        q = Question(survey_id=survey.id, text=text, type=q_type)
        db.session.add(q)
        db.session.commit()
        return redirect(url_for("admin.questions_list", survey_id=survey.id))

    return render_template(
        "admin/question_form.html",
        survey=survey,
        question=None
    )


@admin_bp.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
@admin_required
def question_edit(question_id):
    question = Question.query.get_or_404(question_id)
    survey = question.survey

    if request.method == "POST":
        text = request.form.get("text")
        q_type = request.form.get("type", "single_choice")
        if not text:
            return render_template(
                "admin/question_form.html",
                survey=survey,
                question=question,
                error="Текст вопроса обязателен",
            )
        question.text = text
        question.type = q_type
        db.session.commit()
        return redirect(url_for("admin.questions_list", survey_id=survey.id))

    return render_template(
        "admin/question_form.html",
        survey=survey,
        question=question
    )


@admin_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@admin_required
def question_delete(question_id):
    question = Question.query.get_or_404(question_id)
    survey_id = question.survey_id
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for("admin.questions_list", survey_id=survey_id))


# ---------- ВАРИАНТЫ ОТВЕТА ----------

@admin_bp.route("/questions/<int:question_id>/options/new", methods=["GET", "POST"])
@admin_required
def option_create(question_id):
    question = Question.query.get_or_404(question_id)
    if request.method == "POST":
        text = request.form.get("text")
        if not text:
            return render_template(
                "admin/options_form.html",
                question=question,
                option=None,
                error="Текст варианта обязателен",
            )
        option = Option(question_id=question.id, text=text)
        db.session.add(option)
        db.session.commit()
        return redirect(url_for("admin.questions_list", survey_id=question.survey_id))

    return render_template("admin/options_form.html", question=question, option=None)


@admin_bp.route("/options/<int:option_id>/edit", methods=["GET", "POST"])
@admin_required
def option_edit(option_id):
    option = Option.query.get_or_404(option_id)
    question = option.question

    if request.method == "POST":
        text = request.form.get("text")
        if not text:
            return render_template(
                "admin/options_form.html",
                question=question,
                option=option,
                error="Текст варианта обязателен",
            )
        option.text = text
        db.session.commit()
        return redirect(url_for("admin.questions_list", survey_id=question.survey_id))

    return render_template("admin/options_form.html", question=question, option=option)


@admin_bp.route("/options/<int:option_id>/delete", methods=["POST"])
@admin_required
def option_delete(option_id):
    option = Option.query.get_or_404(option_id)
    survey_id = option.question.survey_id
    db.session.delete(option)
    db.session.commit()
    return redirect(url_for("admin.questions_list", survey_id=survey_id))


# ---------- СТАТИСТИКА (ПОЧИНЕННАЯ + ТЕКСТОВЫЕ ОТВЕТЫ) ----------

@admin_bp.route("/surveys/<int:survey_id>/results")
@admin_required
def survey_results(survey_id):
    from models import Question  # если выше уже импортировано, можно убрать

    survey = Survey.query.get_or_404(survey_id)

    questions_stats = []

    for question in survey.questions.order_by(Question.id).all():
        qtype = question.type

        # Вариантные вопросы: один или несколько вариантов
        if qtype in ["single_choice", "multiple_choice"]:
            stats = (
                db.session.query(
                    Option.id,
                    Option.text,
                    func.count(Answer.id).label("answers_count"),
                )
                .outerjoin(Answer, Answer.option_id == Option.id)
                .filter(Option.question_id == question.id)
                .group_by(Option.id, Option.text)
                .all()
            )

            total = sum(row.answers_count for row in stats) or 1
            options_stats = [
                {
                    "option_id": row.id,
                    "option_text": row.text,
                    "count": row.answers_count,
                    "percent": round(row.answers_count * 100.0 / total, 2),
                }
                for row in stats
            ]

            questions_stats.append({
                "question": question,
                "type": qtype,
                "options_stats": options_stats,
                "value_stats": [],
                "text_answers": [],
            })

        # Короткий текст / число / шкала / дата — группируем одинаковые ответы с процентами
        elif qtype in ["text", "number", "range", "date"]:
            rows = (
                db.session.query(
                    Answer.text_answer,
                    func.count(Answer.id).label("answers_count"),
                )
                .filter(
                    Answer.question_id == question.id,
                    Answer.text_answer.isnot(None),
                    Answer.text_answer != "",
                )
                .group_by(Answer.text_answer)
                .all()
            )

            total = sum(row.answers_count for row in rows) or 1
            value_stats = [
                {
                    "value": row.text_answer,
                    "count": row.answers_count,
                    "percent": round(row.answers_count * 100.0 / total, 2),
                }
                for row in rows
            ]

            questions_stats.append({
                "question": question,
                "type": qtype,
                "options_stats": [],
                "value_stats": value_stats,
                "text_answers": [],
            })

        # Длинный текст — показываем как список
        else:  # long_text или неизвестный
            answers = (
                Answer.query
                .filter(
                    Answer.question_id == question.id,
                    Answer.text_answer.isnot(None),
                    Answer.text_answer != "",
                )
                .all()
            )
            questions_stats.append({
                "question": question,
                "type": qtype,
                "options_stats": [],
                "value_stats": [],
                "text_answers": [a.text_answer for a in answers],
            })

    return render_template(
        "admin/results.html",
        survey=survey,
        questions_stats=questions_stats
    )


