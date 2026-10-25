from flask import render_template, request, redirect, url_for, jsonify
from care_tools import care_tools_bp
import json, os
from datetime import datetime

# --- SAFE DB ADAPTER ---
# We try to import your models. If it fails, we use mock data.
try:
    from models import Medication, Question, Appointment
    HAS_DB = True
except ImportError:
    HAS_DB = False

DATA_FILE = 'care_tools_data.json'

def get_data():
    if not os.path.exists(DATA_FILE):
        return {"journey": [], "visits": [], "passport": {"name": "", "allergies": "Not recorded", "contacts": "", "language": "English"}}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

@care_tools_bp.route('/')
def index():
    return render_template('ct_index.html')

@care_tools_bp.route('/journey', methods=['GET', 'POST'])
def journey():
    data = get_data()
    if request.method == 'POST':
        event = {
            "id": str(datetime.now().timestamp()),
            "title": request.form.get('title'),
            "type": request.form.get('type'),
            "date": request.form.get('date'),
            "location": request.form.get('location'),
            "status": request.form.get('status'),
            "notes": request.form.get('notes')
        }
        data['journey'].append(event)
        data['journey'].sort(key=lambda x: x['date'])
        save_data(data)
        return redirect(url_for('care_tools.journey'))
    
    # Linking existing Care Circle appointments safely
    linked_appointments = []
    if HAS_DB:
        try:
            # ADAPT THIS LINE to match your actual Appointment model
            linked_appointments = Appointment.query.limit(3).all() 
        except Exception:
            pass # Ignore DB errors and fallback to empty list

    today = datetime.now().strftime('%Y-%m-%d')
    upcoming = next((e for e in data['journey'] if e['date'] >= today and e['status'] == 'Planned'), None)
    
    return render_template('ct_journey.html', events=data['journey'], upcoming=upcoming, linked_appointments=linked_appointments)

@care_tools_bp.route('/journey/delete/<id>')
def delete_journey(id):
    data = get_data()
    data['journey'] = [e for e in data['journey'] if e['id'] != id]
    save_data(data)
    return redirect(url_for('care_tools.journey'))

@care_tools_bp.route('/visits', methods=['GET', 'POST'])
def visits():
    data = get_data()
    if request.method == 'POST':
        visit = {
            "id": str(datetime.now().timestamp()),
            "date": request.form.get('date'),
            "clinician": request.form.get('clinician'),
            "notes": request.form.get('notes'),
            "actions": request.form.get('actions'),
            "question_id": request.form.get('question_id'), # Link to Doctor Question
            "status": "Pending"
        }
        data['visits'].append(visit)
        save_data(data)
        return redirect(url_for('care_tools.visits'))
    
    # Safely load existing Doctor Questions
    existing_questions = []
    if HAS_DB:
        try:
            # ADAPT THIS LINE to match your actual Question model
            existing_questions = Question.query.limit(5).all()
        except Exception:
            pass

    return render_template('ct_visits.html', visits=data['visits'], questions=existing_questions)

@care_tools_bp.route('/passport', methods=['GET', 'POST'])
def passport():
    data = get_data()
    if request.method == 'POST':
        data['passport'] = {
            "name": request.form.get('name'),
            "contacts": request.form.get('contacts'),
            "allergies": request.form.get('allergies'),
            "language": request.form.get('language')
        }
        save_data(data)
        return redirect(url_for('care_tools.passport'))
    
    # Safely load existing Medications
    current_meds = []
    if HAS_DB:
        try:
            # ADAPT THIS LINE to match your actual Medication model
            current_meds = Medication.query.all()
        except Exception:
            pass
            
    # Fallback mock data if DB fails or is empty
    if not current_meds:
        current_meds = [{"name": "Demo Med A", "dose": "10mg"}, {"name": "Demo Med B", "dose": "5mg"}]
        
    return render_template('ct_passport.html', passport=data['passport'], medications=current_meds)