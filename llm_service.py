import openai
import os

from dotenv import load_dotenv
load_dotenv()

client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "mock_key"))

async def generate_ai_response_with_llm(question: str, cv: str, job_role: str, context: list) -> str:
    """
    Calls OpenAI to generate a script for the candidate.
    """
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "mock_key":
        # Fallback if no real API key is provided during testing
        return _mock_response(question, cv, job_role)

    system_prompt = f"""
    You are an expert AI Interview Copilot for a candidate applying for the role of '{job_role}'.
    Your goal is to provide a natural-sounding, conversational script for the candidate to read in response to the interviewer's question.
    The response must stitch together facts from the candidate's CV to directly answer the question.
    Do not greet the interviewer. Just provide the direct answer script. Keep it concise (3-4 sentences).

    Candidate's CV:
    {cv}
    """

    messages = [{"role": "system", "content": system_prompt}]

    # Add recent context (up to last 5 turns)
    for msg in context[-5:]:
        messages.append({"role": "user" if msg["role"] == "interviewer" else "assistant", "content": msg["text"]})

    messages.append({"role": "user", "content": f"Interviewer asked: {question}"})

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return _mock_response(question, cv, job_role)

def _mock_response(question: str, cv: str, job_role: str) -> str:
    lower_q = question.lower()
    if "supply chain" in lower_q:
        return f"[Mock] Based on my CV, I have optimized supply chain processes resulting in cost reduction. I utilized data analytics to forecast demand..."
    elif "data" in lower_q or "analytics" in lower_q:
        return f"[Mock] In my previous role, I built dashboards and data pipelines that improved data visibility, directly aligning with the {job_role} requirements."
    elif "experience" in lower_q:
        return f"[Mock] I have relevant experience aligning with the {job_role} position."
    else:
        return "[Mock] That's a great question. Let me tell you about my background..."
