// api/transcribe.js — Deepgram token endpoint (Node.js serverless)
// Returns a short-lived Deepgram API key for client-side WebSocket use
// OR acts as a WebSocket proxy for environments that need it

module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, x-deepgram-key");
  if (req.method === "OPTIONS") { res.status(200).end(); return; }

  // Allow key from env OR from client header (user-supplied key)
  const dgKey = process.env.DEEPGRAM_API_KEY || req.headers["x-deepgram-key"] || "";

  if (!dgKey) {
    return res.status(200).json({
      available: false,
      reason: "No DEEPGRAM_API_KEY configured"
    });
  }

  // Create a short-lived Deepgram API key (1-hour, single-use tag)
  // The client uses this to open a WebSocket directly to Deepgram
  try {
    const body = {
      time_to_live_in_seconds: 3600,
      comment: "cv-copilot-session",
      tags: ["interview-copilot"],
      scopes: ["usage:write"]
    };

    // We need the project ID first
    const projectsRes = await fetch("https://api.deepgram.com/v1/projects", {
      headers: { Authorization: `Token ${dgKey}` }
    });

    if (!projectsRes.ok) {
      const err = await projectsRes.text();
      // If key is valid but listing projects fails (e.g. restricted key), just return the raw key
      // The client will use it directly
      console.warn("Deepgram projects fetch failed:", err);
      return res.status(200).json({ available: true, key: dgKey, mode: "direct" });
    }

    const projects = await projectsRes.json();
    const projectId = projects?.projects?.[0]?.project_id;

    if (!projectId) {
      return res.status(200).json({ available: true, key: dgKey, mode: "direct" });
    }

    const tokenRes = await fetch(
      `https://api.deepgram.com/v1/projects/${projectId}/keys`,
      {
        method: "POST",
        headers: {
          Authorization: `Token ${dgKey}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
      }
    );

    if (!tokenRes.ok) {
      console.warn("Deepgram key creation failed, using raw key");
      return res.status(200).json({ available: true, key: dgKey, mode: "direct" });
    }

    const tokenData = await tokenRes.json();
    return res.status(200).json({
      available: true,
      key: tokenData.key || dgKey,
      mode: "ephemeral"
    });
  } catch (e) {
    console.error("transcribe.js error:", e.message);
    // Fallback: return raw key if fetch fails
    return res.status(200).json({ available: true, key: dgKey, mode: "fallback" });
  }
};
