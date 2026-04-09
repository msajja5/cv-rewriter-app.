import re

with open('templates/index.html', 'r') as f:
    content = f.read()

# Also updateInlineSpeakerUI is gone, but we should make sure btnInt and btnMe don't cause issues in applyToDoc
btn_logic = """            if (btnInt && btnMe) {
                btnInt.style.border = payload.speaker === "interviewer" ? "2px solid white" : "none";
                btnMe.style.border = payload.speaker === "me" ? "2px solid white" : "none";
            }"""

content = content.replace(btn_logic, "")

with open('templates/index.html', 'w') as f:
    f.write(content)
