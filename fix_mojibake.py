import glob

def fix_text(text):
    try:
        # This is the magic trick: It reverses the Windows-1252 to UTF-8 corruption
        return text.encode('cp1252').decode('utf-8')
    except Exception:
        return text

for filepath in glob.glob('templates/*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if the weird characters are present
    if 'â' in content or 'Ã' in content:
        fixed_content = fix_text(content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f'Fixed: {filepath}')
    else:
        print(f'Clean: {filepath}')