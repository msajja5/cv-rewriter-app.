// api/chat.js — Node.js Serverless Function (NOT Edge)
// Groq → Gemini → OpenRouter waterfall with offline fallback

const STYLES = {
  live_script: "Write a natural teleprompter script Manjunath can read aloud during a live interview. 3-4 sentences. First-person, confident, conversational. NO bullet points. Start directly with the answer — no greetings.",
  concise: "Answer in 1-2 sentences only. Direct and punchy.",
  normal: "Answer in 3-4 clear sentences. Professional tone.",
  detailed: "Use the STAR method: Situation, Task, Action, Result. 5-6 sentences. Be specific with numbers and outcomes."
};

// ── Non-question filter (hardened v2) ─────────────────────────────────────────
const NON_QUESTION_KEYWORDS = new Set([
  "hello","hi","hey","test","testing","check","okay","ok","yes","no","yeah","nope",
  "uh","um","hmm","alright","right","good","great","sure","yep","nah","bye","thanks",
  "thank","sorry","pardon","please","wait","hold","ready","start","stop","go","next",
  "one","two","three","123","cool","nice","got","got it","noted"
]);

const NON_QUESTION_PATTERNS = [
  /\b(can you hear me|can you hear|is this on|mic check|sound check|audio check|is this working|testing testing|one two three|check check)\b/i,
  /^(hello|hi|hey|good morning|good afternoon|good evening)[.!?,\s]*$/i,
  /^(okay|ok|yes|no|yeah|nope|sure|yep|nah|alright|right|got it|i see|understood|perfect|great|good|nice|cool|noted|absolutely|of course|definitely|exactly|correct|agreed)[.!?,\s]*$/i,
  /^(uh+|um+|hmm+|er+|ah+|oh+|ehh?)[.!?,\s]*$/i,
  /^(can|could) you (hear|see|understand|read) (me|us)[.?!,\s]*$/i,
  /^(are you there|are you ready|is anyone there|is this recording|can you see me)[.?!,\s]*$/i,
  /^(one moment|just a moment|one second|hold on|bear with me|let me think|sorry about that|excuse me)[.!?,\s]*$/i,
  /^(sorry can you repeat|can you repeat that|pardon me)[.?!,\s]*$/i,
  /^[\d\s.,-]+$/,
];

function isNonQuestion(text) {
  const trimmed = (text || "").trim();
  if (!trimmed) return true;
  const words = trimmed.split(/\s+/);
  const lower = trimmed.toLowerCase().replace(/[.!?,]+$/, "").trim();
  if (words.length <= 3) {
    const allNoise = words.every(w => NON_QUESTION_KEYWORDS.has(w.toLowerCase().replace(/[^a-z]/g,"")));
    if (allNoise) return true;
    if (trimmed.length < 20 && !trimmed.includes("?")) return true;
  }
  if (NON_QUESTION_PATTERNS.some(p => p.test(lower) || p.test(trimmed))) return true;
  if (NON_QUESTION_PATTERNS.some(p => p.test(lower.replace(/\?/g,"")))) return true;
  return false;
}

function buildSystemPrompt(cv, job_role, response_style, target_role_family) {
  return `You are an expert AI Interview Copilot helping Manjunath Sajjan — a Senior Supply Chain professional — answer interview questions in real-time.

He is applying for: "${job_role || 'a supply chain / planning role'}".
Role family: ${target_role_family || 'Supply Chain'}.
Response style: ${STYLES[response_style] || STYLES.live_script}

His CV:
${cv || "(not provided)"}

RULES:
- Answer ONLY the interview question asked
- Always refer to his actual CV experience when relevant
- Be specific: mention tools (Arkieva, SAP, Kinaxis, Power BI, Tableau), metrics (+27% forecast accuracy, -20% holding costs, €2B EMEA), and companies (Ontex, Nike, Solvay, QuEST Global)
- Sound human, warm, and confident — never robotic
- Never say "As an AI" or "I cannot"
- Never repeat the question back
- If the detected speech is not a real interview question (e.g. a greeting, test phrase, filler word, or mic test), respond with exactly the word: SKIP`;
}

function buildMessages(systemPrompt, transcript, context) {
  const messages = [{ role: "system", content: systemPrompt }];
  (context || []).slice(-6).forEach(m =>
    messages.push({ role: m.role === "interviewer" ? "user" : "assistant", content: m.text })
  );
  messages.push({ role: "user", content: transcript });
  return messages;
}

