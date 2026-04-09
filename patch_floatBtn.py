import re

with open('templates/index.html', 'r') as f:
    content = f.read()

# Replace floatBtn with document.getElementById('float-btn')
content = content.replace("floatBtn.addEventListener('click', openOverlay);", "document.getElementById('float-btn').addEventListener('click', openOverlay);")

with open('templates/index.html', 'w') as f:
    f.write(content)
