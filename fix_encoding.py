import glob

# Using Unicode escapes so PowerShell can't break the characters
replacements = {
    '\u00e2\u20ac\u201d': '\u2014', # â€” -> —
    '\u00e2\u20ac\u201c': '\u2013', # â€“ -> –
    '\u00e2\u20ac\u2122': '\u2019', # â€™ -> ’
    '\u00e2\u20ac\u0153': '\u201c', # â€œ -> “
    '\u00e2\u20ac\u009d': '\u201d', # â€ -> ”
    '\u00c3\u00a9': '\u00e9',       # Ã© -> é
}

for filepath in glob.glob('templates/*.html'):
    try:
        # Read stripping any BOM
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        original_content = content
        for bad, good in replacements.items():
            content = content.replace(bad, good)

        # Write back as standard UTF-8 WITHOUT BOM
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        if content != original_content:
            print(f"Fixed encoding in {filepath}")
        else:
            print(f"Clean: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
