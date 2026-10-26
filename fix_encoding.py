import glob
import os

def fix_mojibake(text):
    try:
        # This magic line reverses the exact corruption PowerShell caused
        return text.encode('cp1252').decode('utf-8')
    except Exception:
        pass
    try:
        return text.encode('latin-1').decode('utf-8')
    except Exception:
        return text

for filepath in glob.glob('templates/care_tools/*.html'):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed = fix_mojibake(content)
        
        # Manual safety replacements just in case
        fixed = fixed.replace('à¤¦à¥‡à¤–à¤­à¤¾à¤² à¤‰à¤ªà¤•à¤°à¤£', 'देखभाल उपकरण')
        fixed = fixed.replace('à¤‰à¤ªà¤šà¤¾à¤° à¤¯à¤¾à¤¤à¥à¤°à¤¾', 'उपचार यात्रा')
        fixed = fixed.replace('à¤®à¥à¤²à¤¾à¤•à¤¾à¤¤ à¤¨à¥‹à¤Ÿà¤¬à¥à¤•', 'मुलाकात नोटबुक')
        fixed = fixed.replace('à¤¦à¥‡à¤–à¤­à¤¾à¤² à¤ªà¤¾à¤¸à¤ªà¥‹à¤°à¥à¤Ÿ', 'देखभाल पासपोर्ट')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed)
        print(f"Fixed {filepath}")