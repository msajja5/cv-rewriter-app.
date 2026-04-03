with open("templates/index.html", "r") as f:
    content = f.read()

# Fix the escaped quotes that were accidentally added during previous patch
content = content.replace("if (e.code === \\'Space\\' && !e.repeat) {", "if (e.code === 'Space' && !e.repeat) {")
content = content.replace("if (interviewSection.style.display === \\'block\\') {", "if (interviewSection.style.display === 'block') {")

with open("templates/index.html", "w") as f:
    f.write(content)
