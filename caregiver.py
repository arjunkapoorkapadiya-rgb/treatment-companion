"""
Care Circle — multi-user caregiver hub.

A patient creates a circle, gets a 6-char code, shares with family.
Family members join via code, see read-only status, add notes/tasks.
No passwords, no email, no SMS. Just simple codes.

Storage: data/circles.json
"""

import json
import os
import random
import string
import uuid
from datetime import datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CIRCLES_FILE = os.path.join(DATA_DIR, "circles.json")


# ============================================================
# STORAGE
# ============================================================

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_circles() -> dict:
    """Load circles from disk. Returns {circle_code: circle_dict}."""
    _ensure_data_dir()
    if not os.path.exists(CIRCLES_FILE):
        return {}
    try:
        with open(CIRCLES_FILE, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"[caregiver] Failed to load circles: {e}")
        return {}


def _save_circles(circles: dict) -> None:
    _ensure_data_dir()
    with open(CIRCLES_FILE, "w", encoding="utf-8") as f:
        json.dump(circles, f, indent=2, ensure_ascii=False)


# ============================================================
# HELPERS
# ============================================================

def _generate_code() -> str:
    """Generate a 6-character code like ABC123."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ============================================================
# CIRCLE OPERATIONS
# ============================================================

def create_circle(patient_name: str) -> dict:
    """
    Create a new care circle.
    Returns the circle dict with the generated code.
    """
    patient_name = patient_name.strip() or "Anonymous Patient"
    circles = _load_circles()

    # Ensure unique code
    code = _generate_code()
    while code in circles:
        code = _generate_code()

    circle = {
        "code": code,
        "patient_name": patient_name,
        "created_at": _now_iso(),
        "members": [],
        "notes": [],
        "tasks": [],
        "appointments": [],
    }
    circles[code] = circle
    _save_circles(circles)
    return circle


def get_circle(code: str) -> Optional[dict]:
    """Get a circle by code."""
    circles = _load_circles()
    return circles.get(code.upper())


def list_circles() -> list:
    """Return all circles as a list."""
    return list(_load_circles().values())


def delete_circle(code: str) -> bool:
    circles = _load_circles()
    if code.upper() not in circles:
        return False
    del circles[code.upper()]
    _save_circles(circles)
    return True


# ============================================================
# MEMBER OPERATIONS
# ============================================================

def add_member(code: str, member_name: str, relation: str = "") -> Optional[dict]:
    """Add a family member to a circle."""
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return None

    member = {
        "id": str(uuid.uuid4()),
        "name": member_name.strip() or "Family Member",
        "relation": relation.strip(),
        "joined_at": _now_iso(),
    }
    circles[code]["members"].append(member)
    _save_circles(circles)
    return member


def remove_member(code: str, member_id: str) -> bool:
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return False
    before = len(circles[code]["members"])
    circles[code]["members"] = [
        m for m in circles[code]["members"] if m["id"] != member_id
    ]
    if len(circles[code]["members"]) == before:
        return False
    _save_circles(circles)
    return True


# ============================================================
# NOTES (family members can leave notes for the patient)
# ============================================================

def add_note(code: str, author: str, text: str) -> Optional[dict]:
    """Add a note from a family member to the circle."""
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return None
    text = text.strip()
    if not text:
        return None

    note = {
        "id": str(uuid.uuid4()),
        "author": author.strip() or "Family",
        "text": text[:1000],
        "created_at": _now_iso(),
    }
    circles[code]["notes"].insert(0, note)  # newest first
    # Keep only the last 50 notes
    circles[code]["notes"] = circles[code]["notes"][:50]
    _save_circles(circles)
    return note


def delete_note(code: str, note_id: str) -> bool:
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return False
    before = len(circles[code]["notes"])
    circles[code]["notes"] = [
        n for n in circles[code]["notes"] if n["id"] != note_id
    ]
    if len(circles[code]["notes"]) == before:
        return False
    _save_circles(circles)
    return True


# ============================================================
# TASKS (family can sign up for care tasks)
# ============================================================

def add_task(code: str, title: str, created_by: str) -> Optional[dict]:
    """Add a task to the circle (e.g., 'Drive to chemo Tuesday')."""
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return None
    title = title.strip()
    if not title:
        return None

    task = {
        "id": str(uuid.uuid4()),
        "title": title[:200],
        "created_by": created_by.strip() or "Family",
        "assigned_to": "",
        "done": False,
        "created_at": _now_iso(),
    }
    circles[code]["tasks"].append(task)
    _save_circles(circles)
    return task


def claim_task(code: str, task_id: str, member_name: str) -> bool:
    """Assign a task to a family member."""
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return False
    for t in circles[code]["tasks"]:
        if t["id"] == task_id:
            t["assigned_to"] = member_name.strip() or "Family"
            _save_circles(circles)
            return True
    return False


def complete_task(code: str, task_id: str) -> bool:
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return False
    for t in circles[code]["tasks"]:
        if t["id"] == task_id:
            t["done"] = not t["done"]  # toggle
            _save_circles(circles)
            return True
    return False


def delete_task(code: str, task_id: str) -> bool:
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return False
    before = len(circles[code]["tasks"])
    circles[code]["tasks"] = [
        t for t in circles[code]["tasks"] if t["id"] != task_id
    ]
    if len(circles[code]["tasks"]) == before:
        return False
    _save_circles(circles)
    return True


# ============================================================
# APPOINTMENTS (shared care calendar)
# ============================================================

def add_appointment(code: str, date: str, title: str, location: str = "") -> Optional[dict]:
    """Add an upcoming appointment."""
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return None
    title = title.strip()
    date = date.strip()
    if not title or not date:
        return None

    appt = {
        "id": str(uuid.uuid4()),
        "date": date,
        "title": title[:200],
        "location": location.strip()[:200],
        "created_at": _now_iso(),
    }
    circles[code]["appointments"].append(appt)
    # Sort by date (ascending)
    circles[code]["appointments"].sort(key=lambda a: a.get("date", ""))
    _save_circles(circles)
    return appt


def delete_appointment(code: str, appt_id: str) -> bool:
    circles = _load_circles()
    code = code.upper()
    if code not in circles:
        return False
    before = len(circles[code]["appointments"])
    circles[code]["appointments"] = [
        a for a in circles[code]["appointments"] if a["id"] != appt_id
    ]
    if len(circles[code]["appointments"]) == before:
        return False
    _save_circles(circles)
    return True


# ============================================================
# STATS (for the dashboard)
# ============================================================

def circle_stats(code: str) -> dict:
    """Return quick stats about a circle."""
    circle = get_circle(code)
    if not circle:
        return {}
    return {
        "member_count": len(circle.get("members", [])),
        "note_count": len(circle.get("notes", [])),
        "pending_tasks": sum(1 for t in circle.get("tasks", []) if not t.get("done")),
        "done_tasks": sum(1 for t in circle.get("tasks", []) if t.get("done")),
        "upcoming_appointments": len(circle.get("appointments", [])),
    }


# ============================================================
# DEMO HELPER
# ============================================================

def create_demo_circle() -> dict:
    """Create a pre-populated demo circle for judges."""
    circle = create_circle("Demo Patient")
    code = circle["code"]

    add_member(code, "Sarah (daughter)", "Daughter")
    add_member(code, "Mike (son)", "Son")
    add_member(code, "Priya (sister)", "Sister")

    add_note(code, "Sarah", "Thinking of you today, Mom. Call if you need anything.")
    add_note(code, "Mike", "I picked up your prescription. It's on the kitchen counter.")
    add_note(code, "Priya", "Made extra soup — will drop it by tomorrow evening.")

    t1 = add_task(code, "Drive to chemo on Tuesday at 10am", "Sarah")
    add_task(code, "Pick up groceries Thursday", "Mike")
    t3 = add_task(code, "Call insurance about the new medication", "Priya")
    if t3:
        complete_task(code, t3["id"])
    if t1:
        claim_task(code, t1["id"], "Sarah")

    add_appointment(code, "2026-10-20", "Chemo Session #4", "City Cancer Center, 2nd floor")
    add_appointment(code, "2026-10-28", "Follow-up with Dr. Patel", "Telehealth")

    return get_circle(code)