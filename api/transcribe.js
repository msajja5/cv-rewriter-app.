// api/transcribe.js — Node.js serverless
// Returns whether Deepgram is available and exposes the server key to the frontend.
// Security: server-env key preferred; client-supplied key accepted as fallback.

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-deepgram-key');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  // Client-supplied key takes priority (user pasted it in Settings UI)
  const clientKey = (req.headers['x-deepgram-key'] || '').trim();
  if (clientKey) {
    res.status(200).json({ available: true, key: clientKey, source: 'client' });
    return;
  }

  // Server env var (set in Vercel Dashboard → Settings → Environment Variables)
  const serverKey = (process.env.DEEPGRAM_API_KEY || '').trim();
  if (serverKey) {
    res.status(200).json({ available: true, key: serverKey, source: 'server' });
    return;
  }

  res.status(200).json({
    available: false,
    key: null,
    source: 'none',
    note: 'No Deepgram key found. Browser Web Speech API will be used for STT. To enable Deepgram Nova-3, add DEEPGRAM_API_KEY to Vercel env vars.'
  });
};
