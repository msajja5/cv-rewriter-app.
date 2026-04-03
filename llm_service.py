import os
import logging
from dotenv import load_dotenv
from typing import Tuple

logger = logging.getLogger(__name__)

load_dotenv()

import re
from typing import Tuple, Dict, AsyncGenerator
from domain_knowledge import DOMAIN_KNOWLEDGE, detect_role_family, detect_question_routing
from candidate_profile import MANJUNATH_PROFILE
import json

async def generate_ai_response_with_llm_stream(
    question: str,
    cv: str,
    job_role: str,
    context: list,
    response_style: str = "normal",
    target_role_family: str = "Auto Detect",
    custom_keys: dict = None
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


    # Include up to the last 4 turns of conversation history for context
    history_str = ""
    if context:
        recent_context = context[-4:]
        history_str = "Recent Conversation History:\n" + "\n".join([f"{c.get('role', 'unknown').capitalize()}: {c.get('text', '')}" for c in recent_context])

    system_prompt = """You are an AI interview assistant generating a natural, spoken-language response for a candidate.
Follow these strict rules:
1. Speak in the FIRST PERSON ("I did this", "My experience").
2. Keep it conversational and concise. The target spoken length is 30-90 seconds.
3. Use metrics from the CV whenever available.
4. Prefer direct examples from the candidate's experience.
5. Admit uncertainty gracefully if the CV does not contain exact evidence (do not make up facts).
6. DO NOT use robotic introductions like "Thank you for that question."
7. DO NOT use bullet points or lists. Write in natural paragraphs meant to be read aloud off a teleprompter.

CANDIDATE CV / PROFILE:
{cv}

ROLE BEING INTERVIEWED FOR (INCLUDING TARGET COMPANY):
{job_role}

QUESTION TYPE DETECTED:
{intent}

RULES:
- ALWAYS prioritize information from the provided CANDIDATE CV over any internal generic knowledge.
- If the interviewer asks "what do you know about this company" or similar, use the TARGET COMPANY from the ROLE context.
- ONLY return the raw spoken script. Do not output INTENT or CV_FACTS tags, just the script directly."""

    # 5. Answer format rules

    messages = [{"role": "system", "content": system_prompt}]

    # Add recent context (up to last 8 turns)
    for msg in context[-8:]:
        messages.append({"role": "user" if msg["role"] == "interviewer" else "assistant", "content": msg["text"]})

    messages.append({"role": "user", "content": f"Interviewer asked: {question}"})

    custom_keys = custom_keys or {}

    def get_keys(env_var: str, custom_key_name: str) -> list:
        keys = []
        if custom_keys.get(custom_key_name):
            keys.append(custom_keys[custom_key_name])
        env_keys = [k.strip() for k in os.getenv(env_var, "").split(",") if k.strip()]
        keys.extend(env_keys)
        return keys

    # 1. Try Gemini (gemini-2.0-flash or 1.5 fallback)
    gemini_keys = get_keys("GEMINI_API_KEY", "X-Gemini-Key") or get_keys("GEMINI_KEYS", "X-Gemini-Key")

    for key in gemini_keys:
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            # Try 2.0 first, then 1.5
            model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=system_prompt)

            gemini_history = []
            for msg in messages[1:-1]: # Skip system and last user
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})

            last_msg = messages[-1]["content"]
            chat = model.start_chat(history=gemini_history)
            response_stream = chat.send_message(last_msg, stream=True)

            for chunk in response_stream:
                if chunk.text:
                    yield {
                        "type": "token",
                        "content": chunk.text,
                        "provider": "Gemini 2.0 Flash",
                        "intent": intent,
                        "role_family": resolved_role_family
                    }
            return # Success
        except Exception as e:
             logger.warning(f"Gemini API Error: {str(e)}")
             continue

    # 2. Fallback to Groq
    groq_keys = get_keys("GROQ_API_KEY", "X-Groq-Key") or get_keys("GROQ_KEYS", "X-Groq-Key")
    for key in groq_keys:
        try:
            import httpx
            import json
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 900,
                "temperature": 0.72,
                "stream": True
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                async with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            data = json.loads(line[6:])
                            token = data["choices"][0]["delta"].get("content", "")
                            if token:
                                yield {
                                    "type": "token",
                                    "content": token,
                                    "provider": "Groq Llama-3.3",
                                    "intent": intent,
                                    "role_family": resolved_role_family
                                }
            return # Success
        except Exception as e:
            logger.warning(f"Groq API Error: {str(e)}")
            continue

    # 3. Fallback to OpenAI / OpenRouter
    or_keys = get_keys("OR_KEYS", "X-Or-Key") or get_keys("OPENAI_API_KEYS", "X-Or-Key")
    for key in or_keys:
        try:
            import openai
            base_url = "https://openrouter.ai/api/v1" if key.startswith("sk-or") else None
            model_name = "meta-llama/llama-3.3-70b-instruct:free" if key.startswith("sk-or") else "gpt-4o-mini"
            client = openai.AsyncOpenAI(api_key=key, base_url=base_url)

            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=900,
                temperature=0.72,
                stream=True
            )
            async for chunk in response:
                token = chunk.choices[0].delta.content
                if token:
                    yield {
                        "type": "token",
                        "content": token,
                        "provider": model_name,
                        "intent": intent,
                        "role_family": resolved_role_family
                    }
            return # Success
        except Exception as e:
            logger.warning(f"OpenRouter/OpenAI API Error: {str(e)}")
            continue

    # Final Fallback to Mock Logic
    logger.info("All LLM providers failed or missing keys. Falling back to mock logic.")
    mock_dict = _mock_response(question, cv, job_role, response_style, resolved_role_family)
    # Stream the mock response in chunks to simulate network
    import asyncio
    words = mock_dict["script"].split(" ")
    for word in words:
        yield {
            "type": "token",
            "content": word + " ",
            "provider": "Mock (Local)",
            "intent": mock_dict["intent"],
            "role_family": resolved_role_family
        }
        await asyncio.sleep(0.02)

