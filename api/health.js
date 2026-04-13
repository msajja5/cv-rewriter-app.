// api/health.js — Node.js serverless
module.exports = function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const groq       = !!process.env.GROQ_API_KEY;
  const gemini     = !!process.env.GEMINI_API_KEY;
  const openrouter = !!process.env.OPENROUTER_API_KEY;
  const deepgram   = !!process.env.DEEPGRAM_API_KEY;
  const anyLlm     = groq || gemini || openrouter;

  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    keys: { groq, gemini, openrouter, deepgram },
    anyKeyConfigured: anyLlm,
    providers: {
      groq:       groq       ? 'configured' : 'not set — add GROQ_API_KEY to Vercel env vars',
      gemini:     gemini     ? 'configured' : 'not set — add GEMINI_API_KEY to Vercel env vars',
      openrouter: openrouter ? 'configured' : 'not set — add OPENROUTER_API_KEY to Vercel env vars',
      deepgram:   deepgram   ? 'configured' : 'not set — add DEEPGRAM_API_KEY to Vercel env vars (optional)'
    },
    stt:  deepgram ? 'deepgram-nova3' : 'browser-webspeech',
    mode: anyLlm  ? 'live-ai'        : 'offline-hints-only',
    note: anyLlm  ? 'LLM ready' : 'No LLM keys found in env. App works in offline-hints mode. Add keys via Vercel Dashboard → Settings → Environment Variables, then redeploy.'
  });
};
