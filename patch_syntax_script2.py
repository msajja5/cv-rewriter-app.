with open("templates/index.html", "r") as f:
    content = f.read()

import re

# Correct the nested script tags in the template literal.
# HTML parsers stop the main script block when they see `</script>`, even inside strings.
content = re.sub(
    r'<script>\s*window\.addEventListener\("message",',
    r'<scr` + `ipt>\n                    window.addEventListener("message",',
    content
)

with open("templates/index.html", "w") as f:
    f.write(content)
