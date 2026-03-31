import os
import logging
from dotenv import load_dotenv
from typing import Tuple

logger = logging.getLogger(__name__)

load_dotenv()

import re
from typing import Tuple, Dict

async def generate_ai_response_with_llm(question: str, cv: str, job_role: str, context: list, response_style: str = "normal") -> Tuple[Dict[str, str], str]:
    """
    Calls OpenAI (multiple keys), Groq, and Gemini in sequence to generate a script for the candidate.
    Falls back to mock logic if all fail.
    Returns: (parsed_response_dict, provider_name)
    """
    if response_style == "concise":
        length_instruction = "Keep the script extremely concise, maybe 2 sentences max, directly getting to the point."
        style_instruction = "Write exactly how a real person speaks during an interview. Use contractions."
    elif response_style == "detailed":
        length_instruction = "Provide a detailed, thorough script (5-6 sentences) with a specific STAR method example if applicable."
        style_instruction = "Write exactly how a real person speaks during an interview. Use contractions."
    elif response_style == "live_script":
        length_instruction = "Keep the script extremely conversational and concise enough to read aloud comfortably in one take without running out of breath."
        style_instruction = """Write specifically for LIVE spoken delivery.
    - Use VERY short sentences.
    - Liberally use dashes (—) and commas to indicate natural pauses.
    - Incorporate natural fillers in moderation (e.g., "you know," "actually," "I mean").
    - VARY YOUR OPENING PHRASES. Do NOT always start with "Yeah, absolutely" or "Sure thing". Use varied openings like "To answer that...", "Well, looking back...", "That's an interesting point...", or just jump straight into the answer.
    - Ensure it sounds completely off-the-cuff and not like an essay."""
    else:
        length_instruction = "Keep the script a normal, conversational length (3-4 sentences)."
        style_instruction = "Write exactly how a real person speaks during an interview. Use contractions."

    system_prompt = f"""
    You are an expert AI Interview Copilot for a candidate applying for the role of '{job_role}'.
    Your goal is to analyze the interviewer's question, ground your response strictly in the candidate's CV and the Job Description, and provide a script for the candidate to read live.

    CRITICAL INSTRUCTIONS:
    1. First, classify the question INTENT (e.g., "introduce yourself", "why this role", "experience example", "behavioral STAR question", "supply chain analytics", etc.).
    2. Second, extract specific CV FACTS (companies, metrics, tools like SAP/Power BI, supply chain achievements) relevant to answering this question.
    3. Third, extract specific JD REQS (skills, expectations from the job role) that this answer should address.
    4. Fourth, generate the final spoken SCRIPT. The script MUST stitch together the CV FACTS to prove you meet the JD REQS, specifically answering the question asked.
       - {style_instruction}
       - Do not greet the interviewer. Start right into the spoken answer.
       - {length_instruction}

    You MUST format your EXACT response using the following tags. Do not use markdown blocks outside of these tags.

    INTENT: <classification here>
    CV_FACTS: <bulleted list or short summary of relevant CV facts here>
    JD_REQS: <bulleted list or short summary of relevant JD requirements here>
    SCRIPT: <the final conversational answer script here>

    Candidate's CV:
    {cv}

    Job Role / Description:
    {job_role}
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
                        max_tokens=350,
                        temperature=0.7
                    )
                    return _parse_llm_response(response.choices[0].message.content), "OpenAI"
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
                    max_tokens=350,
                    temperature=0.7
                )
                return _parse_llm_response(response.choices[0].message.content), "Groq"
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

                return _parse_llm_response(response.text), "Gemini"
            except Exception as e:
                 logger.warning(f"Gemini API Error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error executing LLM fallbacks: {str(e)}")

    # Final Fallback to Mock Logic
    logger.info("All LLM providers failed or missing keys. Falling back to mock logic.")
    return _mock_response(question, cv, job_role, response_style), "Mock (Local)"

def _parse_llm_response(raw_text: str) -> Dict[str, str]:
    """Parses the structured tags out of the LLM's response."""
    result = {
        "intent": "Unknown",
        "cv_facts": "None extracted",
        "jd_reqs": "None extracted",
        "script": raw_text # Default to full text if parsing fails
    }

    # Use regex to extract the sections
    intent_match = re.search(r"INTENT:\s*(.*?)(?=CV_FACTS:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    cv_match = re.search(r"CV_FACTS:\s*(.*?)(?=JD_REQS:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    jd_match = re.search(r"JD_REQS:\s*(.*?)(?=SCRIPT:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    script_match = re.search(r"SCRIPT:\s*(.*)", raw_text, re.DOTALL | re.IGNORECASE)

    if intent_match: result["intent"] = intent_match.group(1).strip()
    if cv_match: result["cv_facts"] = cv_match.group(1).strip()
    if jd_match: result["jd_reqs"] = jd_match.group(1).strip()
    if script_match:
        result["script"] = script_match.group(1).strip()

    return result

def _mock_response(question: str, cv: str, job_role: str, style: str = "normal") -> Dict[str, str]:
    lower_q = question.lower()

    response = {
        "intent": "General Inquiry",
        "cv_facts": "Analyzed standard CV metrics.",
        "jd_reqs": "Mapped to general job role.",
        "script": ""
    }

    if "yourself" in lower_q or "background" in lower_q:
        response["intent"] = "Introduce Yourself / Background"
        response["cv_facts"] = "Found 5 years experience in supply chain, logistics optimization, data analytics."
        response["jd_reqs"] = "Requires experienced supply chain professional."
        response["script"] = "To answer that—I've spent the last five years deeply embedded in supply chain logistics. I actually started out analyzing raw transport data, which eventually led to me leading a project that cut our freight costs by about 12%. I mean, I'm really passionate about using data to find those hidden efficiencies, which is exactly why I'm drawn to this role."
    elif "why" in lower_q and "role" in lower_q:
        response["intent"] = "Motivation / Why this role"
        response["cv_facts"] = "Experience managing vendor relations and reducing costs."
        response["jd_reqs"] = "Looking for someone to lead S&OP alignment."
        response["script"] = "Well, looking at the job description, your focus on S&OP alignment really stood out to me. In my last position, I actually bridged the gap between sales and operations, managing vendor relations to drop our lead times by 15%. I think my hands-on experience there makes this a really natural next step for me."
    elif "forecast" in lower_q or "accuracy" in lower_q:
        response["intent"] = "Experience Example / Forecasting"
        response["cv_facts"] = "Implemented new forecasting model in Python, increased accuracy by 18%."
        response["jd_reqs"] = "Requires advanced forecasting and demand planning."
        response["script"] = "That's an interesting point. Actually, just last year we were dealing with massive stockouts due to poor forecasting. I ended up pulling historical data and building a totally new forecasting model using Python. It was a bit of a heavy lift, but—you know—we ended up increasing our forecast accuracy by 18%."
    elif "s&op" in lower_q or "sales and operations" in lower_q:
        response["intent"] = "Cross-functional Collaboration / S&OP"
        response["cv_facts"] = "Led weekly S&OP meetings, aligned sales goals with supply capabilities."
        response["jd_reqs"] = "Must collaborate across departments."
        response["script"] = "Honestly, communication is everything there. I actually ran our weekly S&OP meetings for two years. The biggest challenge was always aligning the sales team's aggressive targets with what operations could actually deliver. I found that bringing hard data—like real-time inventory levels—to those meetings completely changed the conversation and removed the friction."
    else:
        response["intent"] = "Unknown / General"
        response["script"] = "That's a great question. Basically, looking at my background, I've always prioritized cross-functional alignment. I mean, leveraging data to drive decisions is really at the core of what I do."

    if style == "concise":
        response["script"] = "(Concise) " + response["script"]
    elif style == "detailed":
        response["script"] = "(Detailed) " + response["script"]

    return response