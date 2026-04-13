// api/transcribe.js — Node.js serverless (matches vercel.json runtime: nodejs20.x)
// Returns Deepgram key to frontend for live STT WebSocket auth.
// Security: server env key is preferred; client-supplied key accepted as fallback.

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-deepgram-key');

  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  // Client-supplied key takes priority (user pasted it in Settings)
  const clientKey = (req.headers['x-deepgram-key'] || '').trim();
  if (clientKey) {
    res.status(200).json({ available: true, key: clientKey, source: 'client' });
    return;
  }

  // Server env var
  const serverKey = (process.env.DEEPGRAM_API_KEY || '').trim();
  if (serverKey) {
    res.status(200).json({ available: true, key: serverKey, source: 'server' });
    return;
  }

  res.status(200).json({ available: false, key: null, source: 'none' });
};
