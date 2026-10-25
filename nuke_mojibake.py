import os
import glob

# We are using HTML entities (&mdash;) so encoding CANNOT break them
replacements = {
    '&mdash;': '&mdash;',
    '&ndash;': '&ndash;',
    '&rsquo;': '&rsquo;',
    '&ldquo;': '&ldquo;',
    '&rdquo;': '&rdquo;',
    '&eacute;': '&eacute;',
    '&rdquo;¢': '&bull;'
}

# Look in templates, static, and python files
folders = ['templates', 'static', '.']
extensions = ['*.html', '*.py', '*.js', '*.css']

for folder in folders:
    for ext in extensions:
        search_path = os.path.join(folder, ext)
        for filepath in glob.glob(search_path):
            if 'venv' in filepath or '__pycache__' in filepath:
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original = content
                for bad, good in replacements.items():
                    content = content.replace(bad, good)
                
                # Also fix the exact strings seen in the screenshot
                content = content.replace('Not in the mood for a form?', 'Not in the mood for a form?')
                content = content.replace('Just describe how you feel &mdash;', 'Just describe how you feel &mdash;')
                
                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f'Nuked: {filepath}')
            except Exception as e:
                pass