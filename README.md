# 🎙️ AI Interview Copilot

Real-time AI answer scripts for Supply Chain & Data Analytics interviews.

## How it works

- **Frontend**: Static HTML (`public/index.html`) — paste CV, set job role, click Start
- **Backend**: Vercel Edge Functions (`api/chat.js`) — tries Groq → Gemini → OpenRouter in order
- **Offline mode**: If no API key / no internet, shows smart CV-based bullet hints

## Quick start (local)

```bash
npm i -g vercel
vercel dev
```

Open `http://localhost:3000`

## Deployment (Vercel)

1. Push to GitHub
2. Import repo in [vercel.com/new](https://vercel.com/new)
3. Add environment variables (at least one):
   - `GROQ_API_KEY` — get free at [console.groq.com](https://console.groq.com)
   - `GEMINI_API_KEY` — get free at [aistudio.google.com](https://aistudio.google.com)
   - `OPENROUTER_API_KEY` — get free at [openrouter.ai](https://openrouter.ai)
4. Deploy ✅

> Users can also paste their own API keys directly in the UI (no env var needed).

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/chat` | POST | AI answer generation (streams SSE) |
| `/api/health` | GET | Health check |

## Stack

- Vercel Edge Runtime (Node.js serverless)
- Groq `llama-3.3-70b-versatile` (primary)
- Gemini `gemini-1.5-flash` (fallback)
- OpenRouter `meta-llama/llama-3.3-70b-instruct:free` (fallback)
- Web Speech API (browser-native STT)
