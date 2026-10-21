"""
AI service for Treatment Companion.
"""

import json
import os
from dotenv import load_dotenv
import requests

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
CHAT_MODEL = "openai/gpt-oss-120b"
WHISPER_MODEL = "whisper-large-v3-turbo"


# ============================================================
# PROMPTS
# ============================================================

SYMPTOM_PARSE_PROMPT = """You are a compassionate assistant that helps cancer patients log their symptoms.

Your job: parse the patient's free-form text and return structured data.

Return ONLY valid JSON (no markdown, no code fences, no explanation) with this exact schema:

{
  "severity": <integer 1-5>,
  "symptoms": {
    "fatigue": <integer 1-5 or omit>,
    "pain": <integer 1-5 or omit>,
    "nausea": <integer 1-5 or omit>,
    "appetite": <integer 1-5 or omit>,
    "sleep": <integer 1-5 or omit>,
    "mood": <integer 1-5 or omit>,
    "shortness_of_breath": <integer 1-5 or omit>,
    "neuropathy": <integer 1-5 or omit>
  },
  "notes": "<short summary of what the patient said>"
}

Rules:
- 1 = none/mild, 5 = very severe
- If the patient doesn't mention a symptom, omit it from "symptoms"
- "severity" is an overall feeling of how they are today. If not stated, infer from symptoms.
- "notes" should be a brief summary in the patient's own words, not a diagnosis.
- NEVER add medical advice. Just structure what they said.
- If the text is not about symptoms (e.g., "hello"), return severity 1 and empty symptoms.

Examples:

Input: "Felt really tired today, mild headache, didn't sleep well"
Output: {"severity": 3, "symptoms": {"fatigue": 4, "pain": 2, "sleep": 4}, "notes": "Felt really tired, mild headache, didn't sleep well"}

Input: "Bad nausea after lunch, threw up twice, overall a 4"
Output: {"severity": 4, "symptoms": {"nausea": 5}, "notes": "Bad nausea after lunch, vomited twice"}
"""


DOCTOR_QUESTIONS_PROMPT = """You are a compassionate assistant helping a cancer patient prepare for their next doctor appointment.

You will receive a summary of their recent symptom data (last 14 days). Your job is to generate 4-6 thoughtful, specific questions they should ask their oncology care team.

Guidelines:
- Base questions on ACTUAL patterns in the data (high averages, rising trends, new symptoms, unusual combinations)
- Questions should be clear, plain-language, and medically appropriate
- NEVER diagnose or suggest treatment changes
- Frame as questions the patient can ask, not advice
- If data is sparse, generate general but useful questions
- Be warm and specific, not generic

Return ONLY valid JSON (no markdown, no code fences) with this schema:

{
  "questions": ["<q1>", "<q2>", ...],
  "reasoning": "<one sentence explaining what patterns you noticed>"
}
"""


# ============================================================
# PUBLIC API
# ============================================================

def parse_symptom_text(text: str) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set. Check your .env file.")
    parsed = _call_groq_json(SYMPTOM_PARSE_PROMPT, text.strip())
    parsed.setdefault("severity", 1)
    parsed.setdefault("symptoms", {})
    parsed.setdefault("notes", text.strip())
    try:
        s = int(parsed["severity"])
    except (TypeError, ValueError):
        s = 1
    parsed["severity"] = max(1, min(5, s))
    sanitized = {}
    for key, val in parsed.get("symptoms", {}).items():
        try:
            v = int(val)
            sanitized[key] = max(1, min(5, v))
        except (TypeError, ValueError):
            continue
    parsed["symptoms"] = sanitized
    return parsed


def generate_doctor_questions(symptom_entries: list, trends: dict, insights: list) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set. Check your .env file.")
    summary = _build_data_summary(symptom_entries, trends, insights)
    result = _call_groq_json(DOCTOR_QUESTIONS_PROMPT, summary)
    questions = result.get("questions", [])
    if not isinstance(questions, list):
        questions = []
    cleaned = [q.strip() for q in questions if isinstance(q, str) and q.strip()][:8]
    return {
        "questions": cleaned,
        "reasoning": str(result.get("reasoning", "")).strip(),
    }


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Send audio to Groq Whisper. Return transcribed text.
    Raises RuntimeError on failure.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set. Check your .env file.")

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": (filename, audio_bytes, "audio/webm"),
    }
    data = {
        "model": WHISPER_MODEL,
        "language": "en",       # Can be auto-detected; en forces English
        "response_format": "json",
    }

    response = requests.post(
        GROQ_TRANSCRIBE_URL,
        headers=headers,
        files=files,
        data=data,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Whisper API error {response.status_code}: {response.text}")

    result = response.json()
    text = result.get("text", "").strip()
    if not text:
        raise RuntimeError("Whisper returned empty transcription.")
    return text


# ============================================================
# INTERNALS
# ============================================================

def _call_groq_json(system_prompt: str, user_content: str) -> dict:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(GROQ_CHAT_URL, headers=headers, json=body, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Groq API error {response.status_code}: {response.text}")
    content = response.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model returned invalid JSON: {content[:200]}") from e


def _build_data_summary(entries: list, trends: dict, insights: list) -> str:
    lines = ["PATIENT SYMPTOM DATA (last 14 days)"]
    lines.append(f"Total entries logged: {len(entries)}")
    lines.append("")
    if trends:
        lines.append("SYMPTOM TRENDS:")
        for name, data in trends.items():
            pretty = name.replace("_", " ").title()
            lines.append(f"  - {pretty}: avg {data['avg']}/5 over {data['count']} day(s), trend {data['arrow']}")
        lines.append("")
    if insights:
        lines.append("DETECTED PATTERNS:")
        for i in insights:
            lines.append(f"  - {i}")
        lines.append("")
    if entries:
        lines.append("RECENT ENTRIES (most recent first):")
        for e in entries[-7:][::-1]:
            date = getattr(e, "entry_date", "?")
            sev = getattr(e, "severity", "?")
            syms = getattr(e, "symptoms", {}) or {}
            sym_str = ", ".join(f"{k}={v}/5" for k, v in syms.items()) or "none"
            notes = getattr(e, "notes", "") or ""
            line = f"  - {date}: severity {sev}/5; symptoms: {sym_str}"
            if notes:
                line += f"; notes: {notes}"
            lines.append(line)
    if not trends and not entries:
        lines.append("(No symptom data available yet.)")
    return "\n".join(lines)