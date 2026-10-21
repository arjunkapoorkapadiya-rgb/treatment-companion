"""
Data models for Treatment Companion.

Every symptom entry is one row of the patient's daily log.
"""

from dataclasses import dataclass, asdict, field
from datetime import date, datetime
from typing import Optional
import uuid


# Common symptoms that patients track. These are the ones
# most frequently reported in oncology literature.
COMMON_SYMPTOMS = [
    "fatigue",
    "pain",
    "nausea",
    "appetite",
    "sleep",
    "mood",
    "shortness_of_breath",
    "neuropathy",
]


# Severity levels for the 1-5 scale.
SEVERITY_LABELS = {
    1: "None",
    2: "Mild",
    3: "Moderate",
    4: "Severe",
    5: "Very Severe",
}


@dataclass
class SymptomEntry:
    """
    One day's symptom log entry.

    Attributes:
        id: unique identifier
        entry_date: YYYY-MM-DD
        severity: 1-5 overall severity
        symptoms: dict of symptom_name -> severity (1-5)
        notes: free-text notes
        questions: list of questions to ask the doctor
        created_at: ISO timestamp
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entry_date: str = field(default_factory=lambda: date.today().isoformat())
    severity: int = 1
    symptoms: dict = field(default_factory=dict)
    notes: str = ""
    questions: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "SymptomEntry":
        return SymptomEntry(
            id=data.get("id", str(uuid.uuid4())),
            entry_date=data.get("entry_date", date.today().isoformat()),
            severity=int(data.get("severity", 1)),
            symptoms=data.get("symptoms", {}),
            notes=data.get("notes", ""),
            questions=data.get("questions", []),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )

    @staticmethod
    def validate_severity(value) -> int:
        """Clamp severity to 1-5 range."""
        try:
            v = int(value)
        except (TypeError, ValueError):
            return 1
        return max(1, min(5, v))


@dataclass
class QuestionEntry:
    """A question the patient wants to ask their doctor."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    asked: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "QuestionEntry":
        return QuestionEntry(
            id=data.get("id", str(uuid.uuid4())),
            text=data.get("text", ""),
            asked=bool(data.get("asked", False)),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )