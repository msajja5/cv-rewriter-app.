import re

with open('llm_service.py', 'r') as f:
    content = f.read()

# 1. Update Stable Mock Streaming (Ensure JSON payload generation)
old_mock_loop = """    words = mock_dict["script"].split(" ")
    for word in words:
        yield {
            "type": "token",
            "content": word + " ",
            "provider": "Mock (Local)",
            "intent": mock_dict["intent"],
            "role_family": resolved_role_family
        }
        await asyncio.sleep(0.02)"""

new_mock_loop = """    words = mock_dict["script"].split(" ")
    for word in words:
        yield {
            "type": "token",
            "content": word + " ",
            "provider": "Mock (Local)",
            "intent": mock_dict["intent"],
            "role_family": resolved_role_family
        }
        await asyncio.sleep(0.02)
    # Ensure terminal event if any
    yield {"type": "done"}"""

content = content.replace(old_mock_loop, new_mock_loop)

# 2. Correct Key Resolution prioritizing BUILTIN_GEMINI_KEY/GEMINI_API_KEY appropriately without empty lists issues.
old_get_keys = """def get_keys(custom_keys: dict = None) -> list:
    keys = []
    # If custom keys are provided via the frontend, prioritize those
    if custom_keys:
        if custom_keys.get("X-Gemini-Key"):
            keys.append(("gemini", custom_keys.get("X-Gemini-Key")))
        if custom_keys.get("X-Groq-Key"):
            keys.append(("groq", custom_keys.get("X-Groq-Key")))
        if custom_keys.get("X-Or-Key"):
            keys.append(("openrouter", custom_keys.get("X-Or-Key")))

    # Then append environment variables
    if os.getenv("GEMINI_API_KEY"):
        keys.append(("gemini", os.getenv("GEMINI_API_KEY")))
    if os.getenv("GROQ_API_KEY"):
        keys.append(("groq", os.getenv("GROQ_API_KEY")))
    if os.getenv("OR_API_KEY"):
        keys.append(("openrouter", os.getenv("OR_API_KEY")))

    return keys"""

new_get_keys = """def get_keys(custom_keys: dict = None) -> list:
    keys = []

    # Check custom keys first
    if custom_keys:
        if custom_keys.get("X-Gemini-Key"):
            keys.append(("gemini", custom_keys.get("X-Gemini-Key")))
        if custom_keys.get("X-Groq-Key"):
            keys.append(("groq", custom_keys.get("X-Groq-Key")))
        if custom_keys.get("X-Or-Key"):
            keys.append(("openrouter", custom_keys.get("X-Or-Key")))

    # Append built-in env var keys (Vercel)
    builtin_gemini = os.getenv("BUILTIN_GEMINI_KEY") or os.getenv("GEMINI_API_KEY")
    if builtin_gemini and not any(k[0] == "gemini" for k in keys):
        keys.append(("gemini", builtin_gemini))

    builtin_groq = os.getenv("GROQ_API_KEY")
    if builtin_groq and not any(k[0] == "groq" for k in keys):
        keys.append(("groq", builtin_groq))

    builtin_or = os.getenv("OR_API_KEY")
    if builtin_or and not any(k[0] == "openrouter" for k in keys):
        keys.append(("openrouter", builtin_or))

    # Always append mock as the last fallback if no valid keys exist to ensure loop completes safely
    if not keys:
        logger.warning("No API keys found in custom or environment variables.")

    return keys"""

content = content.replace(old_get_keys, new_get_keys)

with open('llm_service.py', 'w') as f:
    f.write(content)
