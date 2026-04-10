import Groq from "groq-sdk";
export const config = { runtime: "edge" };
export default async function handler(req) {
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
  const groqKey = req.headers.get("x-groq-key") || process.env.GROQ_API_KEY || "";
  if (!groqKey) {
    const s = new ReadableStream({ start(c) { c.enqueue(new TextEncoder().encode(`data: {"type":"token","content":"⚠️ No Groq key. Enter it in Tab 3 (API Keys).","provider":"No Key"}\n\n`)); c.close(); }});
    return new Response(s, { headers: { "Content-Type": "text/event-stream" } });
  }
  const { cv, job_role, transcript, context = [], response_style = "live_script", target_role_family = "Auto Detect" } = await req.json();
  const styles = {
    live_script: "Natural spoken script, 3-4 sentences, direct, use 'I'. No bullets.",
    concise: "1-2 sentences only.",
    normal: "3-4 clear sentences.",
    detailed: "STAR method: Situation, Task, Action, Result (5-6 sentences)."
  };
  const systemPrompt = `You are an AI Interview Copilot for a Supply Chain professional applying for: "${job_role || 'supply chain role'}". Role family: ${target_role_family}. Style: ${styles[response_style] || styles.live_script}\nCV:\n${cv || "(not provided)"}\nAnswer ONLY the question. Be specific and confident. Never say "As an AI".`;
  const messages = [{ role: "system", content: systemPrompt }];
  context.slice(-6).forEach(m => messages.push({ role: m.role === "interviewer" ? "user" : "assistant", content: m.text }));
  messages.push({ role: "user", content: transcript });
  const groq = new Groq({ apiKey: groqKey });
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const completion = await groq.chat.completions.create({
          model: "llama-3.3-70b-versatile",
          messages,
          max_tokens: 300,
          temperature: 0.7,
          stream: true
        });
        let first = true;
        for await (const chunk of completion) {
          const token = chunk.choices[0]?.delta?.content || "";
          if (token) {
            const p = { type: "token", content: token, provider: "Groq Llama-3.3" };
            if (first) { p.intent = "SC Interview"; p.role_family = target_role_family; first = false; }
            controller.enqueue(encoder.encode(`data: ${JSON.stringify(p)}\n\n`));
          }
        }
      } catch (e) {
        controller.enqueue(encoder.encode(`data: {"type":"token","content":"Error: ${e.message}","provider":"Error"}\n\n`));
      }
      controller.close();
    }
  });
  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", "Access-Control-Allow-Origin": "*" }
  });
}
