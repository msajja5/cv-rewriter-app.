with open("templates/index.html", "r") as f:
    content = f.read()

import re

# We removed toggle-compact-btn in earlier patch but didn't remove the event listeners. This is causing a JS error when float-btn was added.
content = re.sub(
    r'// Compact Mode Toggles\s*toggleCompactBtn\.addEventListener\(\'click\', \(\) => \{.*?\}\);\s*exitCompactBtn\.addEventListener\(\'click\', \(\) => \{.*?\}\);',
    r'',
    content,
    flags=re.DOTALL
)

with open("templates/index.html", "w") as f:
    f.write(content)
