import re

with open('templates/index.html', 'r') as f:
    content = f.read()

# Add let overlayFs = 24; globally
content = content.replace("    let overlayMode = \"none\";", "    let overlayMode = \"none\";\n    let overlayFs = 24;")

with open('templates/index.html', 'w') as f:
    f.write(content)
