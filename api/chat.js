const STYLES = {
  live_script: "Write a natural teleprompter script Manjunath can read aloud during a live interview. 3-4 sentences. First-person, confident, conversational. NO bullet points. Start directly with the answer — no greetings.",
  concise: "Answer in 1-2 sentences only. Direct and punchy.",
  normal: "Answer in 3-4 clear sentences. Professional tone.",
  detailed: "Use the STAR method: Situation, Task, Action, Result. 5-6 sentences. Be specific with numbers and outcomes."
};

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
- Never repeat the question back`;
}

function buildMessages(systemPrompt, transcript, context) {
  const messages = [{ role: "system", content: systemPrompt }];
  (context || []).slice(-6).forEach(m =>
    messages.push({ role: m.role === "interviewer" ? "user" : "assistant", content: m.text })
  );
  messages.push({ role: "user", content: transcript });
  return messages;
}

function streamText(text, provider, controller, encoder) {
  // Stream word by word for teleprompter feel
  const words = text.split(" ");
  let first = true;
  for (const word of words) {
    const p = { type: "token", content: (first ? "" : " ") + word, provider };
    controller.enqueue(encoder.encode(`data: ${JSON.stringify(p)}\n\n`));
    first = false;
  }
}

// ── Provider 1: Groq (fastest — Llama 3.3 70B) ──────────────────────────────
async function tryGroq(messages, groqKey) {
  const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { "Authorization": `Bearer ${groqKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model: "llama-3.3-70b-versatile", messages, max_tokens: 300, temperature: 0.7, stream: false })
  });
  if (!res.ok) {
    const err = await res.text();
    if (res.status === 429 || err.includes("rate_limit") || err.includes("quota")) throw new Error("RATE_LIMIT");
    throw new Error(`Groq error: ${res.status}`);
  }
  const data = await res.json();
  return { text: data.choices[0].message.content, provider: "⚡ Groq Llama-3.3" };
}

// ── Provider 2: Gemini (high quality — gemini-1.5-flash) ────────────────────
async function tryGemini(messages, geminiKey) {
  const contents = messages.filter(m => m.role !== "system").map(m => ({
    role: m.role === "user" ? "user" : "model",
    parts: [{ text: m.content }]
  }));
  const systemInstruction = messages.find(m => m.role === "system")?.content || "";
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`,
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
    throw new Error(`Gemini error: ${res.status}`);
  }
  const data = await res.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) throw new Error("Gemini empty response");
  return { text, provider: "✨ Gemini 1.5 Flash" };
}

// ── Provider 3: OpenRouter (fallback — best available free model) ────────────
async function tryOpenRouter(messages, openrouterKey) {
  const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${openrouterKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://cv-rewriter-app.vercel.app",
      "X-Title": "CV Interview Copilot"
    },
    body: JSON.stringify({
      model: "meta-llama/llama-3.3-70b-instruct:free",
      messages,
      max_tokens: 300,
      temperature: 0.7
    })
  });
  if (!res.ok) throw new Error(`OpenRouter error: ${res.status}`);
  const data = await res.json();
  const text = data.choices?.[0]?.message?.content;
  if (!text) throw new Error("OpenRouter empty response");
  return { text, provider: "🔀 OpenRouter Llama-3.3" };
}

export default async function handler(req) {
  if (req.method === "OPTIONS") {
    return new Response(null, {
      headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type, x-groq-key, x-gemini-key, x-openrouter-key" }
    });
  }
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

  const groqKey       = process.env.GROQ_API_KEY       || "";
  const geminiKey     = process.env.GEMINI_API_KEY     || "";
  const openrouterKey = process.env.OPENROUTER_API_KEY || "";

  const encoder = new TextEncoder();

  const sendError = (msg) => new Response(
    new ReadableStream({ start(c) {
      c.enqueue(encoder.encode(`data: {"type":"token","content":"${msg}","provider":"Error"}\n\n`));
      c.close();
    }}),
    { headers: { "Content-Type": "text/event-stream", "Access-Control-Allow-Origin": "*" } }
  );

  if (!groqKey && !geminiKey && !openrouterKey) {
    return sendError("⚠️ No API keys configured. Add GROQ_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY in Vercel environment variables.");
  }

  let body;
  try { body = await req.json(); } catch { return sendError("Invalid JSON body"); }

  const { cv, job_role, transcript, context = [], response_style = "live_script", target_role_family = "Auto Detect" } = body;

  if (!transcript) return sendError("No question transcript provided.");

  const systemPrompt = buildSystemPrompt(cv, job_role, response_style, target_role_family);
  const messages = buildMessages(systemPrompt, transcript, context);

  const stream = new ReadableStream({
    async start(controller) {
      let result = null;
      const errors = [];

      // 1️⃣ Try Groq first (fastest)
      if (groqKey) {
        try {
          result = await tryGroq(messages, groqKey);
        } catch (e) {
          errors.push(`Groq: ${e.message}`);
          console.log("Groq failed, trying Gemini...", e.message);
        }
      }

      // 2️⃣ Fallback to Gemini
      if (!result && geminiKey) {
        try {
          result = await tryGemini(messages, geminiKey);
        } catch (e) {
          errors.push(`Gemini: ${e.message}`);
          console.log("Gemini failed, trying OpenRouter...", e.message);
        }
      }

      // 3️⃣ Fallback to OpenRouter
      if (!result && openrouterKey) {
        try {
          result = await tryOpenRouter(messages, openrouterKey);
        } catch (e) {
          errors.push(`OpenRouter: ${e.message}`);
        }
      }

      if (result) {
        // Stream first token with metadata
        const firstChunk = { type: "token", content: "", provider: result.provider, intent: "SC Interview", role_family: target_role_family };
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(firstChunk)}\n\n`));
        // Stream the text word by word for teleprompter feel
        streamText(result.text, result.provider, controller, encoder);
        // Send done signal
        controller.enqueue(encoder.encode(`data: {"type":"done","provider":"${result.provider}"}\n\n`));
      } else {
        const errMsg = `All AI providers failed. Errors: ${errors.join(" | ")}`;
        controller.enqueue(encoder.encode(`data: {"type":"token","content":"${errMsg}","provider":"Error"}\n\n`));
      }

      controller.close();
    }
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Access-Control-Allow-Origin": "*"
    }
  });
}
