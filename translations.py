"""
Translations for Treatment Companion.
"""

TRANSLATIONS = {
    "en": {
        "home": "Home", "log": "Log", "ai_log": "AI Log", "meds": "Meds",
        "trends": "Trends", "questions": "Questions", "glossary": "Glossary",
        "care_circle": "Care Circle", "emergency": "Emergency",
        "welcome": "How are you today?",
        "welcome_sub": "A calm place to track how you're feeling and prepare for your next appointment.",
        "log_symptoms": "Log today's symptoms", "print_summary": "Print summary",
        "patterns": "Patterns from the last 14 days", "recent_entries": "Recent entries",
        "no_entries": "No entries yet. Start by logging how you feel today.",
        "upcoming_questions": "Questions for your next appointment",
        "no_questions": "No pending questions.", "add_question": "Add question",
        "cancel": "Cancel", "save": "Save entry", "delete": "Delete",
        "date": "Date", "severity": "Overall severity", "symptoms": "Symptoms", "notes": "Notes",
        "severity_none": "None", "severity_mild": "Mild", "severity_moderate": "Moderate", 
        "severity_severe": "Severe", "severity_very_severe": "Very Severe",
        "lang_en": "English", "lang_hi": "हिंदी"
    },
    "hi": {
        "home": "मुख्य पृष्ठ", "log": "लॉग", "ai_log": "AI लॉग", "meds": "दवाइयाँ",
        "trends": "रुझान", "questions": "प्रश्न", "glossary": "शब्दावली",
        "care_circle": "देखभाल समूह", "emergency": "आपातकाल",
        "welcome": "आज आप कैसा महसूस कर रहे हैं?",
        "welcome_sub": "अपनी भावनाओं को ट्रैक करने और अपनी अगली नियुक्ति की तैयारी करने के लिए एक शांत जगह।",
        "log_symptoms": "आज के लक्षण दर्ज करें", "print_summary": "सारांश प्रिंट करें",
        "patterns": "पिछले 14 दिनों के पैटर्न", "recent_entries": "हाल की प्रविष्टियाँ",
        "no_entries": "अभी तक कोई प्रविष्टि नहीं है। आज अपना लॉग दर्ज करके शुरू करें।",
        "upcoming_questions": "आपकी अगली नियुक्ति के लिए प्रश्न",
        "no_questions": "कोई लंबित प्रश्न नहीं है।", "add_question": "प्रश्न जोड़ें",
        "cancel": "रद्द करें", "save": "प्रविष्टि सहेजें", "delete": "हटाएं",
        "date": "तारीख", "severity": "समग्र गंभीरता", "symptoms": "लक्षण", "notes": "टिप्पणियाँ",
        "severity_none": "कोई नहीं", "severity_mild": "हल्का", "severity_moderate": "मध्यम", 
        "severity_severe": "गंभीर", "severity_very_severe": "बहुत गंभीर",
        "lang_en": "English", "lang_hi": "हिंदी"
    }
}

def get_text(key, lang="en"):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
