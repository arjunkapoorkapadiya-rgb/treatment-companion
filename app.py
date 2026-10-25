import os
"""
Treatment Companion &mdash; Flask app.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session

import storage
import ai_service
import caregiver
import medications
from models import SymptomEntry, QuestionEntry, COMMON_SYMPTOMS, SEVERITY_LABELS
from translations import get_text


app = Flask(__name__)
app.secret_key = "treatment-companion-dev-key"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# Inject translation function into all templates
@app.context_processor
def inject_translations():
    lang = session.get("lang", "en")
    return dict(
        t=lambda key: get_text(key, lang),
        current_lang=lang
    )


@app.route("/set-lang/<lang>")
def set_lang(lang):
    """Toggle language and redirect back."""
    if lang in ["en", "hi"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


# ==== Pages ====

@app.route("/")
def index():
    entries = storage.recent_entries(days=14)
    insights = storage.pattern_insights(days=14)
    questions = [q for q in storage.list_questions() if not q.asked]
    meds_summary = medications.today_summary()
    return render_template(
        "index.html",
        entries=entries,
        insights=insights,
        questions=questions,
        severity_labels=SEVERITY_LABELS,
        meds_summary=meds_summary,
    )


@app.route("/log", methods=["GET", "POST"])
def log_symptom():
    if request.method == "POST":
        entry = SymptomEntry(
            entry_date=request.form.get("entry_date") or SymptomEntry().entry_date,
            severity=SymptomEntry.validate_severity(request.form.get("severity", 1)),
            symptoms={},
            notes=request.form.get("notes", "").strip(),
            temperature=request.form.get("temperature", "").strip(),
            sleep_hours=request.form.get("sleep_hours", "").strip(),
        )
        for name in COMMON_SYMPTOMS:
            val = request.form.get(f"symptom_{name}")
            if val:
                entry.symptoms[name] = SymptomEntry.validate_severity(val)
        storage.save_symptom(entry)
        flash("Entry saved. Take care of yourself today. ðŸ’š", "success")
        return redirect(request.path)
    return render_template(
        "log.html",
        common_symptoms=COMMON_SYMPTOMS,
        severity_labels=SEVERITY_LABELS,
    )


@app.route("/entry/<entry_id>/delete", methods=["POST"])
def delete_entry(entry_id):
    storage.delete_symptom(entry_id)
    flash("Entry deleted.", "info")
    return redirect(request.path)


@app.route("/analyze", methods=["GET", "POST"])
def analyze_page():
    if request.method == "POST":
        if request.form.get("confirm") == "yes":
            entry = SymptomEntry(
                entry_date=request.form.get("entry_date") or SymptomEntry().entry_date,
                severity=SymptomEntry.validate_severity(request.form.get("severity", 1)),
                symptoms={},
                notes=request.form.get("notes", "").strip(),
            temperature=request.form.get("temperature", "").strip(),
            sleep_hours=request.form.get("sleep_hours", "").strip(),
            )
            for name in COMMON_SYMPTOMS:
                val = request.form.get(f"symptom_{name}")
                if val:
                    entry.symptoms[name] = SymptomEntry.validate_severity(val)
            storage.save_symptom(entry)
            flash("Entry saved from AI analysis. ðŸ’š", "success")
            return redirect(request.path)

        raw_text = request.form.get("raw_text", "").strip()
        if not raw_text:
            flash("Please type something first.", "error")
            return redirect(url_for("analyze_page"))

        try:
            parsed = ai_service.parse_symptom_text(raw_text)
            return render_template(
                "ai_analyze.html",
                common_symptoms=COMMON_SYMPTOMS,
                severity_labels=SEVERITY_LABELS,
                raw_text=raw_text,
                parsed=parsed,
            )
        except Exception as e:
            flash(f"AI error: {e}", "error")
            return render_template(
                "ai_analyze.html",
                common_symptoms=COMMON_SYMPTOMS,
                severity_labels=SEVERITY_LABELS,
                raw_text=raw_text,
                parsed=None,
            )

    return render_template(
        "ai_analyze.html",
        common_symptoms=COMMON_SYMPTOMS,
        severity_labels=SEVERITY_LABELS,
        raw_text="",
        parsed=None,
    )


@app.route("/questions", methods=["GET", "POST"])
def questions_page():
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            storage.save_question(QuestionEntry(text=text))
            flash("Question added.", "success")
        return redirect(url_for("questions_page"))
    return render_template(
        "questions.html",
        questions=storage.list_questions(),
        suggestions=None,
        reasoning=None,
    )


@app.route("/questions/generate", methods=["POST"])
def generate_questions_route():
    try:
        entries = storage.recent_entries(days=14)
        trends = storage.symptom_trends(days=14)
        insights = storage.pattern_insights(days=14)
        result = ai_service.generate_doctor_questions(entries, trends, insights)
        return render_template(
            "questions.html",
            questions=storage.list_questions(),
            suggestions=result["questions"],
            reasoning=result.get("reasoning", ""),
        )
    except Exception as e:
        flash(f"AI error: {e}", "error")
        return redirect(url_for("questions_page"))


@app.route("/questions/<q_id>/toggle", methods=["POST"])
def toggle_question(q_id):
    for q in storage.list_questions():
        if q.id == q_id:
            q.asked = not q.asked
            storage.save_question(q)
            break
    return redirect(url_for("questions_page"))


@app.route("/questions/<q_id>/delete", methods=["POST"])
def delete_question_route(q_id):
    storage.delete_question(q_id)
    flash("Question removed.", "info")
    return redirect(url_for("questions_page"))


@app.route("/questions/add-from-suggestion", methods=["POST"])
def add_from_suggestion():
    text = request.form.get("text", "").strip()
    if text:
        storage.save_question(QuestionEntry(text=text))
        flash("Question added.", "success")
    return redirect(url_for("questions_page"))


@app.route("/print")
def print_summary():
    from datetime import date
    entries = storage.recent_entries(days=14)
    trends = storage.symptom_trends(days=14)
    questions = [q for q in storage.list_questions() if not q.asked]
    return render_template(
        "print.html",
        entries=entries,
        trends=trends,
        questions=questions,
        today=date.today().isoformat(),
        severity_labels=SEVERITY_LABELS,
    )


@app.route("/glossary")
def glossary_page():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip() or None
    terms = storage.list_glossary(category=category, query=query or None)
    categories = storage.glossary_categories()
    return render_template(
        "glossary.html",
        terms=terms,
        categories=categories,
        current_category=category or "",
        query=query,
    )


@app.route("/chart")
def chart_page():
    data = storage.severity_series(days=14)
    return render_template("chart.html", data=data)


@app.route("/emergency", methods=["GET", "POST"])
def emergency_page():
    groups = storage.list_emergency_groups()
    all_symptoms = storage.all_emergency_symptom_keys()
    result = None
    selected = []
    if request.method == "POST":
        selected = request.form.getlist("symptom")
        result = storage.check_emergency(selected)
    return render_template(
        "emergency.html",
        groups=groups,
        all_symptoms=all_symptoms,
        result=result,
        selected=selected,
    )


# ==== Medications ====

@app.route("/medications")
def medications_page():
    meds = medications.list_medications()
    summary = medications.today_summary()
    adherence = medications.adherence_last_days(days=14)
    return render_template(
        "medications.html",
        medications=meds,
        summary=summary,
        adherence=adherence,
        common_meds=medications.COMMON_MEDS,
    )


@app.route("/medications/add", methods=["POST"])
def medications_add():
    name = request.form.get("name", "").strip()
    dose = request.form.get("dose", "").strip()
    schedule = request.form.get("schedule", "").strip()
    notes = request.form.get("notes", "").strip()
    if name:
        medications.add_medication(name, dose, schedule, notes)
        flash(f"Added {name}.", "success")
    else:
        flash("Medication name is required.", "error")
    return redirect(url_for("medications_page"))


@app.route("/medications/<med_id>/toggle", methods=["POST"])
def medications_toggle(med_id):
    medications.toggle_dose_taken(med_id)
    return redirect(url_for("medications_page"))


@app.route("/medications/<med_id>/delete", methods=["POST"])
def medications_delete(med_id):
    medications.delete_medication(med_id)
    flash("Medication removed.", "info")
    return redirect(url_for("medications_page"))


@app.route("/medications/<med_id>/reactivate", methods=["POST"])
def medications_reactivate(med_id):
    medications.toggle_active(med_id)
    flash("Medication reactivated.", "success")
    return redirect(url_for("medications_page"))


# ==== Caregiver / Care Circle ====

@app.route("/caregiver")
def caregiver_dashboard():
    circles = caregiver.list_circles()
    return render_template(
        "caregiver.html",
        circles=circles,
        circle=None,
        stats={},
    )


@app.route("/caregiver/create", methods=["POST"])
def caregiver_create():
    patient_name = request.form.get("patient_name", "").strip()
    circle = caregiver.create_circle(patient_name)
    flash(f"Care Circle created! Share code: {circle['code']}", "success")
    return redirect(url_for("caregiver_circle", code=circle["code"]))


@app.route("/caregiver/<code>")
def caregiver_circle(code):
    circle = caregiver.get_circle(code)
    if not circle:
        flash("Circle not found.", "error")
        return redirect(url_for("caregiver_dashboard"))
    stats = caregiver.circle_stats(code)
    return render_template(
        "caregiver.html",
        circles=caregiver.list_circles(),
        circle=circle,
        stats=stats,
    )


@app.route("/caregiver/<code>/add-member", methods=["POST"])
def caregiver_add_member(code):
    name = request.form.get("name", "").strip()
    relation = request.form.get("relation", "").strip()
    if name:
        caregiver.add_member(code, name, relation)
        flash("Member added.", "success")
    return redirect(url_for("caregiver_circle", code=code))


@app.route("/caregiver/<code>/remove-member/<member_id>", methods=["POST"])
def caregiver_remove_member(code, member_id):
    caregiver.remove_member(code, member_id)
    flash("Member removed.", "info")
    return redirect(url_for("caregiver_circle", code=code))


@app.route("/caregiver/<code>/add-task", methods=["POST"])
def caregiver_add_task(code):
    title = request.form.get("title", "").strip()
    created_by = request.form.get("created_by", "Patient").strip()
    if title:
        caregiver.add_task(code, title, created_by)
        flash("Task added.", "success")
    return redirect(url_for("caregiver_circle", code=code))


@app.route("/caregiver/<code>/task/<task_id>/complete", methods=["POST"])
def caregiver_complete_task(code, task_id):
    caregiver.complete_task(code, task_id)
    return redirect(url_for("caregiver_circle", code=code))


@app.route("/caregiver/<code>/task/<task_id>/delete", methods=["POST"])
def caregiver_delete_task(code, task_id):
    caregiver.delete_task(code, task_id)
    flash("Task removed.", "info")
    return redirect(url_for("caregiver_circle", code=code))


@app.route("/caregiver/<code>/add-appointment", methods=["POST"])
def caregiver_add_appt(code):
    date = request.form.get("date", "").strip()
    title = request.form.get("title", "").strip()
    location = request.form.get("location", "").strip()
    if date and title:
        caregiver.add_appointment(code, date, title, location)
        flash("Appointment added.", "success")
    return redirect(url_for("caregiver_circle", code=code))


@app.route("/caregiver/<code>/appointment/<appt_id>/delete", methods=["POST"])
def caregiver_delete_appt(code, appt_id):
    caregiver.delete_appointment(code, appt_id)
    flash("Appointment removed.", "info")
    return redirect(url_for("caregiver_circle", code=code))


@app.route("/caregiver/<code>/add-note", methods=["POST"])
def caregiver_add_note(code):
    text = request.form.get("text", "").strip()
    author = request.form.get("author", "Patient").strip()
    if text:
        caregiver.add_note(code, author, text)
        flash("Note posted.", "success")
    return redirect(url_for("caregiver_circle", code=code))


@app.route("/caregiver/<code>/note/<note_id>/delete", methods=["POST"])
def caregiver_delete_note(code, note_id):
    caregiver.delete_note(code, note_id)
    flash("Note removed.", "info")
    return redirect(url_for("caregiver_circle", code=code))


@app.route("/caregiver/join", methods=["GET", "POST"])
def caregiver_join():
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip()
        relation = request.form.get("relation", "").strip()
        circle = caregiver.get_circle(code)
        if not circle:
            flash("Circle code not found. Ask the patient for the correct code.", "error")
            return redirect(url_for("caregiver_join"))
        if name:
            caregiver.add_member(code, name, relation)
        return redirect(url_for("caregiver_view", code=code))
    return render_template("caregiver_join.html")


@app.route("/caregiver/<code>/view")
def caregiver_view(code):
    circle = caregiver.get_circle(code)
    if not circle:
        flash("Circle not found.", "error")
        return redirect(url_for("caregiver_join"))
    stats = caregiver.circle_stats(code)
    return render_template(
        "caregiver_view.html",
        circle=circle,
        stats=stats,
    )


@app.route("/caregiver/<code>/leave-note", methods=["POST"])
def caregiver_leave_note(code):
    text = request.form.get("text", "").strip()
    author = request.form.get("author", "").strip()
    if text and author:
        caregiver.add_note(code, author, text)
        flash("Note sent to the circle.", "success")
    else:
        flash("Please enter your name and a message.", "error")
    return redirect(url_for("caregiver_view", code=code))


@app.route("/caregiver/<code>/claim-task/<task_id>", methods=["POST"])
def caregiver_claim_task(code, task_id):
    member_name = request.form.get("member_name", "").strip()
    if member_name:
        caregiver.claim_task(code, task_id, member_name)
        flash("Task claimed. Thank you!", "success")
    else:
        flash("Please enter your name to claim.", "error")
    return redirect(url_for("caregiver_view", code=code))


@app.route("/caregiver/demo")
def caregiver_demo():
    circle = caregiver.create_demo_circle()
    flash(f"Demo circle created! Code: {circle['code']}", "success")
    return redirect(url_for("caregiver_view", code=circle["code"]))


@app.route("/chat")
def chat_page():
    return render_template("chat.html")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    history = data.get("history", [])
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    try:
        reply = ai_service.chat_with_ai(user_message, history)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat")
def chat_page_duplicate():
    return render_template("chat.html")

@app.route("/api/chat", methods=["POST"])
def api_chat_v2():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    history = data.get("history", [])
    if not user_message: return jsonify({"error": "Empty message"}), 400
    try:
        reply = ai_service.chat_with_ai(user_message, history)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/caregiver/<code>/sync-hospital", methods=["POST"])
def caregiver_sync_hospital(code):
    circle = caregiver.get_circle(code)
    if circle:
        import json, os
        fhir_path = os.path.join(BASE_DIR, "data", "mock_fhir.json")
        try:
            with open(fhir_path, "r") as f: fhir_data = json.load(f)
            count = 0
            for entry in fhir_data.get("entry", []):
                appt = entry.get("resource", {})
                if appt.get("start") and appt.get("description"):
                    caregiver.add_appointment(code, appt["start"], appt["description"], appt.get("location", ""))
                    count += 1
            flash(f"Synced {count} appointments from Epic MyChart (FHIR Demo)!", "success")
        except Exception as e:
            flash(f"Sync failed: {str(e)}", "error")
    return redirect(request.path)

# ==== API ====

@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "no audio file provided"}), 400
    audio_file = request.files["audio"]
    audio_bytes = audio_file.read()
    if not audio_bytes:
        return jsonify({"error": "empty audio file"}), 400
    filename = audio_file.filename or "audio.webm"
    try:
        text = ai_service.transcribe_audio(audio_bytes, filename)
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/symptoms")
def api_symptoms():
    return jsonify([e.to_dict() for e in storage.list_symptoms()])


@app.route("/api/insights")
def api_insights():
    return jsonify(storage.pattern_insights(days=14))


@app.route("/api/series")
def api_series():
    return jsonify(storage.severity_series(days=14))


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "service": "treatment-companion"})


# ==== Errors ====

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ==== Run ====

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))




import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

