import os
import logging
from dotenv import load_dotenv
from typing import Tuple

logger = logging.getLogger(__name__)

load_dotenv()

async def generate_ai_response_with_llm(question: str, cv: str, job_role: str, context: list, response_style: str = "normal") -> Tuple[str, str]:
    """
    Calls OpenAI (multiple keys), Groq, and Gemini in sequence to generate a script for the candidate.
    Falls back to mock logic if all fail.
    Returns: (generated_response, provider_name)
    """
    if response_style == "concise":
        length_instruction = "Keep the answer extremely concise, maybe 2 sentences max, directly getting to the point."
    elif response_style == "detailed":
        length_instruction = "Provide a detailed, thorough answer (5-6 sentences) with a specific STAR method example if applicable."
    else:
        length_instruction = "Keep the answer a normal, conversational length (3-4 sentences)."

    system_prompt = f"""
    You are an expert AI Interview Copilot for a candidate applying for the role of '{job_role}', particularly focused on supply chain, demand planning, S&OP, and analytics.
    Your goal is to provide a natural-sounding, spoken-English script for the candidate to read live in response to the interviewer's question.

    CRITICAL INSTRUCTIONS:
    - The response must stitch together facts directly from the candidate's CV to answer the question.
    - Write exactly how a real person speaks during an interview. Do NOT write formal robotic text.
    - Start the answer naturally with conversational connectors, such as:
      "Sure —"
      "Yeah, absolutely."
      "So, in my previous role..."
      "One example that comes to mind is..."
      "That's a great question. Looking back at my time..."
    - Include commas and short pauses naturally. Use contractions (e.g., "I'm", "we've", "didn't").
    - Do not greet the interviewer (e.g., no "Hi there"). Start right into the spoken answer.
    - {length_instruction}

    Candidate's CV:
    {cv}
    """

    messages = [{"role": "system", "content": system_prompt}]

    # Add recent context (up to last 5 turns)
    for msg in context[-5:]:
        messages.append({"role": "user" if msg["role"] == "interviewer" else "assistant", "content": msg["text"]})

    messages.append({"role": "user", "content": f"Interviewer asked: {question}"})

    try:
        # Try OpenAI Keys First
        openai_keys_str = os.getenv("OPENAI_API_KEYS", "")
        if openai_keys_str:
            openai_keys = [k.strip() for k in openai_keys_str.split(",") if k.strip()]
            for key in openai_keys:
                try:
                    import openai
                    client = openai.AsyncOpenAI(api_key=key)
                    response = await client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        max_tokens=200,
                        temperature=0.7
                    )
                    return response.choices[0].message.content, "OpenAI"
                except Exception as e:
                    logger.warning(f"OpenAI API Error with key {key[:5]}...: {str(e)}")
                    continue # Try next key

        # Fallback to Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                from groq import AsyncGroq
                client = AsyncGroq(api_key=groq_key)
                response = await client.chat.completions.create(
                    model="llama3-8b-8192", # Example Groq model
                    messages=messages,
                    max_tokens=200,
                    temperature=0.7
                )
                return response.choices[0].message.content, "Groq"
            except Exception as e:
                logger.warning(f"Groq API Error: {str(e)}")

        # Fallback to Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')

                # Convert context to Gemini format
                gemini_history = []
                for msg in messages:
                    role = "user" if msg["role"] == "user" else "model"
                    # System prompt gets added as first user message or prepended
                    if msg["role"] == "system":
                       pass # Handled differently in Gemini, typically via system_instruction in 1.5 Pro, but for flash we can prepend
                    else:
                       gemini_history.append({"role": role, "parts": [msg["content"]]})

                # For simplicity with flash, we prepend system prompt to the first user message
                if gemini_history and gemini_history[0]["role"] == "user":
                    gemini_history[0]["parts"][0] = system_prompt + "\n\n" + gemini_history[0]["parts"][0]
                else:
                     gemini_history.insert(0, {"role": "user", "parts": [system_prompt]})

                # Get the actual question (last user message)
                last_msg = messages[-1]["content"]

                if len(gemini_history) == 1:
                    chat = model.start_chat(history=[])
                    response = chat.send_message(gemini_history[0]["parts"][0])
                else:
                    gemini_history = gemini_history[:-1]
                    chat = model.start_chat(history=gemini_history)
                    response = chat.send_message(last_msg)

                return response.text, "Gemini"
            except Exception as e:
                 logger.warning(f"Gemini API Error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error executing LLM fallbacks: {str(e)}")

    # Final Fallback to Mock Logic
    logger.info("All LLM providers failed or missing keys. Falling back to mock logic.")
    return _mock_response(question, cv, job_role, response_style), "Mock (Local)"

def _mock_response(question: str, cv: str, job_role: str, style: str = "normal") -> str:
    lower_q = question.lower()
    prefix = ""
    if style == "concise":
        prefix = "(Concise) "
    elif style == "detailed":
        prefix = "(Detailed) "

    if "supply chain" in lower_q:
        return f"{prefix}Yeah, absolutely. Looking at my CV, I've actually optimized our supply chain processes, which resulted in a solid cost reduction. I mainly utilized data analytics to tighten up our demand forecasting..."
    elif "data" in lower_q or "analytics" in lower_q:
        return f"{prefix}Sure — so in my previous role, I built several dashboards and data pipelines. That really improved data visibility across the team, which directly aligns with what you're looking for in this {job_role} position."
    elif "experience" in lower_q or "background" in lower_q:
        return f"{prefix}One example that comes to mind is my recent work aligning directly with the {job_role} requirements. I've spent a lot of time focusing on exactly these kinds of operational challenges."
    else:
        return f"{prefix}That's a great question. So, based on my background, I've always prioritized cross-functional alignment and leveraging data to drive my decisions."