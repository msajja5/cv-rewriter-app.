with open('main.py', 'r') as f:
    content = f.read()

bad_string = 'yield f"data: {json.dumps({\'type\': \'token\', \'content\': \'\'})}\\n\\n"'
# If it was actually written over multiple lines:
bad_string_multi = 'yield f"data: {json.dumps({\'type\': \'token\', \'content\': \'\'})}\n\n"'

if bad_string_multi in content:
    content = content.replace(bad_string_multi, 'yield f"data: {json.dumps({\'type\': \'token\', \'content\': \'\'})}\\n\\n"')

with open('main.py', 'w') as f:
    f.write(content)
