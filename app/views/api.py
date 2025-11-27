from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func
from extensions import db, limiter
from models import Survey, Question, Option, Response, Answer

api_bp = Blueprint("api", __name__)


# ---------- ПРОСТАЯ API-АВТОРИЗАЦИЯ ПО ТОКЕНУ ----------

def check_api_token():
    token = request.headers.get("X-API-Token") or request.args.get("api_token")
    return token and token == current_app.config.get("API_TOKEN")


def api_auth_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not check_api_token():
            return jsonify({"error": "unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper


# ---------- ВСПОМОГАТЕЛЬНЫЕ СЕРИАЛИЗАТОРЫ ----------

def survey_to_dict(survey: Survey, include_questions=False):
    data = {
        "id": survey.id,
        "title": survey.title,
        "description": survey.description,
        "is_active": survey.is_active,
    }
    if include_questions:
        questions = []
        for q in survey.questions.order_by(Question.id).all():
            q_data = {
                "id": q.id,
                "text": q.text,
                "type": q.type,  # single_choice / text
            }
            if q.type == "single_choice":
                q_data["options"] = [
                    {"id": o.id, "text": o.text}
                    for o in q.options.order_by(Option.id).all()
                ]
            else:
                q_data["options"] = []
            questions.append(q_data)
        data["questions"] = questions
    return data


# ---------- ЭНДПОИНТЫ ----------

@api_bp.route("/surveys", methods=["GET"])
@api_auth_required
def api_surveys_list():
    """Список активных опросов."""
    surveys = Survey.query.filter_by(is_active=True).all()
    return jsonify([survey_to_dict(s) for s in surveys])


@api_bp.route("/surveys/<int:survey_id>", methods=["GET"])
@api_auth_required
def api_survey_detail(survey_id):
    """Подробная информация об опросе с вопросами и вариантами."""
    survey = Survey.query.filter_by(id=survey_id, is_active=True).first()
    if not survey:
        return jsonify({"error": "not_found"}), 404

    return jsonify(survey_to_dict(survey, include_questions=True))


# ограничим частоту, чтобы не долбили POST бесконечно
@api_bp.route("/surveys/<int:survey_id>/responses", methods=["POST"])
@api_auth_required
@limiter.limit("30/hour")
def api_submit_response(survey_id):
    """
    Отправка ответов на опрос.

    Ожидаемый JSON:
    {
      "client_token": "user_or_device_id",
      "answers": [
        {"question_id": 1, "option_id": 10},
        {"question_id": 2, "text_answer": "какой-то текст"}
      ]
    }
    """
    survey = Survey.query.filter_by(id=survey_id, is_active=True).first()
    if not survey:
        return jsonify({"error": "not_found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid_json"}), 400

    client_token = data.get("client_token")
    answers_payload = data.get("answers", [])

    if not isinstance(answers_payload, list) or len(answers_payload) == 0:
        return jsonify({"error": "answers_required"}), 400

    ip = request.remote_addr

    # защита от накрутки: один ответ на опрос с одного client_token или IP
    query = Response.query.filter_by(survey_id=survey_id)
    if client_token:
        query = query.filter(
            (Response.client_token == client_token) | (Response.ip_address == ip)
        )
    else:
        query = query.filter(Response.ip_address == ip)

    existing = query.first()
    if existing:
        return jsonify({"status": "already_answered"}), 200

    response = Response(
        survey_id=survey_id,
        ip_address=ip,
        client_token=client_token,
    )
    db.session.add(response)
    db.session.flush()

    # валидируем и сохраняем ответы
    questions_by_id = {
        q.id: q for q in survey.questions.order_by(Question.id).all()
    }

    for item in answers_payload:
        try:
            q_id = int(item.get("question_id"))
        except (TypeError, ValueError):
            continue

        question = questions_by_id.get(q_id)
        if not question:
            continue

        if question.type == "single_choice":
            option_id = item.get("option_id")
            if option_id is None:
                continue
            try:
                option_id = int(option_id)
            except (TypeError, ValueError):
                continue

            option = Option.query.filter_by(
                id=option_id,
                question_id=question.id,
            ).first()
            if not option:
                continue

            answer = Answer(
                response_id=response.id,
                question_id=question.id,
                option_id=option.id,
            )
            db.session.add(answer)

        else:  # text
            text_answer = item.get("text_answer", "")
            if not text_answer or not isinstance(text_answer, str):
                continue
            text_answer = text_answer.strip()
            if not text_answer:
                continue

            answer = Answer(
                response_id=response.id,
                question_id=question.id,
                text_answer=text_answer,
            )
            db.session.add(answer)

    db.session.commit()
    return jsonify({"status": "ok"}), 201


@api_bp.route("/surveys/<int:survey_id>/results", methods=["GET"])
@api_auth_required
def api_survey_results(survey_id):
    """JSON-статистика по опросу: выборочные и текстовые ответы."""
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "not_found"}), 404

    result = {
        "survey": survey_to_dict(survey),
        "questions": [],
    }

    for question in survey.questions.order_by(Question.id).all():
        q_block = {
            "id": question.id,
            "text": question.text,
            "type": question.type,
        }
        if question.type == "single_choice":
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
            q_block["options"] = [
                {
                    "id": row.id,
                    "text": row.text,
                    "count": row.answers_count,
                    "percent": round(row.answers_count * 100.0 / total, 2),
                }
                for row in stats
            ]
            q_block["text_answers"] = []
        else:
            answers = (
                Answer.query
                .filter(
                    Answer.question_id == question.id,
                    Answer.text_answer.isnot(None),
                    Answer.text_answer != "",
                )
                .all()
            )
            q_block["options"] = []
            q_block["text_answers"] = [a.text_answer for a in answers]

        result["questions"].append(q_block)

    return jsonify(result)
