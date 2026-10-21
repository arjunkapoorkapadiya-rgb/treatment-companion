"""
Medications Tracker for Treatment Companion.
"""
import json
import os
import uuid
from datetime import date, datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MEDS_FILE = os.path.join(DATA_DIR, "medications.json")

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _load() -> list:
    _ensure_data_dir()
    if not os.path.exists(MEDS_FILE):
        return []
    try:
        with open(MEDS_FILE, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        print(f"[medications] Failed to load: {e}")
        return []

def _save(meds: list) -> None:
    _ensure_data_dir()
    with open(MEDS_FILE, "w", encoding="utf-8") as f:
        json.dump(meds, f, indent=2, ensure_ascii=False)

def _now() -> str:
    return datetime.utcnow().isoformat()

def list_medications() -> list:
    return _load()

def get_medication(med_id: str) -> Optional[dict]:
    for m in _load():
        if m["id"] == med_id:
            return m
    return None

def add_medication(name: str, dose: str, schedule: str, notes: str = "") -> dict:
    meds = _load()
    med = {
        "id": str(uuid.uuid4()),
        "name": name.strip()[:100],
        "dose": dose.strip()[:80],
        "schedule": schedule.strip()[:100],
        "notes": notes.strip()[:500],
        "created_at": _now(),
        "active": True,
        "doses": {},
    }
    meds.append(med)
    _save(meds)
    return med

def update_medication(med_id: str, **kwargs) -> Optional[dict]:
    meds = _load()
    for m in meds:
        if m["id"] == med_id:
            for k, v in kwargs.items():
                if k in ("name", "dose", "schedule", "notes", "active"):
                    m[k] = v
            _save(meds)
            return m
    return None

def delete_medication(med_id: str) -> bool:
    meds = _load()
    before = len(meds)
    meds = [m for m in meds if m["id"] != med_id]
    if len(meds) == before:
        return False
    _save(meds)
    return True

def toggle_active(med_id: str) -> bool:
    meds = _load()
    for m in meds:
        if m["id"] == med_id:
            m["active"] = not m.get("active", True)
            _save(meds)
            return True
    return False

def today_str() -> str:
    return date.today().isoformat()

def toggle_dose_taken(med_id: str, day: Optional[str] = None) -> bool:
    meds = _load()
    day = day or today_str()
    for m in meds:
        if m["id"] == med_id:
            doses = m.setdefault("doses", {})
            doses[day] = not doses.get(day, False)
            _save(meds)
            return True
    return False

def today_summary() -> dict:
    meds = _load()
    day = today_str()
    active = [m for m in meds if m.get("active", True)]
    taken = [m for m in active if m.get("doses", {}).get(day, False)]
    pending = [m for m in active if not m.get("doses", {}).get(day, False)]
    return {
        "day": day,
        "total_active": len(active),
        "taken": len(taken),
        "pending": len(pending),
        "active_meds": active,
        "taken_meds": taken,
        "pending_meds": pending,
    }

def adherence_last_days(days: int = 14) -> dict:
    from datetime import timedelta
    meds = _load()
    active = [m for m in meds if m.get("active", True)]
    if not active:
        return {"dates": [], "percentages": [], "overall_pct": 0.0}
    today = date.today()
    dates = []
    pcts = []
    total_taken = 0
    total_possible = 0
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        dstr = d.isoformat()
        taken = sum(1 for m in active if m.get("doses", {}).get(dstr, False))
        pct = (taken / len(active)) * 100 if active else 0
        dates.append(dstr[5:])
        pcts.append(round(pct, 1))
        total_taken += taken
        total_possible += len(active)
    overall = (total_taken / total_possible * 100) if total_possible else 0.0
    return {
        "dates": dates,
        "percentages": pcts,
        "overall_pct": round(overall, 1),
    }

COMMON_MEDS = [
    {"name": "Tamoxifen", "dose": "20 mg", "schedule": "Once daily"},
    {"name": "Letrozole", "dose": "2.5 mg", "schedule": "Once daily"},
    {"name": "Ondansetron", "dose": "4-8 mg", "schedule": "Every 8h as needed"},
    {"name": "Metoclopramide", "dose": "10 mg", "schedule": "Every 6h as needed"},
    {"name": "Dexamethasone", "dose": "4 mg", "schedule": "Twice daily"},
    {"name": "Loratadine", "dose": "10 mg", "schedule": "Once daily"},
    {"name": "Morphine (IR)", "dose": "5-15 mg", "schedule": "Every 4h as needed"},
    {"name": "Oxycodone", "dose": "5 mg", "schedule": "Every 6h as needed"},
    {"name": "Filgrastim", "dose": "300 mcg", "schedule": "Daily for 5-7 days"},
    {"name": "Prednisone", "dose": "20 mg", "schedule": "Once daily"},
]
