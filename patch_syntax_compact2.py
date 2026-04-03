with open("templates/index.html", "r") as f:
    content = f.read()

import re

# Remove the JS variable declaration since the DOM element no longer exists
content = re.sub(
    r'const toggleCompactBtn = document\.getElementById\(\'toggle-compact-btn\'\);\n\s*const exitCompactBtn = document\.getElementById\(\'exit-compact-btn\'\);',
    r'',
    content
)

with open("templates/index.html", "w") as f:
    f.write(content)
