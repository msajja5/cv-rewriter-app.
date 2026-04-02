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
        length_instruction = "Provide a detailed, natural language response structured for spoken delivery without sounding like a bulleted list or a corporate essay."
        style_instruction = """Write specifically for LIVE spoken delivery.
    - Use varied sentence lengths. Use conversational pacing.
    - Use contractions everywhere (I'm, we've, they'll).
    - Liberally use dashes (—) and commas to indicate natural pauses.
    - Incorporate natural fillers in moderation (e.g., "you know," "actually," "I mean").
    - Start directly, but VARY YOUR OPENING PHRASES. Do NOT always start with "Yeah, absolutely" or "Sure thing". Use varied openings like "To answer that...", "Well, looking back...", "That's an interesting point...", or just jump straight into the answer.
    - Explain your past experience thoroughly and conversationally, but do not read like a book script. Speak like an experienced human having an in-depth conversation over coffee."""
    else:
        length_instruction = "Provide a detailed, thorough script (3-5 paragraphs) explaining your experience in a natural, conversational manner."
        style_instruction = "Write exactly how a real person speaks during an in-depth interview. Use contractions."

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
    1. INTENT: Classify the exact question meaning (e.g., "small talk/logistics", "introduce yourself", "why this role", "forecasting example", "inventory trade-off", "systems/SAP").
    2. ANSWER_STRATEGY: Select one of the following explicit answer strategies to structure your response:
       - "Small talk / logistics" -> 1-2 word natural confirmation (e.g., "Yes, I can hear you perfectly.", "I'm doing well, thanks.")
       - "Introduce yourself" -> 1. The Hook (Value Signal/Continuous delivery) + 2. The Anchors (Discipline & Adaptive Project) + 3. The Curiosity Gap (The Invitation)
       - "Why this role" -> motivation + match to JD + value I can bring
       - "Strengths" -> top 2 relevant skills + brief example
       - "Weakness" -> real development area + active mitigation
       - "Forecasting example" -> specific achievement with numbers + root cause + action
       - "Inventory trade-off" -> framework (cost vs service) + example + KPI logic
       - "S&OP / cross-functional" -> conflict resolution + data-driven alignment
       - "Procurement / supplier" -> negotiation strategy + risk management + savings
       - "Data analytics / KPI" -> problem + dashboard built + business impact
       - "ERP / SAP / Tools" -> systems exposure + business usage + implementation/support angle
       - "Master data" -> data governance + business impact + cross-functional coordination
       - "Behavioral STAR story" -> Situation, Task, Action, Result
    3. ROLE_FAMILY: Identify the relevant supply chain domain (e.g., {resolved_role_family}).
    4. CV_FACTS: Extract explicit CV evidence (companies like Ontex, Nike, Solvay, QuEST Global, specific metrics, tools like SAP, Power BI, Tableau) relevant to answering this exact question.
    5. JD_SIGNALS: Extract specific company, industry, or JD requirement signals that this answer addresses.
    6. SCRIPT: Generate the final spoken answer based STRICTLY on the chosen ANSWER_STRATEGY.
       - Do NOT use broad generic openings (like "I've always focused on cross-functional alignment") unless explicitly tied to a specific CV example.
       - The script MUST weave the targeted CV_FACTS together to answer the exact question asked.
       - {style_instruction}
       - Do not greet the interviewer. Start right into the spoken answer.
       - {length_instruction}

    You MUST format your EXACT response using the following tags. Do not use markdown blocks outside of these tags.

    INTENT: <classification here>
    ANSWER_STRATEGY: <selected strategy from the list above>
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
        "answer_strategy": "Unknown",
        "role_family": "Unknown",
        "cv_facts": "None extracted",
        "jd_signals": "None extracted",
        "script": raw_text # Default to full text if parsing fails
    }

    # Use regex to extract the sections
    intent_match = re.search(r"INTENT:\s*(.*?)(?=ANSWER_STRATEGY:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    strategy_match = re.search(r"ANSWER_STRATEGY:\s*(.*?)(?=ROLE_FAMILY:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    role_match = re.search(r"ROLE_FAMILY:\s*(.*?)(?=CV_FACTS:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    cv_match = re.search(r"CV_FACTS:\s*(.*?)(?=JD_SIGNALS:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    jd_match = re.search(r"JD_SIGNALS:\s*(.*?)(?=SCRIPT:|$)", raw_text, re.DOTALL | re.IGNORECASE)
    script_match = re.search(r"SCRIPT:\s*(.*)", raw_text, re.DOTALL | re.IGNORECASE)

    if intent_match: result["intent"] = intent_match.group(1).strip()
    if strategy_match: result["answer_strategy"] = strategy_match.group(1).strip()
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

    tools = []
    if "power bi" in cv_lower: tools.append("Power BI")
    if "tableau" in cv_lower: tools.append("Tableau")
    if "sap" in cv_lower: tools.append("SAP")

    cv_facts_str = ", ".join(facts + tools) if (facts or tools) else "General supply chain background"
    company_mention = facts[0] if facts else "my current role"
    tool_mention = tools[0] if tools else "our core planning systems"

    response = {
        "intent": "General Inquiry",
        "answer_strategy": "Behavioral STAR story",
        "role_family": role_family,
        "cv_facts": cv_facts_str,
        "jd_signals": f"Required {role_family} competencies.",
        "script": ""
    }

    if ("hear me" in lower_q or "can you see" in lower_q or "see my screen" in lower_q or "how are you" in lower_q or "hello" in lower_q.split() or "hi" in lower_q.split()) and len(lower_q.split()) < 8:
        response["intent"] = "Small Talk / Logistics"
        response["answer_strategy"] = "Small talk / logistics -> 1-2 word natural confirmation"

        if "hear me" in lower_q:
            response["script"] = "Yep, I can hear you perfectly."
        elif "see" in lower_q or "screen" in lower_q:
            response["script"] = "Yes, I can see it clearly."
        elif "how are you" in lower_q:
            response["script"] = "I'm doing great, thank you! How are you?"
        else:
            response["script"] = "Hello! Thanks for having me today."

    elif "yourself" in lower_q or "background" in lower_q:
        response["intent"] = "Introduce Yourself / Background"
        response["answer_strategy"] = "Introduce yourself -> 1. The Hook (Value Signal/Continuous delivery) + 2. The Anchors (Discipline & Adaptive Project) + 3. The Curiosity Gap (The Invitation)"

        response["script"] = f"I specialize in high-intensity, continuous delivery environments where I've mastered the art of staying physically and mentally sharp during long-haul analytical sessions. I don't just complete tasks; I optimize my personal workflow and my environment to ensure that the quality of my output at hour eight is just as high as it was at hour one.\n\nI've developed a rigorous personal protocol for maintaining focus. For me, peak performance is a result of consistent, hourly resets. This level of self-discipline translates directly into my work—whether it's managing complex {role_family} data at {company_mention} using {tool_mention} or hitting tight deadlines, I have a proven track record of maintaining momentum without burning out.\n\nIn my recent work, I've focused heavily on technical troubleshooting and optimizing our core KPIs. I've found that my best breakthroughs happen when I bridge the gap between deep-focus 'sitting' work and active, lateral thinking. This approach helped me solve massive alignment issues by looking at them from a fresh perspective during one of my planned breaks.\n\nI've actually found that this structured approach to my workday has helped me catch errors that others often miss during long shifts. I'd love to tell you more about how I applied that specific 'reset' mindset to streamline my last project if you're interested."

    elif "why" in lower_q and "role" in lower_q:
        response["intent"] = "Motivation / Why this role"
        response["answer_strategy"] = "Why this role -> motivation + match to JD + value I can bring"

        response["script"] = f"Well, what really drew me to this role is your explicit focus on driving measurable {role_family} outcomes, which completely aligns with how I've built my career. Looking back at my work with {company_mention}, I wasn't just maintaining the status quo—I was actively leveraging {tool_mention} to completely streamline our planning cycles and drop lead times.\n\nI really appreciate that your job description highlights the need for rigorous, data-driven discipline. I've spent years developing exactly that kind of workflow to ensure I don't just execute, but I actually optimize the processes I touch. I know I can step right into this position and immediately bring that same level of continuous value to your team."

    elif "forecast" in lower_q or "accuracy" in lower_q:
        response["intent"] = "Forecasting / Demand Planning"
        response["answer_strategy"] = "Forecasting example -> specific achievement with numbers + root cause + action"

        response["script"] = f"Sure, that's a great area to touch on. Back at {company_mention}, we actually ran into a major issue where our forecast accuracy was hovering right around 65%. The root of the problem was that our sales and supply teams were totally misaligned, operating in silos.\n\nI knew we needed a structural fix, so I took it upon myself to pull all our historical data into {tool_mention}. I essentially rebuilt our baseline statistical model from the ground up to automatically flag those outliers. By applying that deep-focus analytical approach I mentioned earlier, I was able to catch inconsistencies that were previously overlooked. Within about six months, that one major overhaul brought our consensus forecast accuracy up to 82%."

    elif "inventory" in lower_q or "trade-off" in lower_q or "service level" in lower_q:
        response["intent"] = "Supply Planning / Inventory Trade-off"
        response["answer_strategy"] = "Inventory trade-off -> framework (cost vs service) + example + KPI logic"

        response["script"] = f"That's an excellent question, as it's really the core of what we do. Basically, my fundamental framework for inventory management is always balancing our holding costs against the required target fill rate. You can't maximize both without being incredibly disciplined with your data.\n\nFor instance, at {company_mention}, we realized we were carrying way too much safety stock just as a buffer against uncertainty. I ended up using {tool_mention} to run a highly rigorous ABC/XYZ analysis. That allowed us to confidently dial back inventory on our stable 'A' items while still fiercely protecting service levels on our highly volatile 'Z' items. Ultimately, we successfully reduced our overall working capital by 12% without suffering a single stockout."

    elif "sap" in lower_q or "planning tool" in lower_q or "system" in lower_q:
        response["intent"] = "ERP / Systems / Implementation"
        response["answer_strategy"] = "ERP / SAP / Tools -> systems exposure + business usage + implementation/support angle"

        response["script"] = f"I've actually got extensive, hands-on experience in that area, particularly working deeply with {tool_mention}. While I was with {company_mention}, my role wasn't just about hitting buttons as an end-user—I was heavily involved in the actual business side of how the system functioned.\n\nI personally wrote functional specs, ran the user acceptance testing cycles, and constantly drove the effort to clean up our master data. Honestly, I know firsthand that a complex planning system is only ever as good as the raw data you feed into it, which is why I apply such a rigorous, disciplined approach to system management and data governance."

    else:
        response["intent"] = "Unknown / General Behavioral"
        response["answer_strategy"] = "Behavioral STAR story -> Situation, Task, Action, Result"
        response["script"] = f"That's a really good point, and a specific example that comes to mind is from my time over at {company_mention}. We were facing a pretty significant cross-functional breakdown within our {role_family} team, which was leading to a lot of frustration and delayed outputs.\n\nI realized the issue wasn't effort, but visibility. So, I took the initiative to build out a centralized, automated tracking dashboard using {tool_mention}. It took some intense, deep-focus work to get the logic right, but it immediately aligned everyone on the exact same real-time KPIs. And as a direct result, we significantly reduced our operational delays across the board."

    if style == "concise":
        response["script"] = "(Concise) " + response["script"]
    elif style == "detailed":
        response["script"] = "(Detailed) " + response["script"]

    return response