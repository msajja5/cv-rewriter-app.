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

    # 1. Identity & Framing
    system_prompt = "You are a candidate speaking in a live job interview. You read answers directly on screen. Write EXACTLY what the candidate would say — in their voice, grounded in their real career history.\n\n"

    # 2. Target role context
    system_prompt += f"ROLE BEING INTERVIEWED FOR (INCLUDING TARGET COMPANY): {job_role}\n\n"

    # 3. Question-type routing
    intent = detect_question_routing(question)
    system_prompt += f"QUESTION TYPE DETECTED: {intent}\n\n"

    # 4. Full Candidate Profile (CV)
    system_prompt += f"CANDIDATE CV / PROFILE:\n{cv}\n\n"

    # 5. Answer format rules
    system_prompt += """RULES:
- ALWAYS prioritize information from the provided CANDIDATE CV over any internal generic knowledge.
- If the interviewer asks \"what do you know about this company\" or similar, use the TARGET COMPANY from the ROLE context.
- Natural spoken English.
- STAR structure woven invisibly.
- 3-4 paragraphs, blank line between each.
- Use conversational connectors: \"So,\", \"Basically,\", \"What I did was,\", \"Honestly,\", \"At the end of the day.\"
- NEVER start with: \"Certainly\", \"Great question\", \"Absolutely\", \"Sure\".
- First person (\"I\") only. Max 2-3 sentences per paragraph.
- ONLY return the raw spoken script. Do not output INTENT or CV_FACTS tags, just the script directly."""
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
        response["answer_strategy"] = "Introduce yourself -> Name & core expertise + career arc (QuEST -> Solvay -> Nike -> Ontex) + why this role"

        response["script"] = f"Hi, my name is Manjunath Sajjan. To give you a high-level overview, I've spent the last 7 years deeply embedded in end-to-end supply chain roles, specifically bridging the gap between heavy technical systems and practical business execution.\n\nMy career really started over at QuEST Global, where I was a Kinaxis Consultant. I led major planning tool implementations for companies like ExxonMobil and Bombardier, cutting planning cycles down from weeks to just hours. That's where I really built my foundational understanding of advanced planning systems.\n\nFrom there, I wanted to get closer to the business side, so I took on Supply Chain Analyst roles at Solvay in France and then Nike here in Belgium. At Solvay, I was heavy into SAP MRP and master data governance—I actually resolved over 1,500 data defects to bring our master data completeness from 60% up to 99%. At Nike, I shifted focus towards demand forecasting and building Tableau dashboards to align the commercial and supply teams across our €2 billion retail network.\n\nFor the last three years, I've been with Ontex as a Supply Chain Consultant, managing a €4 billion portfolio across 12 global plants. That role has been highly cross-functional. I spearheaded our Arkieva implementation to improve forecast accuracy by 27%, drove a consensus S&OP process, and managed to secure €60 million in procurement savings. \n\nRight now, I'm looking to take that blend of strategic S&OP experience and deep technical expertise in tools like SAP S/4HANA and Power BI, and apply it directly to the {role_family} challenges you've outlined for this role."

    elif ("why" in lower_q and "role" in lower_q) or "why do you want" in lower_q or "why do you like" in lower_q or "interested in" in lower_q or "join this" in lower_q:
        response["intent"] = "Motivation / Why this role"
        response["answer_strategy"] = "Why this role -> motivation + match to JD + value I can bring"

        response["script"] = f"Well, what really drew me to this role is your explicit focus on driving measurable {role_family} outcomes, which completely aligns with how I've built my career. Looking back at my work with {company_mention}, I wasn't just maintaining the status quo—I was actively leveraging {tool_mention} to completely streamline our planning cycles and drop lead times.\n\nI really appreciate that your job description highlights the need for rigorous, data-driven discipline. I've spent years developing exactly that kind of workflow to ensure I don't just execute, but I actually optimize the processes I touch. I know I can step right into this position and immediately bring that same level of continuous value to your team."

    elif "forecast" in lower_q or "accuracy" in lower_q:
        response["intent"] = "Forecasting / Demand Planning"
        response["answer_strategy"] = "Forecasting example -> specific achievement with numbers + root cause + action"

        response["script"] = f"Sure, that's a great area to touch on, and I'll give you a specific example of how I handle that. Back at {company_mention}, the core issue we faced was that our forecast accuracy was completely stagnant at around 65%. The root of the problem wasn't necessarily the data itself, but rather that our sales team and our supply team were operating in total silos, which made my task to bridge that gap and rebuild our consensus planning process.\n\nTo tackle that, I knew I needed a structural fix that was rooted in hard facts. I took it upon myself to pull all our raw, historical sales data into {tool_mention}. Applying that same deep-focus analytical approach I mentioned earlier, I essentially rebuilt our baseline statistical model from the ground up to automatically flag promotional outliers and seasonal shifts. But having the data wasn't enough; the real action was managing the stakeholders. I set up bi-weekly S&OP alignment meetings where I literally put the {tool_mention} dashboard on the screen. Instead of arguing over opinions, I forced the conversation to revolve strictly around the data trends I had uncovered.\n\nAs a direct result of combining that rigorous analytical overhaul with tight stakeholder management, we broke down those silos entirely. Within about six months, we actually brought our consensus forecast accuracy up from 65% to 82%, which significantly reduced our expedited freight costs."

    elif "inventory" in lower_q or "trade-off" in lower_q or "service level" in lower_q:
        response["intent"] = "Supply Planning / Inventory Trade-off"
        response["answer_strategy"] = "Inventory trade-off -> framework (cost vs service) + example + KPI logic"

        response["script"] = f"That's an excellent question, as balancing inventory trade-offs is really the core of what we do. My fundamental framework is always strictly balancing our holding costs against the required target fill rate, and you simply can't maximize both without being incredibly disciplined with your data. For example, during a particularly volatile period at {company_mention}, we realized we were carrying way too much safety stock just as a blind buffer against uncertainty, tying up a massive amount of working capital.\n\nMy specific task was to lean out our inventory footprint without risking stockouts on key accounts. I started by isolating myself with the raw data and using {tool_mention} to run a highly rigorous ABC/XYZ analysis. I completely re-segmented our portfolio, which allowed us to clearly see where we were over-indexed. I then presented this data to the commercial stakeholders to secure their buy-in on adjusting our service level agreements.\n\nThe final result was that we confidently dialed back inventory on our highly stable 'A' items while fiercely protecting service levels on our erratic 'Z' items. By executing that focused, data-driven approach, we successfully reduced our overall working capital by 12% without suffering a single critical stockout."

    elif "sap" in lower_q or "planning tool" in lower_q or "system" in lower_q:
        response["intent"] = "ERP / Systems / Implementation"
        response["answer_strategy"] = "ERP / SAP / Tools -> systems exposure + business usage + implementation/support angle"

        response["script"] = f"I've actually got extensive, hands-on experience in that area, particularly working deeply with SAP S/4HANA and MRP modules. A great example of this is from my time at Solvay, where we were dealing with massive data quality issues in our chemical manufacturing lines. The situation was chaotic because the legacy data was incredibly messy—we had over 1,500 master data defects—and my task was to ensure our supply chain module functioned cleanly without disrupting our daily operations.\n\nMy role wasn't just about hitting buttons as an end-user. I was heavily involved in the actual business side of how the system functioned. I personally sat down and wrote out the functional specs to bridge the gap between our IT developers and our supply chain planners. I ran the rigorous user acceptance testing cycles, and I aggressively cleaned up our master data, taking our data completeness from 60% up to 99%.\n\nBecause I applied such a disciplined approach to that system management and data governance, we saw an 85% reduction in MRP exceptions. Honestly, I know firsthand that a complex planning system is only ever as good as the raw data you feed into it, and I take pride in making sure that foundation is rock solid."

    elif "kinaxis" in lower_q or "rapidresponse" in lower_q:
        response["intent"] = "Kinaxis / Implementation Support"
        response["answer_strategy"] = "Kinaxis -> module config + user training + go-live support"

        response["script"] = f"Yes, I have very deep experience with Kinaxis RapidResponse from my time as a Consultant at QuEST Global. I actually led two major implementations there—one for ExxonMobil across 6 plants, and another for Bombardier across 5 plants.\n\nThe core challenge in both scenarios was that their existing planning cycles were far too slow to react to supply shocks. My task was to configure the specific Kinaxis modules, integrate them with their legacy ERP systems, and provide the technical go-live support. But more importantly, I had to ensure the actual human planners knew how to use it, so I personally trained over 280 users across both organizations.\n\nThe results were massive. For ExxonMobil, we reduced their planning cycle from two weeks down to just four hours, released €12 million in working capital, and improved OTIF by 28%. So I'm extremely comfortable jumping into complex technical deployments and driving real, measurable ROI."

    elif "data" in lower_q or "tableau" in lower_q or "analytics" in lower_q:
        response["intent"] = "Data Analytics / Dashboards"
        response["answer_strategy"] = "Data analytics / KPI -> problem + dashboard built + business impact"

        response["script"] = f"I'm incredibly passionate about data analytics, and I rely on it heavily to drive my decision-making. Back when I was a Supply Chain Analyst at Nike EMEA, we were struggling with a lack of visibility across our €2 billion retail distribution network. The commercial and supply teams were operating off completely different spreadsheets, which made it impossible to accurately forecast demand.\n\nMy task was to build a single source of truth. I pulled the raw data and built a suite of complex Tableau dashboards, utilizing Level of Detail expressions to segment our inventory metrics accurately. I then rolled these dashboards out to the commercial and supply leadership, training them on how to actually read the data to make purchasing decisions.\n\nAs a direct result of giving everyone that clear, unified visibility, we were able to reduce our overall inventory holding costs by 20%. I take that same exact analytical approach into every role I step into, whether I'm building models in Tableau, Power BI, or pulling raw SQL."

    elif "interpersonal" in lower_q or "social" in lower_q or "conflict" in lower_q or "stakeholder" in lower_q:
        response["intent"] = "Interpersonal / Soft Skills"
        response["answer_strategy"] = "S&OP / cross-functional -> conflict resolution + data-driven alignment"

        response["script"] = f"That's a really important question. I firmly believe that in supply chain, your technical skills are only as valuable as your ability to communicate them. A great example of my interpersonal skills in action was during my time at Ontex. We were running a €4 billion operation across 12 global plants, but the sales, finance, and operations teams were constantly clashing because they all had completely different priorities.\n\nMy task was to facilitate a consensus S&OP process and get everyone aligned. Instead of just arguing over opinions, I used my interpersonal skills to first understand each department's pain points. I then brought them all into the same room and projected our live Power BI and Arkieva dashboards onto the screen. I acted as the neutral mediator, forcing the conversation to revolve strictly around the hard data trends rather than departmental politics.\n\nBy leading with empathy but backing it up with rigorous data, I was able to break down those silos entirely. We established a fully integrated consensus forecast, which ultimately improved our accuracy by 27% and completely transformed the culture of our weekly meetings."

    else:
        response["intent"] = "Unknown / General Behavioral"
        response["answer_strategy"] = "Behavioral STAR story -> Situation, Task, Action, Result"
        response["script"] = f"That's a really good point, and a specific example that perfectly illustrates this comes to mind from my time over at Ontex. We were facing a pretty significant cross-functional breakdown within our {role_family} team. The core situation was that different departments were using completely different sets of numbers, which was leading to constant friction and severely delayed outputs. My task was to establish a single source of truth and rebuild trust across those stakeholders.\n\nI realized the issue wasn't a lack of effort, but a complete lack of visibility. So, I took the initiative to dive deep into our raw systems and build out a centralized, automated tracking dashboard using Power BI. It took some intense, deep-focus analytical work to get the underlying logic right, but I eventually rolled it out to the leadership team, walking them through exactly how it worked so they trusted the numbers.\n\nAs a direct result, it immediately aligned everyone on the exact same real-time KPIs. We stopped arguing over whose spreadsheet was right and started actually solving problems, which significantly reduced our operational delays across the board."

    if style == "concise":
        response["script"] = "(Concise) " + response["script"]
    elif style == "detailed":
        response["script"] = "(Detailed) " + response["script"]

    return response