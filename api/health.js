// api/health.js — Edge Runtime
export const config = { runtime: "edge" };

export default function handler(req) {
  const groq       = !!process.env.GROQ_API_KEY;
  const gemini     = !!process.env.GEMINI_API_KEY;
  const openrouter = !!process.env.OPENROUTER_API_KEY;
  const deepgram   = !!process.env.DEEPGRAM_API_KEY;

  const anyActive = groq || gemini || openrouter;

  return new Response(
    JSON.stringify({
      status: "ok",
      timestamp: new Date().toISOString(),
      providers: {
        groq:       groq       ? "configured" : "not set",
        gemini:     gemini     ? "configured" : "not set",
        openrouter: openrouter ? "configured" : "not set",
        deepgram:   deepgram   ? "configured" : "not set (Tab/System audio will use browser fallback)"
      },
      mode: anyActive ? "live" : "offline-hints",
    }),
    {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      }
    }
  );
}
