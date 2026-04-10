// api/transcribe.js — returns Deepgram key to frontend for WebSocket auth
// Security: only exposes the key if DEEPGRAM_API_KEY is set server-side.
// The client may also pass its own key via x-deepgram-key header.
export const config = { runtime: "edge" };

export default function handler(req) {
  const CORS = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json"
  };

  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS });
  }

  // Client-supplied key takes priority (user entered it in the UI)
  const clientKey = req.headers.get("x-deepgram-key")?.trim();
  if (clientKey) {
    return new Response(
      JSON.stringify({ available: true, key: clientKey, source: "client" }),
      { status: 200, headers: CORS }
    );
  }

  // Fall back to server env var
  const serverKey = process.env.DEEPGRAM_API_KEY?.trim();
  if (serverKey) {
    return new Response(
      JSON.stringify({ available: true, key: serverKey, source: "server" }),
      { status: 200, headers: CORS }
    );
  }

  return new Response(
    JSON.stringify({ available: false, key: null, source: "none" }),
    { status: 200, headers: CORS }
  );
}
