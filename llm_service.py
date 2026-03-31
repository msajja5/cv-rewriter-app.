import os
import logging
from dotenv import load_dotenv
from typing import Tuple

logger = logging.getLogger(__name__)

load_dotenv()

import re
from typing import Tuple, Dict
from domain_knowledge import DOMAIN_KNOWLEDGE, detect_role_family

async def generate_ai_response_with_llm(
    question: str,
    cv: str,
    job_role: str,
    context: list,
    response_style: str = "normal",
    target_role_family: str = "Auto Detect"
) -> Tuple[Dict[str, str], str]:
    """
    Calls OpenAI (multiple keys), Groq, and Gemini in sequence to generate a script for the candidate.
    Falls back to mock logic if all fail.
    Returns: (parsed_response_dict, provider_name)
    """
    if target_role_family == "Auto Detect":
        resolved_role_family = detect_role_family(job_role)
    else:
        resolved_role_family = target_role_family

    # Get Domain Knowledge
    domain_info = DOMAIN_KNOWLEDGE.get(resolved_role_family, {
        "themes": ["supply chain efficiency"],
        "kpis": ["cost savings"],
        "tools": ["Excel", "ERP"],
        "language": ["cross-functional alignment"]
    })

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
    You are an expert AI Interview Copilot for a candidate applying for a '{resolved_role_family}' role.
    Target Job Details: '{job_role}'.

    You must answer as an experienced professional specifically trained in {resolved_role_family} concepts.
    Domain Intelligence:
    - Focus Themes: {', '.join(domain_info.get('themes', []))}
    - Key Metrics (KPIs): {', '.join(domain_info.get('kpis', []))}
    - Industry Tools: {', '.join(domain_info.get('tools', []))}
    - Expected Language/Jargon: {', '.join(domain_info.get('language', []))}

    Your goal is to analyze the interviewer's question, ground your response strictly in the candidate's CV and the Job Description, and provide a script for the candidate to read live.

    CRITICAL INSTRUCTIONS:
    1. INTENT: Classify the question intent (e.g., "introduce yourself", "why this role", "behavioral STAR question").
    2. ROLE_FAMILY: Identify the relevant supply chain domain (e.g., {resolved_role_family}).
    3. CV_FACTS: Extract specific CV FACTS (companies like Ontex, Nike, Solvay, QuEST Global, specific metrics, tools like SAP, Power BI, Tableau) relevant to answering this question.
    4. JD_SIGNALS: Extract specific company, industry, or JD requirement signals that this answer addresses.
    5. SCRIPT: Generate the final spoken answer.
       - The script MUST weave the targeted CV_FACTS together to answer the question, using the Domain Intelligence terminology listed above.
       - The script must NOT sound generic. It must explicitly mention the extracted CV facts (companies, tools, specific metrics) and directly relate them to the JD_SIGNALS.
       - {style_instruction}
       - Do not greet the interviewer. Start right into the spoken answer.
       - {length_instruction}

    You MUST format your EXACT response using the following tags. Do not use markdown blocks outside of these tags.

    INTENT: <classification here>
    ROLE_FAMILY: {resolved_role_family}
    CV_FACTS: <bulleted list or short summary of relevant CV facts here>
    JD_SIGNALS: <bulleted list or short summary of relevant JD signals here>
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
    return _mock_response(question, cv, job_role, response_style, resolved_role_family), "Mock (Local)"