def _mock_response(question: str, cv: str, job_role: str, style: str, role_family: str) -> Dict[str, str]:
    response = {}
    lower_q = question.lower()

    if "company" in lower_q or "know about us" in lower_q or "why us" in lower_q:
        response["intent"] = "Company Knowledge / Fit"
        response["answer_strategy"] = "Company research -> align values with profile"
        response["script"] = f"That's a great question. Based on the job description for {job_role}, I know you are looking for someone who can drive efficiency and build strong cross-functional relationships. My background as outlined in my CV aligns perfectly with this, as I have a proven track record of reducing operational delays and improving forecast accuracy. I am very impressed by your company's recent growth and focus on innovation, and I am excited about the opportunity to bring my analytical approach to your team."

    elif any(word in lower_q for word in ["forecast", "demand", "s&op", "planning"]):
        response["intent"] = "Demand Planning / S&OP"
        response["answer_strategy"] = "S&OP failure -> statistical rebuild -> stakeholder alignment -> result"
        response["script"] = f"This is an area I've spent a lot of time optimizing. At a previous role, our consensus forecast accuracy was completely stagnant. The root of the problem wasn't necessarily the data itself, but rather that our sales and supply teams were operating in total silos. My task was to bridge that gap and rebuild our consensus planning process.\n\nTo tackle that, I pulled all our raw, historical sales data into {tool_mention}. I rebuilt our baseline statistical model from the ground up to automatically flag promotional outliers and seasonal shifts. But having the data wasn't enough; the real action was managing the stakeholders. I set up bi-weekly S&OP alignment meetings where I literally put the dashboard on the screen. Instead of arguing over opinions, I forced the conversation to revolve strictly around the data trends.\n\nAs a direct result, we broke down those silos entirely. Within about six months, we actually brought our consensus forecast accuracy up significantly, which dramatically reduced our expedited freight costs."

    elif any(word in lower_q for word in ["inventory", "trade", "service level", "stock"]):
        response["intent"] = "Supply Planning / Inventory Trade-off"
        response["answer_strategy"] = "Inventory trade-off -> framework (cost vs service) + example + KPI logic"
        response["script"] = f"That's an excellent question. Balancing inventory trade-offs is really the core of what we do. My fundamental framework is always strictly balancing our holding costs against the required target fill rate. During a particularly volatile period at {company_mention}, we realized we were carrying way too much safety stock just as a blind buffer against uncertainty.\n\nMy specific task was to lean out our inventory footprint without risking stockouts on key accounts. I started by using {tool_mention} to run a highly rigorous ABC/XYZ analysis. I completely re-segmented our portfolio, which allowed us to clearly see where we were over-indexed. I then presented this data to the commercial stakeholders to secure their buy-in on adjusting our service level agreements.\n\nThe final result was that we confidently dialed back inventory on our highly stable 'A' items while fiercely protecting service levels on our erratic 'Z' items. By executing that focused approach, we successfully reduced our overall working capital without suffering a single critical stockout."

    elif any(word in lower_q for word in ["system", "erp", "sap", "tool", "software"]):
        response["intent"] = "ERP / Systems / Implementation"
        response["answer_strategy"] = "ERP / SAP / Tools -> systems exposure + business usage + implementation/support angle"
        response["script"] = f"I've actually got extensive, hands-on experience in that area. A great example of this is from my time dealing with massive data quality issues in our manufacturing lines. The situation was chaotic because the legacy data was incredibly messy, and my task was to ensure our supply chain module functioned cleanly without disrupting our daily operations.\n\nMy role wasn't just about hitting buttons as an end-user. I was heavily involved in the actual business side of how the system functioned. I personally sat down and wrote out the functional specs to bridge the gap between our IT developers and our supply chain planners. I ran the rigorous user acceptance testing cycles, and I aggressively cleaned up our master data.\n\nBecause I applied such a disciplined approach to that system management and data governance, we saw a massive reduction in exceptions. Honestly, I know firsthand that a complex planning system is only ever as good as the raw data you feed into it."

    elif any(word in lower_q for word in ["data", "analytics", "dashboard", "tableau", "power bi"]):
        response["intent"] = "Data Analytics / Dashboards"
        response["answer_strategy"] = "Data analytics / KPI -> problem + dashboard built + business impact"
        response["script"] = f"I'm incredibly passionate about data analytics. We were struggling with a lack of visibility across our retail distribution network. The commercial and supply teams were operating off completely different spreadsheets, which made it impossible to accurately forecast demand.\n\nMy task was to build a single source of truth. I pulled the raw data and built a suite of complex dashboards, utilizing advanced metrics to segment our inventory accurately. I then rolled these dashboards out to the commercial and supply leadership, training them on how to actually read the data to make purchasing decisions.\n\nAs a direct result of giving everyone that clear, unified visibility, we were able to reduce our overall inventory holding costs by 20%. I take that same exact analytical approach into every role I step into."

    elif any(word in lower_q for word in ["conflict", "stakeholder", "interpersonal", "difficult", "disagree"]):
        response["intent"] = "Interpersonal / Soft Skills"
        response["answer_strategy"] = "S&OP / cross-functional -> conflict resolution + data-driven alignment"
        response["script"] = f"That's a really important question. I firmly believe that your technical skills are only as valuable as your ability to communicate them. A great example of my interpersonal skills in action was when the sales, finance, and operations teams were constantly clashing because they all had completely different priorities.\n\nMy task was to facilitate a consensus process and get everyone aligned. Instead of just arguing over opinions, I used my interpersonal skills to first understand each department's pain points. I then brought them all into the same room and projected our live dashboards onto the screen. I acted as the neutral mediator, forcing the conversation to revolve strictly around the hard data trends rather than departmental politics.\n\nBy leading with empathy but backing it up with rigorous data, I was able to break down those silos entirely. We established a fully integrated consensus forecast, which completely transformed the culture of our weekly meetings."

    else:
        response["intent"] = "Unknown / General Behavioral"
        response["answer_strategy"] = "Behavioral STAR story -> Situation, Task, Action, Result"
        response["script"] = f"That's a really good point, and a specific example that perfectly illustrates this comes to mind. We were facing a pretty significant cross-functional breakdown within our team. The core situation was that different departments were using completely different sets of numbers, which was leading to constant friction and severely delayed outputs. My task was to establish a single source of truth and rebuild trust across those stakeholders.\n\nI realized the issue wasn't a lack of effort, but a complete lack of visibility. So, I took the initiative to dive deep into our raw systems and build out a centralized, automated tracking dashboard. It took some intense, deep-focus analytical work to get the underlying logic right, but I eventually rolled it out to the leadership team, walking them through exactly how it worked so they trusted the numbers.\n\nAs a direct result, it immediately aligned everyone on the exact same real-time KPIs. We stopped arguing over whose spreadsheet was right and started actually solving problems, which significantly reduced our operational delays across the board."

    if style == "concise":
        response["script"] = "(Concise) " + response["script"]
    elif style == "detailed":
        response["script"] = "(Detailed) " + response["script"]

    return response