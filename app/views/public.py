from flask import Blueprint, render_template, request, redirect, url_for, abort
from extensions import db, limiter
from models import Survey, Response, Answer, Option, Question

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    ip = request.remote_addr

    # все активные опросы
    active_surveys = Survey.query.filter_by(is_active=True).all()

    # все ответы этого IP
    responses = Response.query.filter_by(ip_address=ip).all()
    completed_ids = {r.survey_id for r in responses}

    available_surveys = [s for s in active_surveys if s.id not in completed_ids]
    completed_surveys = [s for s in active_surveys if s.id in completed_ids]

    return render_template(
        "public/index.html",
        available_surveys=available_surveys,
        completed_surveys=completed_surveys,
    )



@public_bp.route("/survey/<int:survey_id>", methods=["GET"])
def show_survey(survey_id):
    survey = Survey.query.filter_by(id=survey_id, is_active=True).first()
    if not survey:
        abort(404)

    ip = request.remote_addr

    # уже отвечал на этот опрос с этого IP? -> сразу на страницу "спасибо"
    existing = Response.query.filter_by(survey_id=survey_id, ip_address=ip).first()
    if existing:
        return redirect(url_for("public.thank_you", survey_id=survey_id))

    return render_template("public/survey_fill.html", survey=survey)


@limiter.limit("5/minute")
@public_bp.route("/survey/<int:survey_id>", methods=["POST"])
def submit_survey(survey_id):
    survey = Survey.query.filter_by(id=survey_id, is_active=True).first()
    if not survey:
        abort(404)

    ip = request.remote_addr

    # защита от повторного голосования по IP
    existing = Response.query.filter_by(survey_id=survey_id, ip_address=ip).first()
    if existing:
        return redirect(url_for("public.thank_you", survey_id=survey_id))

    response = Response(survey_id=survey_id, ip_address=ip)
    db.session.add(response)
    db.session.flush()

    for question in survey.questions.order_by(Question.id).all():
        if question.type == "single_choice":
            field_name = f"question_{question.id}"
            option_id = request.form.get(field_name)
            if option_id:
                try:
                    option_id_int = int(option_id)
                except ValueError:
                    continue
                option = Option.query.filter_by(
                    id=option_id_int,
                    question_id=question.id
                ).first()
                if option:
                    answer = Answer(
                        response_id=response.id,
                        question_id=question.id,
                        option_id=option.id
                    )
                    db.session.add(answer)
        elif question.type == "multiple_choice":
            field_name = f"question_{question.id}_multi"
            option_ids = request.form.getlist(field_name)
            for oid in option_ids:
                try:
                    oid_int = int(oid)
                except:
                    continue
                option = Option.query.filter_by(id=oid_int, question_id=question.id).first()
                if option:
                    db.session.add(Answer(
                        response_id=response.id,
                        question_id=question.id,
                        option_id=option.id
                    ))

        elif question.type in ["text", "long_text", "number", "range", "date"]:
            field_name = f"question_{question.id}"
            value = request.form.get(field_name, "").strip()
            if value:
                db.session.add(Answer(
                    response_id=response.id,
                    question_id=question.id,
                    text_answer=value
                ))
        else:
            continue


    db.session.commit()
    return redirect(url_for("public.thank_you", survey_id=survey_id))


@public_bp.route("/survey/<int:survey_id>/thanks")
def thank_you(survey_id):
    return render_template("public/thank_you.html", survey_id=survey_id)

