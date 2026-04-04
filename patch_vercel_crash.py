import re

with open("llm_service.py", "r") as f:
    content = f.read()

# Fix the broken history_str string literal that I botched.
# The newline characters got evaluated instead of remaining literal.
content = content.replace('history_str = "Recent Conversation History:\n" + "\n".join([f"{c.get(\'role\', \'unknown\').capitalize()}: {c.get(\'text\', \'\')}" for c in recent_context])', 'history_str = "Recent Conversation History:\\n" + "\\n".join([f"{c.get(\'role\', \'unknown\').capitalize()}: {c.get(\'text\', \'\')}" for c in recent_context])')

with open("llm_service.py", "w") as f:
    f.write(content)
