import os

# Default Production Model Configuration
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "gemini")  # Options: gemini, groq, openrouter, mock
DEFAULT_MODEL_GEMINI = os.getenv("DEFAULT_MODEL_GEMINI", "gemini-2.0-flash")
DEFAULT_MODEL_GROQ = os.getenv("DEFAULT_MODEL_GROQ", "llama-3.3-70b-versatile")

# Provider hierarchy for fallbacks if primary fails or keys are missing
FALLBACK_CHAIN = ["gemini", "groq", "openrouter", "mock"]

# Feature Flags
ENABLE_SERVER_STT = True
