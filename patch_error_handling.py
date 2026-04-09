import re

with open('templates/index.html', 'r') as f:
    content = f.read()

# Enhance the error log so it dumps more info about why fetch failed
content = content.replace(
    'console.error("Failed to fetch from backend", err, err.stack);',
    'console.error("Failed to fetch from backend", err, err.stack);\n            console.log("Full error details:", JSON.stringify({message: err.message, stack: err.stack}));'
)

with open('templates/index.html', 'w') as f:
    f.write(content)
