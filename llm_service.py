import os
import httpx
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

def _build_messages(question: str, cv: str, job_role: str, context: list) -> list:
    system_prompt = f"""You are an expert AI Interview Copilot helping Manjunath Sajjan — a Senior Supply Chain professional — answer interview questions in real-time.
He is applying for: '{job_role or 'a supply chain / planning role'}'.
Write a natural teleprompter script he can read aloud. 3-4 sentences. First-person, confident, conversational. No bullet points. Start directly with the answer.
Be specific: mention tools (Arkieva, SAP, Kinaxis, Power BI, Tableau), metrics (+27% forecast accuracy, -20% holding costs, \u20ac2B EMEA), and companies (Ontex, Nike, Solvay, QuEST Global) when relevant.
Never say 'As an AI'. Never repeat the question.

Candidate's CV:
{cv or '(not provided)'}"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in context[-6:]:
        messages.append({"role": "user" if msg["role"] == "interviewer" else "assistant", "content": msg["text"]})
    messages.append({"role": "user", "content": question})
    return messages


async def generate_ai_response_with_llm(question: str, cv: str, job_role: str, context: list) -> str:
    groq_key       = os.getenv("GROQ_API_KEY", "")
    gemini_key     = os.getenv("GEMINI_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

    messages = _build_messages(question, cv, job_role, context)

    # 1. Try Groq (fastest — free)
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

    # 2. Try Gemini (free tier)
    if gemini_key:
        try:
            contents = [m for m in messages if m["role"] != "system"]
            gemini_messages = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                for m in contents
            ]
            system_text = next((m["content"] for m in messages if m["role"] == "system"), "")
            res = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}",
                json={
                    "system_instruction": {"parts": [{"text": system_text}]},
                    "contents": gemini_messages,
                    "generationConfig": {"maxOutputTokens": 300, "temperature": 0.7}
                },
                timeout=15
            )
            text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            if text:
                return text
        except Exception as e:
            print(f"Gemini failed: {e}")

    # 3. Try OpenRouter (free Llama-3.3)
    if openrouter_key:
        try:
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

    # 4. Offline smart hint (always works — no internet needed)
    return _smart_hint(question, job_role)


def _smart_hint(question: str, job_role: str) -> str:
    """Returns structured bullet hints based on CV knowledge. Used when all APIs are offline."""
    q = question.lower()

    # — Introduction / Tell me about yourself
    if any(x in q for x in ["tell me about", "introduce yourself", "about yourself", "walk me through", "background"]):
        return (
            "\U0001f4cc HINT — Introduction:\n"
            "\u2022 5+ years supply chain: Ontex (Belgium), Nike (Belgium), Solvay (France), QuEST Global (India)\n"
            "\u2022 Core: demand forecasting, supply planning, S&OP, capacity planning\n"
            "\u2022 Tools: Arkieva, SAP, Kinaxis, Power BI, Tableau\n"
            "\u2022 MSc Supply Chain — EM Normandie, France (2020-21)\n"
            "\u2022 Key win: +27% forecast accuracy at Ontex across 12 global sites"
        )

    # — Supply chain / planning experience
    if any(x in q for x in ["supply chain", "s&op", "planning", "demand", "supply"]):
        return (
            "\U0001f4cc HINT — Supply Chain / Planning:\n"
            "\u2022 Ontex: Led demand+supply planning, 12 global sites, Arkieva tool\n"
            "\u2022 Created 18-month rolling plans with Sales/Finance/Operations alignment\n"
            "\u2022 Nike: \u20ac2B EMEA retail demand forecasting using statistical models\n"
            "\u2022 Solvay: \u20ac150M raw material MRP, material availability, capacity planning\n"
            "\u2022 Result: +27% forecast accuracy (Ontex), -20% holding costs (Nike)"
        )

    # — Forecasting
    if any(x in q for x in ["forecast", "accuracy", "statistical", "prediction"]):
        return (
            "\U0001f4cc HINT — Forecasting:\n"
            "\u2022 Ontex: +27% forecast accuracy improvement using Arkieva\n"
            "\u2022 Nike: Statistical demand forecasting for \u20ac2B EMEA retail network\n"
            "\u2022 QuEST Global: Designed EOQ + safety stock models for FMCG clients\n"
            "\u2022 Approach: data-driven models + cross-functional alignment (Sales, Ops, Finance)"
        )

    # — SAP / ERP / tools
    if any(x in q for x in ["sap", "erp", "kinaxis", "arkieva", "omp", "tool", "system", "software"]):
        return (
            "\U0001f4cc HINT — Tools & Systems:\n"
            "\u2022 Arkieva: demand/supply planning at Ontex (12 global sites)\n"
            "\u2022 SAP ERP: implementations at QuEST Global for FMCG/manufacturing clients\n"
            "\u2022 Kinaxis RapidResponse: functional consulting experience\n"
            "\u2022 Power BI + Tableau: OTIF, DIO, supplier KPI dashboards\n"
            "\u2022 Solvay: MRP data integrity for \u20ac150M raw material planning"
        )

    # — KPIs / dashboards / analytics
    if any(x in q for x in ["kpi", "dashboard", "analytics", "data", "metric", "report", "tableau", "power bi"]):
        return (
            "\U0001f4cc HINT — KPIs & Analytics:\n"
            "\u2022 Ontex: Automated Power BI/Tableau dashboards — OTIF, DIO, supply KPIs\n"
            "\u2022 Nike: Tableau supplier KPI dashboards + demand optimizer simulations\n"
            "\u2022 Metrics owned: OTIF, DIO, forecast accuracy, cost-to-serve, inventory turns\n"
            "\u2022 Impact: -20% holding costs (Nike EMEA), +27% forecast accuracy (Ontex)"
        )

    # — NPI / new product launch
    if any(x in q for x in ["npi", "new product", "launch", "introduction"]):
        return (
            "\U0001f4cc HINT — NPI & Product Launch:\n"
            "\u2022 Ontex: Led NPI teams for supply chain readiness across new product launches\n"
            "\u2022 Cross-functional coordination: R&D, procurement, production, logistics\n"
            "\u2022 Ensured material availability and capacity alignment before launch dates"
        )

    # — Stakeholder management / collaboration
    if any(x in q for x in ["stakeholder", "collaborat", "team", "cross-functional", "communicate", "align"]):
        return (
            "\U0001f4cc HINT — Stakeholders & Collaboration:\n"
            "\u2022 Ontex: Daily alignment with Sales, Finance, Operations across 12 sites\n"
            "\u2022 Led S&OP meetings — bridging demand signals with production capacity\n"
            "\u2022 Nike: Coordinated with EMEA retail partners and distribution teams\n"
            "\u2022 Solvay: Supplier coordination to resolve PO discrepancies (€150M spend)"
        )

    # — Challenge / problem / difficult situation
    if any(x in q for x in ["challenge", "difficult", "problem", "obstacle", "failure", "mistake"]):
        return (
            "\U0001f4cc HINT — Challenge (STAR):\n"
            "\u2022 Situation: Post-COVID demand volatility, 12 Ontex sites globally\n"
            "\u2022 Task: Rebuild S&OP process to restore planning accuracy\n"
            "\u2022 Action: Rebuilt 18-month rolling plan in Arkieva, aligned Sales/Finance/Ops\n"
            "\u2022 Result: +27% forecast accuracy, better OTIF and DIO performance"
        )

    # — Achievement / proud / accomplishment
    if any(x in q for x in ["achiev", "proud", "accomplish", "success", "impact", "result"]):
        return (
            "\U0001f4cc HINT — Achievements:\n"
            "\u2022 Ontex: +27% forecast accuracy across 12 global sites\n"
            "\u2022 Nike: -20% holding costs across \u20ac2B EMEA retail network\n"
            "\u2022 Automated KPI dashboards eliminating manual reporting hours\n"
            "\u2022 Solvay: Improved data integrity for \u20ac150M raw material MRP"
        )

    # — Leadership / management
    if any(x in q for x in ["lead", "manag", "mentor", "junior", "team lead"]):
        return (
            "\U0001f4cc HINT — Leadership:\n"
            "\u2022 Ontex: Led cross-site NPI supply chain readiness teams\n"
            "\u2022 Coordinated capacity plans with production managers across 12 sites\n"
            "\u2022 QuEST Global: Led demand/supply planning projects for multiple FMCG clients"
        )

    # — Weakness / development area
    if any(x in q for x in ["weakness", "improve", "develop", "area of growth"]):
        return (
            "\U0001f4cc HINT — Weakness (frame positively):\n"
            "\u2022 Mention: deepening technical Python/ML skills for advanced forecasting\n"
            "\u2022 Action taken: building SupplyMind AI — ESG + supply chain data product\n"
            "\u2022 Show awareness + proactive improvement — not a blocker to the role"
        )

    # — Why this company / role
    if any(x in q for x in ["why", "motivation", "interest", "choose", "join"]):
        return (
            "\U0001f4cc HINT — Why this role:\n"
            "\u2022 Strong fit: 5+ years demand/supply planning in FMCG + manufacturing\n"
            "\u2022 Tools match: SAP, Arkieva, Kinaxis, Power BI exactly align\n"
            "\u2022 Impact-driven: proven +27% accuracy, -20% cost track record\n"
            f"\u2022 Excited about applying this in {job_role} context"
        )

    # — Salary / compensation
    if any(x in q for x in ["salary", "compensation", "expect", "package", "pay"]):
        return (
            "\U0001f4cc HINT — Salary:\n"
            "\u2022 Research market rate for this role/location first\n"
            "\u2022 Frame: based on my 5+ years and measurable impact, I\'m targeting [X range]\n"
            "\u2022 Add: open to discuss full package including benefits"
        )

    # — Relocation / availability
    if any(x in q for x in ["relocat", "availab", "start", "notice", "when"]):
        return (
            "\U0001f4cc HINT — Availability:\n"
            "\u2022 Open for relocation (currently Paris)\n"
            "\u2022 No visa sponsorship needed (EU)\n"
            "\u2022 Notice period: confirm current status"
        )

    # — Default generic hint
    return (
        f"\U0001f4cc HINT — Key points for '{question[:60]}...':\n"
        f"\u2022 Ontex: 12 global sites, Arkieva, +27% forecast accuracy\n"
        f"\u2022 Nike: \u20ac2B EMEA, Tableau, -20% holding costs\n"
        f"\u2022 Solvay: \u20ac150M MRP, data integrity\n"
        f"\u2022 QuEST Global: SAP ERP, EOQ/safety stock models\n"
        f"\u2022 Skills: demand planning, S&OP, capacity planning, Power BI, SAP"
    )
