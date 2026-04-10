import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

def _get_client():
    key = os.getenv("GROQ_API_KEY", "")
    if key:
        return Groq(api_key=key)
    return None

async def generate_ai_response_with_llm(question: str, cv: str, job_role: str, context: list) -> str:
    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

    if not groq_key and not gemini_key and not openrouter_key:
        return _mock_response(question, cv, job_role)

    system_prompt = f"""You are an expert AI Interview Copilot helping Manjunath Sajjan — a Senior Supply Chain professional — answer interview questions in real-time.
He is applying for: '{job_role or 'a supply chain / planning role'}'.
Write a natural teleprompter script he can read aloud. 3-4 sentences. First-person, confident, conversational. No bullet points. Start directly with the answer.
Be specific: mention tools (Arkieva, SAP, Kinaxis, Power BI, Tableau), metrics (+27% forecast accuracy, -20% holding costs, €2B EMEA), and companies (Ontex, Nike, Solvay, QuEST Global) when relevant.
Never say 'As an AI'. Never repeat the question.

Candidate's CV:
{cv or '(not provided)'}"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in context[-6:]:
        messages.append({"role": "user" if msg["role"] == "interviewer" else "assistant", "content": msg["text"]})
    messages.append({"role": "user", "content": question})

    # 1. Try Groq
    if groq_key:
        try:
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq failed: {e}")

    # 2. Try Gemini via REST
    if gemini_key:
        try:
            import httpx
            contents = [m for m in messages if m["role"] != "system"]
            gemini_messages = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]} for m in contents]
            system_text = next((m["content"] for m in messages if m["role"] == "system"), "")
            res = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}",
                json={"system_instruction": {"parts": [{"text": system_text}]}, "contents": gemini_messages, "generationConfig": {"maxOutputTokens": 300, "temperature": 0.7}},
                timeout=15
            )
            data = res.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            if text:
                return text
        except Exception as e:
            print(f"Gemini failed: {e}")

    # 3. Try OpenRouter
    if openrouter_key:
        try:
            import httpx
            res = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                json={"model": "meta-llama/llama-3.3-70b-instruct:free", "messages": messages, "max_tokens": 300, "temperature": 0.7},
                timeout=15
            )
            text = res.json()["choices"][0]["message"]["content"]
            if text:
                return text
        except Exception as e:
            print(f"OpenRouter failed: {e}")

    return _mock_response(question, cv, job_role)

def _mock_response(question: str, cv: str, job_role: str) -> str:
    lower_q = question.lower()
    if "supply chain" in lower_q or "planning" in lower_q:
        return "In my role at Ontex, I led demand and supply planning across 12 global sites using Arkieva, which improved forecast accuracy by 27%. I also built Power BI dashboards to track OTIF and DIO KPIs in real time."
    elif "data" in lower_q or "analytics" in lower_q:
        return "At Nike, I developed Tableau dashboards for supplier KPIs and ran demand optimizer simulations to reduce holding costs by 20% across the EMEA retail network worth €2B."
    elif "experience" in lower_q or "background" in lower_q:
        return f"I have over 5 years of supply chain experience across FMCG and manufacturing, working with Ontex, Nike, and Solvay. My expertise is in demand forecasting, capacity planning, and data-driven decision-making — all directly relevant to the {job_role} role."
    else:
        return f"Based on my experience at Ontex and Nike, I've built strong expertise in {job_role} through hands-on work with SAP, Arkieva, and advanced analytics tools."
