with open("llm_service.py", "r") as f:
    content = f.read()

# There is ANOTHER history_str in the mock fallback maybe?
# In llm_service.py around line 150?

with open("llm_service.py", "w") as f:
    f.write(content.replace('history_str = "Recent Conversation History:\n" + "\n".join', 'history_str = "Recent Conversation History:\\n" + "\\n".join'))
