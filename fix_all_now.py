import os

def fix_mojibake(text):
    try:
        return text.encode('cp1252').decode('utf-8')
    except Exception:
        try:
            return text.encode('latin-1').decode('utf-8')
        except Exception:
            return text

# Walk through every single folder
for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                fixed_content = fix_mojibake(content)
                
                # If the text actually changed, save it!
                if fixed_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    print(f"✅ FIXED: {filepath}")
            except Exception as e:
                print(f"❌ ERROR on {filepath}: {e}")