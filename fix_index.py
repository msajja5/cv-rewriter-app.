with open('templates/index.html', 'r') as f:
    content = f.read()

# I see what's happening.
# Let's verify if `window.sessionKeys` is undefined in some execution paths.
# If `window.sessionKeys` is undefined, `window.sessionKeys.gemini` throws a TypeError which bubbles up to the catch block!
content = content.replace(
    "'X-Gemini-Key': window.sessionKeys ? window.sessionKeys.gemini : document.getElementById('gemini-key').value,",
    "'X-Gemini-Key': window.sessionKeys ? window.sessionKeys.gemini : (document.getElementById('gemini-key') ? document.getElementById('gemini-key').value : ''),"
)

content = content.replace(
    "'X-Groq-Key': window.sessionKeys ? window.sessionKeys.groq : document.getElementById('groq-key').value,",
    "'X-Groq-Key': window.sessionKeys ? window.sessionKeys.groq : (document.getElementById('groq-key') ? document.getElementById('groq-key').value : ''),"
)

content = content.replace(
    "'X-Or-Key': window.sessionKeys ? window.sessionKeys.or : document.getElementById('or-key').value",
    "'X-Or-Key': window.sessionKeys ? window.sessionKeys.or : (document.getElementById('or-key') ? document.getElementById('or-key').value : '')"
)

with open('templates/index.html', 'w') as f:
    f.write(content)
