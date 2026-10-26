import os
import glob

def fix_mojibake(text):
    try:
        # The magic reversal trick for Windows-1252 corruption
        return text.encode('cp1252').decode('utf-8')
    except Exception:
        # Fallback if the text is only partially corrupted
        try:
            return text.encode('latin-1').decode('utf-8')
        except Exception:
            return text

# Scan all HTML files in templates and subfolders
for filepath in glob.glob('templates/**/*.html', recursive=True):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed = fix_mojibake(content)
        
        if fixed != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f"Fixed: {filepath}")
    except Exception as e:
        print(f"Skipped {filepath} due to error: {e}")