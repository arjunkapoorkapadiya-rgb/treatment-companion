import os

count = 0
# Walk through every single folder
for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                new_lines = []
                for line in lines:
                    # If the line has mojibake, skip it entirely
                    if 'à¤' in line or 'à¥' in line or 'ðŸ' in line or 'â€' in line:
                        continue
                    new_lines.append(line)
                
                # Only write if we actually removed something
                if len(new_lines) != len(lines):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    print(f"✅ Cleaned: {filepath}")
                    count += 1
            except Exception as e:
                pass
print(f"Total files cleaned: {count}")