def _parse_llm_response(raw_text: str) -> Dict[str, str]:
    """Parses the structured tags out of the LLM's response."""
    result = {
        "intent": "Unknown",
        "role_family": "Unknown",
        "cv_facts": "None extracted",
        "jd_signals": "None extracted",
        "script": raw_text # Default to full text if parsing fails
    }

    # Use regex to extract the sections
    intent_match = re.search(r"INTENT:\s*(.*?)(?=ROLE_FAMILY:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    role_match = re.search(r"ROLE_FAMILY:\s*(.*?)(?=CV_FACTS:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    cv_match = re.search(r"CV_FACTS:\s*(.*?)(?=JD_SIGNALS:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    jd_match = re.search(r"JD_SIGNALS:\s*(.*?)(?=SCRIPT:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    script_match = re.search(r"SCRIPT:\s*(.*)", raw_text, re.DOTALL | re.IGNORECASE)

    if intent_match: result["intent"] = intent_match.group(1).strip()
    if role_match: result["role_family"] = role_match.group(1).strip()
    if cv_match: result["cv_facts"] = cv_match.group(1).strip()
    if jd_match: result["jd_signals"] = jd_match.group(1).strip()
    if script_match:
        result["script"] = script_match.group(1).strip()

    return result

def _mock_response(question: str, cv: str, job_role: str, style: str, role_family: str) -> Dict[str, str]:
    lower_q = question.lower()
    cv_lower = cv.lower()

    # Heuristically pull personalized facts from CV for mock mode
    facts = []
    if "ontex" in cv_lower: facts.append("Ontex")
    if "nike" in cv_lower: facts.append("Nike")
    if "solvay" in cv_lower: facts.append("Solvay")
    if "quest global" in cv_lower: facts.append("QuEST Global")

    if "power bi" in cv_lower: facts.append("Power BI")
    if "tableau" in cv_lower: facts.append("Tableau")
    if "sap" in cv_lower: facts.append("SAP")

    cv_facts_str = ", ".join(facts) if facts else "General supply chain background"
    company_mention = facts[0] if facts else "my previous company"
    tool_mention = "SAP" if "sap" in cv_lower else "Power BI" if "power bi" in cv_lower else "ERP tools"

    response = {
        "intent": "General Inquiry",
        "role_family": role_family,
        "cv_facts": cv_facts_str,
        "jd_signals": f"Detected target: {role_family} requirements.",
        "script": ""
    }

    if "yourself" in lower_q or "background" in lower_q:
        response["intent"] = "Introduce Yourself / Background"

        if role_family == "Demand Planning":
            response["script"] = f"To answer that—I've spent the last few years heavily focused on demand forecasting and S&OP alignment. Specifically at {company_mention}, I was responsible for cleaning historical sales data and managing promotional lift to improve our overall forecast accuracy. I mean, I really enjoy diving into {tool_mention} to pull out baseline trends, which is exactly why this Demand Planning role caught my eye."
        elif role_family == "Procurement / Buyer":
            response["script"] = f"To answer that—my background is deeply rooted in strategic sourcing and vendor management. During my time at {company_mention}, I handled supplier negotiations that directly led to significant cost savings and better MOQ agreements. I'm very comfortable managing risk and lead times across the supply base, and that aligns perfectly with what you need here."
        elif role_family == "Data Analytics":
            response["script"] = f"To answer that—I'm a data-driven analyst at heart. I spent a lot of my time at {company_mention} building out actionable dashboards in {tool_mention} and streamlining our ETL pipelines. My core focus has always been on translating complex raw data into clear KPI storytelling for leadership."
        elif role_family == "ERP / Planning Systems":
            response["script"] = f"To answer that—I specialize in bridging the gap between business processes and technical implementations. At {company_mention}, I played a key role in our recent system rollout, handling everything from business requirement gathering and UAT testing to hypercare support. Working extensively with {tool_mention} master data taught me how critical cross-functional alignment really is."
        else: # Supply Planning / Inventory / General
            response["script"] = f"To answer that—I've spent my career optimizing end-to-end supply chain flows. Over at {company_mention}, I focused heavily on balancing capacity constraints with inventory service levels. I relied extensively on {tool_mention} to track our core KPIs and really drive down working capital."

    elif "why" in lower_q and "role" in lower_q:
        response["intent"] = "Motivation / Why this role"
        response["script"] = f"Well, looking at your job description, your focus on {role_family} really stood out to me. At {company_mention}, I was already doing very similar work—driving cross-functional alignment and managing those key metrics. I think bringing my hands-on experience with {tool_mention} into your environment makes this a really natural next step for me."

    elif "forecast" in lower_q or "accuracy" in lower_q:
        response["intent"] = "Experience Example / Forecasting"
        response["script"] = f"That's an interesting point. Actually, while I was at {company_mention}, we were dealing with significant forecast bias due to poor historical data. I ended up pulling the data into {tool_mention} and essentially rebuilding our baseline statistical forecasting model. It was a bit of a heavy lift, but—you know—we ultimately stabilized our MAPE and significantly improved our consensus planning."

    elif "inventory" in lower_q or "trade-off" in lower_q or "service level" in lower_q:
        response["intent"] = "Experience Example / Inventory Trade-offs"
        response["script"] = f"Honestly, managing that balance is the core of {role_family}. At {company_mention}, we constantly had to weigh holding costs against our target fill rates. I ran a detailed ABC/XYZ analysis using {tool_mention} to optimize our safety stock parameters. It allowed us to reduce our SLOBs without hurting our core service levels."

    elif "sap" in lower_q or "planning tool" in lower_q or "system" in lower_q:
        response["intent"] = "Experience Example / Systems & Tools"
        response["script"] = f"Sure thing. I've had extensive exposure to planning systems, particularly {tool_mention}. During my time with {company_mention}, I wasn't just a passive user; I actively participated in mapping out functional specs and cleaning up the material master data before cutover. I know firsthand how critical accurate master data is to making these systems actually work."

    else:
        response["intent"] = "Unknown / General"
        response["script"] = f"That's a great question. Basically, looking at my background with {company_mention}, I've always prioritized cross-functional alignment within {role_family}. I mean, leveraging {tool_mention} to drive decisions and hit those core KPIs is really at the heart of what I do."

    if style == "concise":
        response["script"] = "(Concise) " + response["script"]
    elif style == "detailed":
        response["script"] = "(Detailed) " + response["script"]

    return response