// api/health.js — Edge Runtime
export const config = { runtime: "edge" };

export default function handler(req) {
  const groq       = !!process.env.GROQ_API_KEY;
  const gemini     = !!process.env.GEMINI_API_KEY;
  const openrouter = !!process.env.OPENROUTER_API_KEY;
  const deepgram   = !!process.env.DEEPGRAM_API_KEY;

  const anyLlm    = groq || gemini || openrouter;
  const anyKeyConfigured = anyLlm;

  return new Response(
    JSON.stringify({
      status: "ok",
      timestamp: new Date().toISOString(),
      keys: { groq, gemini, openrouter, deepgram },
      anyKeyConfigured,
      providers: {
        groq:       groq       ? "configured" : "not set",
        gemini:     gemini     ? "configured" : "not set",
        openrouter: openrouter ? "configured" : "not set",
        deepgram:   deepgram   ? "configured" : "ready — Deepgram Nova-3 live STT"
      },
      stt: deepgram ? "deepgram" : "browser",
      mode: anyLlm ? "live" : "offline-hints"
    }),
    {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    }
  );
}
