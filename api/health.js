// api/health.js — Node.js serverless
module.exports = function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
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
      groq:       groq       ? 'configured' : 'not set',
      gemini:     gemini     ? 'configured' : 'not set',
      openrouter: openrouter ? 'configured' : 'not set',
      deepgram:   deepgram   ? 'configured' : 'not set'
    },
    stt:  deepgram ? 'deepgram' : 'browser',
    mode: anyLlm   ? 'live'     : 'offline-hints'
  });
};
