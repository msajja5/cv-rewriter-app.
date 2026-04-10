export default async function handler(req) {
  const groq       = !!(process.env.GROQ_API_KEY       || req.headers.get("x-groq-key"));
  const gemini     = !!(process.env.GEMINI_API_KEY     || req.headers.get("x-gemini-key"));
  const openrouter = !!(process.env.OPENROUTER_API_KEY || req.headers.get("x-openrouter-key"));
  return new Response(JSON.stringify({
    status: "ok",
    keys: { groq, gemini, openrouter },
    anyKeyConfigured: groq || gemini || openrouter
  }), {
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
  });
}
