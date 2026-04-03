with open("templates/index.html", "r") as f:
    content = f.read()

import re

# The nested `</script>` tag inside the template literal strings (`buildPipHTML`) will close the main `<script>` tag prematurely in HTML.
# We must break it up like `"<\/script>"` or `"</scr" + "ipt>"` when writing template strings in HTML.
content = content.replace("</script>", "</scr\" + \"ipt>", 1) # Only the inner one inside `buildPipHTML`
# Let's be safer and replace it explicitly
content = content.replace("</script>\n            </body>\n            </html>\n        `;", "</scr` + `ipt>\n            </body>\n            </html>\n        `;")


with open("templates/index.html", "w") as f:
    f.write(content)
