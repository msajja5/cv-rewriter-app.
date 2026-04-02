import re

with open("templates/index.html", "r") as f:
    content = f.read()

# Update Spacebar toggle logic to allow scrolling if overlay is open
content = re.sub(
    r'if \(e\.code === \'Space\' && !e\.repeat\) \{\s*e\.preventDefault\(\);\s*if \(interviewSection\.style\.display === \'block\'\) \{\s*toggleSpeakerMode\(\);\s*\}\s*\}',
    r'if (e.code === \'Space\' && !e.repeat) {\n            if (interviewSection.style.display === \'block\') {\n                e.preventDefault();\n                toggleSpeakerMode();\n            }\n        }',
    content
)

# Fix double event listener spacebar if it was duplicated
content = re.sub(
    r'// Replace the spacebar event to toggle properly without preventing default if not needed\n',
    r'',
    content
)


with open("templates/index.html", "w") as f:
    f.write(content)
