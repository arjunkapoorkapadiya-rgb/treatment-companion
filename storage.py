"""
Storage layer for Treatment Companion.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional

from models import SymptomEntry, QuestionEntry


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SYMPTOMS_FILE = os.path.join(DATA_DIR, "symptoms.json")
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")
GLOSSARY_FILE = os.path.join(DATA_DIR, "glossary.json")
EMERGENCY_FILE = os.path.join(DATA_DIR, "emergency.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_json(path: str) -> list:
    _ensure_data_dir()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        print(f"[storage] Failed to load {path}: {e}")
        return []


def _load_json_any(path: str):
    """Load JSON that may be a list OR dict."""
    _ensure_data_dir()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[storage] Failed to load {path}: {e}")
        return None


def _save_json(path: str, data: list) -> None:
    _ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ==== Symptom entries ====

def list_symptoms() -> list:
    raw = _load_json(SYMPTOMS_FILE)
    entries = [SymptomEntry.from_dict(d) for d in raw]
    entries.sort(key=lambda e: e.entry_date, reverse=True)
    return entries


def get_symptom(entry_id: str) -> Optional[SymptomEntry]:
    for d in _load_json(SYMPTOMS_FILE):
        if d.get("id") == entry_id:
            return SymptomEntry.from_dict(d)
    return None


def save_symptom(entry: SymptomEntry) -> SymptomEntry:
    raw = _load_json(SYMPTOMS_FILE)
    updated = False
    for i, d in enumerate(raw):
        if d.get("id") == entry.id:
            raw[i] = entry.to_dict()
            updated = True
            break
    if not updated:
        raw.append(entry.to_dict())
    _save_json(SYMPTOMS_FILE, raw)
    return entry


def delete_symptom(entry_id: str) -> bool:
    raw = _load_json(SYMPTOMS_FILE)
    new = [d for d in raw if d.get("id") != entry_id]
    if len(new) == len(raw):
        return False
    _save_json(SYMPTOMS_FILE, new)
    return True


# ==== Pattern detection ====

def recent_entries(days: int = 14) -> list:
    cutoff = (datetime.today() - timedelta(days=days - 1)).date()
    out = []
    for entry in list_symptoms():
        try:
            d = datetime.fromisoformat(entry.entry_date).date()
        except ValueError:
            continue
        if d >= cutoff:
            out.append(entry)
    out.sort(key=lambda e: e.entry_date)
    return out


def pattern_insights(days: int = 14) -> list:
    entries = recent_entries(days)
    insights = []
    if not entries:
        return ["No entries yet — start logging to see patterns."]
    symptom_values = {}
    for entry in entries:
        for name, value in (entry.symptoms or {}).items():
            symptom_values.setdefault(name, []).append(SymptomEntry.validate_severity(value))
    for name, values in symptom_values.items():
        if not values:
            continue
        avg = sum(values) / len(values)
        pretty = name.replace("_", " ").title()
        if avg >= 3.5:
            insights.append(f"{pretty} has been high (avg {avg:.1f}/5). Consider discussing with your care team.")
        elif avg >= 2.5:
            insights.append(f"{pretty} has been moderate (avg {avg:.1f}/5).")
        else:
            insights.append(f"{pretty} has been low (avg {avg:.1f}/5). Good news.")
    if len(entries) >= 3:
        severities = [SymptomEntry.validate_severity(e.severity) for e in entries]
        first_half = severities[:len(severities) // 2]
        second_half = severities[len(severities) // 2:]
        if sum(second_half) / len(second_half) > sum(first_half) / len(first_half) + 0.5:
            insights.append("Overall symptoms are trending upward. Let your care team know.")
    return insights


# ==== Trends ====

def symptom_trends(days: int = 14) -> dict:
    entries = recent_entries(days)
    grouped = {}
    for entry in entries:
        for name, value in (entry.symptoms or {}).items():
            grouped.setdefault(name, []).append(SymptomEntry.validate_severity(value))
    result = {}
    for name, values in grouped.items():
        if not values:
            continue
        avg = sum(values) / len(values)
        arrow = "→"
        if len(values) >= 3:
            first = values[: len(values) // 2]
            second = values[len(values) // 2 :]
            fa = sum(first) / len(first)
            sa = sum(second) / len(second)
            if sa > fa + 0.5:
                arrow = "↑"
            elif sa < fa - 0.5:
                arrow = "↓"
        result[name] = {"avg": round(avg, 1), "arrow": arrow, "count": len(values)}
    return result


def severity_series(days: int = 14) -> dict:
    entries = recent_entries(days)
    labels = []
    severity = []
    symptom_series = {}
    all_symptoms = set()
    for e in entries:
        for name in (e.symptoms or {}).keys():
            all_symptoms.add(name)
    for name in all_symptoms:
        symptom_series[name] = []
    for entry in entries:
        try:
            d = datetime.fromisoformat(entry.entry_date)
            labels.append(d.strftime("%b %d"))
        except ValueError:
            labels.append(entry.entry_date)
        severity.append(SymptomEntry.validate_severity(entry.severity))
        for name in all_symptoms:
            val = (entry.symptoms or {}).get(name)
            if val is None:
                symptom_series[name].append(None)
            else:
                symptom_series[name].append(SymptomEntry.validate_severity(val))
    return {"labels": labels, "severity": severity, "symptoms": symptom_series}


# ==== Questions ====

def list_questions() -> list:
    raw = _load_json(QUESTIONS_FILE)
    qs = [QuestionEntry.from_dict(d) for d in raw]
    qs.sort(key=lambda q: (q.asked, q.created_at))
    return qs


def save_question(q: QuestionEntry) -> QuestionEntry:
    raw = _load_json(QUESTIONS_FILE)
    updated = False
    for i, d in enumerate(raw):
        if d.get("id") == q.id:
            raw[i] = q.to_dict()
            updated = True
            break
    if not updated:
        raw.append(q.to_dict())
    _save_json(QUESTIONS_FILE, raw)
    return q


def delete_question(q_id: str) -> bool:
    raw = _load_json(QUESTIONS_FILE)
    new = [d for d in raw if d.get("id") != q_id]
    if len(new) == len(raw):
        return False
    _save_json(QUESTIONS_FILE, new)
    return True


# ==== Glossary ====

def list_glossary(category: Optional[str] = None, query: Optional[str] = None) -> list:
    raw = _load_json(GLOSSARY_FILE)
    terms = raw if isinstance(raw, list) else []
    if category:
        terms = [t for t in terms if t.get("category") == category]
    if query:
        q = query.lower().strip()
        terms = [
            t for t in terms
            if q in t.get("term", "").lower() or q in t.get("definition", "").lower()
        ]
    terms.sort(key=lambda t: t.get("term", "").lower())
    return terms


def glossary_categories() -> list:
    raw = _load_json(GLOSSARY_FILE)
    cats = set()
    for t in raw:
        if isinstance(t, dict) and t.get("category"):
            cats.add(t["category"])
    return sorted(cats)


# ==== Emergency signs ====

def list_emergency_groups() -> list:
    """Return all emergency symptom groups."""
    data = _load_json_any(EMERGENCY_FILE)
    if not data:
        return []
    return data.get("symptom_groups", [])


def check_emergency(selected_symptoms: list) -> dict:
    """
    Given a list of selected symptom keys, return the highest-severity match.
    Returns: {"level": "red|amber|green|none", "match": <group or None>, "all_matches": [...]}
    """
    if not selected_symptoms:
        return {"level": "none", "match": None, "all_matches": []}

    selected = set(s.lower() for s in selected_symptoms)
    groups = list_emergency_groups()

    matches = []
    for g in groups:
        g_symptoms = set(s.lower() for s in g.get("symptoms", []))
        overlap = selected & g_symptoms
        if overlap:
            matches.append((g, len(overlap)))

    if not matches:
        return {"level": "none", "match": None, "all_matches": []}

    # Sort by level (red > amber > green), then by number of matches
    level_order = {"red": 0, "amber": 1, "green": 2}
    matches.sort(key=lambda m: (level_order.get(m[0].get("level", "green"), 3), -m[1]))

    top = matches[0][0]
    return {
        "level": top.get("level", "green"),
        "match": top,
        "all_matches": [m[0] for m in matches],
    }


def all_emergency_symptom_keys() -> list:
    """Return all unique symptom keys across groups (for the picker UI)."""
    groups = list_emergency_groups()
    keys = set()
    for g in groups:
        for s in g.get("symptoms", []):
            keys.add(s)
    return sorted(keys)