async function tryGroq(messages, key) {
  const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { "Authorization": `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model: "llama-3.3-70b-versatile", messages, max_tokens: 300, temperature: 0.7, stream: false })
  });
  if (!res.ok) {
    const err = await res.text();
    if (res.status === 429 || err.includes("rate_limit") || err.includes("quota")) throw new Error("RATE_LIMIT");
    throw new Error(`Groq ${res.status}: ${err.slice(0, 200)}`);
  }
  const data = await res.json();
  return { text: data.choices[0].message.content, provider: "⚡ Groq Llama-3.3" };
}

async function tryGemini(messages, key) {
  const contents = messages.filter(m => m.role !== "system").map(m => ({
    role: m.role === "user" ? "user" : "model",
    parts: [{ text: m.content }]
  }));
  const systemInstruction = messages.find(m => m.role === "system")?.content || "";
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${key}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: systemInstruction }] },
        contents,
        generationConfig: { maxOutputTokens: 300, temperature: 0.7 }
      })
    }
  );
  if (!res.ok) {
    const err = await res.text();
    if (res.status === 429 || err.includes("quota")) throw new Error("RATE_LIMIT");
    throw new Error(`Gemini ${res.status}: ${err.slice(0, 200)}`);
  }
  const data = await res.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) throw new Error("Gemini empty response");
  return { text, provider: "✨ Gemini 1.5 Flash" };
}

async function tryOpenRouter(messages, key) {
  const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${key}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://cv-rewriter-app.vercel.app",
      "X-Title": "CV Interview Copilot"
    },
    body: JSON.stringify({ model: "meta-llama/llama-3.3-70b-instruct:free", messages, max_tokens: 300, temperature: 0.7 })
  });
  if (!res.ok) throw new Error(`OpenRouter ${res.status}`);
  const data = await res.json();
  const text = data.choices?.[0]?.message?.content;
  if (!text) throw new Error("OpenRouter empty response");
  return { text, provider: "🔀 OpenRouter Llama-3.3" };
}

function buildOfflineHint(question) {
  const q = (question || "").toLowerCase();
  const has = arr => arr.some(k => q.includes(k));
  if (has(["tell me about","introduce","background","walk me through","yourself"]))
    return "I have 7+ years in supply chain planning across Ontex, Nike, Solvay and QuEST Global — managing demand and supply planning for 12 global sites and a €2B EMEA retail portfolio. My core tools are Arkieva, SAP, Kinaxis RapidResponse, Power BI and Tableau. I hold an MSc in Supply Chain from EM Normandie. At Ontex I improved forecast accuracy by 27%, and at Nike I reduced holding costs by 20%.";
  if (has(["forecast","accuracy","demand plan"]))
    return "At Ontex I led 18-month rolling demand plans using Arkieva across 12 global sites, improving forecast accuracy by 27%. At Nike I built statistical demand models for a €2B EMEA retail portfolio. I also developed EOQ and safety stock models at QuEST Global for FMCG clients.";
  if (has(["supply chain","s&op","planning"]))
    return "I managed end-to-end supply chain planning at Ontex (12 sites, Arkieva), Nike (€2B EMEA, -20% holding costs), Solvay (€150M raw material MRP) and QuEST Global (SAP ERP implementation).";
  if (has(["sap","erp","kinaxis","arkieva","tool","software","system"]))
    return "My planning toolset: Arkieva for demand/supply planning, SAP ERP for MRP and implementation, Kinaxis RapidResponse for functional consulting, and Power BI/Tableau for KPI dashboards tracking OTIF, DIO and cost-to-serve.";
  if (has(["challenge","difficult","problem","failure","mistake"]))
    return "At Ontex during post-COVID volatility, I rebuilt the S&OP process across 12 global sites. I introduced 18-month rolling plans in Arkieva and aligned Sales, Finance and Operations on a weekly cadence — resulting in +27% forecast accuracy and improved OTIF.";
  if (has(["achiev","proud","success","impact","result","accomplishment"]))
    return "My top achievements: +27% forecast accuracy at Ontex across 12 global sites, -20% holding costs at Nike on a €2B EMEA portfolio, and automated Power BI dashboards that cut manual KPI reporting from 8 hours to 30 minutes per week.";
  if (has(["strength","good at","best at"]))
    return "My core strength is bridging data and operations — translating complex supply chain data into actionable plans that Sales, Finance and Operations all align on. I combine strong analytical skills (Power BI, Python, SQL) with cross-functional communication.";
  if (has(["weakness","improve","develop"]))
    return "I tend to go deep into data analysis before acting. I've learned to timebox my analysis phase — now I set a clear decision deadline and move to action even with imperfect data, aligning stakeholders faster.";
  if (has(["why","motivated","interest","leave","left"]))
    return "I'm passionate about supply chain because every optimisation has a direct impact on service levels, costs and people. I'm looking for a role where I can apply my planning and analytics expertise at scale across a global organisation.";
  return "Draw on your 7+ years across Ontex, Nike, Solvay and QuEST Global. Mention specific tools (Arkieva, Kinaxis, SAP, Power BI), quantified results (+27% forecast accuracy, -20% holding costs, €2B EMEA), and your cross-functional leadership in S&OP and NPI.";
}

// ── Startup ENV check ──────────────────────────────────────────────────────────
const hasGroq       = !!process.env.GROQ_API_KEY;
const hasGemini     = !!process.env.GEMINI_API_KEY;
const hasOpenRouter = !!process.env.OPENROUTER_API_KEY;
if (!hasGroq && !hasGemini && !hasOpenRouter) {
  console.warn('[chat.js] WARNING: No LLM API keys set in environment. All requests without client-supplied keys will use offline hints.');
}

// ── Main handler ───────────────────────────────────────────────────────────────
module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, x-groq-key, x-gemini-key, x-openrouter-key, x-deepgram-key");
  if (req.method === "OPTIONS") { res.status(200).end(); return; }
  if (req.method !== "POST") { res.status(405).send("Method Not Allowed"); return; }

  const groqKey       = process.env.GROQ_API_KEY       || req.headers["x-groq-key"]       || "";
  const geminiKey     = process.env.GEMINI_API_KEY     || req.headers["x-gemini-key"]     || "";
  const openrouterKey = process.env.OPENROUTER_API_KEY || req.headers["x-openrouter-key"] || "";

  const body = req.body || {};
  const { cv, job_role, transcript, context = [], response_style = "live_script", target_role_family = "Supply Chain" } = body;

  if (!transcript) { res.status(400).json({ error: "No transcript provided" }); return; }

  // ── Pre-filter: skip non-question phrases ──
  if (isNonQuestion(transcript)) {
    res.status(200).json({ answer: null, skip: true, provider: "filter" });
    return;
  }

  if (!groqKey && !geminiKey && !openrouterKey) {
    res.status(200).json({
      answer: buildOfflineHint(transcript),
      provider: "📋 Offline Hints (no API key — add keys in Settings ⚙)",
      offline: true
    });
    return;
  }

  const systemPrompt = buildSystemPrompt(cv, job_role, response_style, target_role_family);
  const messages = buildMessages(systemPrompt, transcript, context);

  let result = null;
  const errors = [];

  if (groqKey)       { try { result = await tryGroq(messages, groqKey);             } catch (e) { errors.push(`Groq: ${e.message}`);       console.error("Groq failed:",       e.message); } }
  if (!result && geminiKey)     { try { result = await tryGemini(messages, geminiKey);         } catch (e) { errors.push(`Gemini: ${e.message}`);     console.error("Gemini failed:",     e.message); } }
  if (!result && openrouterKey) { try { result = await tryOpenRouter(messages, openrouterKey); } catch (e) { errors.push(`OpenRouter: ${e.message}`); console.error("OpenRouter failed:", e.message); } }

  if (result) {
    // ── FIX: SKIP response must never enter the SSE stream ──
    if (result.text.trim().toUpperCase() === "SKIP") {
      res.status(200).json({ answer: null, skip: true, provider: result.provider });
      return;
    }

    // ── SSE streaming response ──
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("X-Accel-Buffering", "no"); // disable nginx buffering on Vercel
    res.status(200);

    const words = result.text.split(" ");
    let first = true;
    for (const word of words) {
      const payload = { type: "token", content: (first ? "" : " ") + word, provider: result.provider };
      res.write(`data: ${JSON.stringify(payload)}\n\n`);
      first = false;
    }
    res.write(`data: ${JSON.stringify({ type: "done", provider: result.provider })}\n\n`);
    res.end();
  } else {
    res.status(200).json({
      answer: buildOfflineHint(transcript),
      provider: "📋 Offline Hints (all APIs failed)",
      offline: true,
      errors
    });
  }
};
