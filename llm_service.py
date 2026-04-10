import os
import httpx
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# MANJUNATH'S EXPERIENCE KNOWLEDGE BASE — offline fallback with real STAR stories
# ═══════════════════════════════════════════════════════════════════════════════

ROLE_SUMMARIES = {
    "ontex": (
        "At Ontex (May 2022 – Jul 2025, Belgium) I was a Supply Chain Consultant leading demand and supply "
        "planning across 12 global manufacturing sites with €4B operations scope. I built 18-month rolling "
        "demand plans using Arkieva, improved forecast accuracy from ~55% to 82% (+27%), developed capacity "
        "plans aligning production with demand, automated Power BI/Tableau dashboards for OTIF, DIO and KPIs, "
        "and led NPI cross-functional readiness teams. The role ended in a company restructuring/redundancy."
    ),
    "nike": (
        "At Nike (Sep 2021 – Apr 2022, Belgium) I was a Supply Chain Analyst managing demand forecasting and "
        "supply planning for the €2B EMEA retail portfolio. I used statistical models for demand optimization, "
        "reduced distribution holding costs by 20%, built Tableau supplier KPI dashboards, and ran demand "
        "optimizer simulations for cost-to-serve and inventory placement decisions. Fixed-term contract role."
    ),
    "solvay": (
        "At Solvay (May 2021 – Aug 2021, France) I was a Master Data Planner ensuring data integrity for "
        "€150M raw material planning in SAP MRP. I managed material availability, capacity planning, demand "
        "forecasting, and resolved PO discrepancies through better supplier coordination. MSc internship at "
        "EM Normandie — 4-month fixed placement."
    ),
    "quest": (
        "At QuEST Global (Nov 2017 – Dec 2019, India) I was a Supply Chain Consultant deployed to client "
        "sites in manufacturing, oil & gas, and aerospace. I handled demand/supply planning for international "
        "FMCG/manufacturing clients, led SAP ERP implementations to enhance planning accuracy, and designed "
        "EOQ and safety stock models balancing service levels with costs. Left to pursue MSc in France."
    ),
}

# 17 STAR stories — teleprompter ready, natural spoken language
STAR_STORIES = {
    "forecast accuracy": (
        "📌 STAR — Improving Forecast Accuracy at Ontex:\n"
        "Situation: When I joined Ontex, forecast accuracy was around 55% across 12 global sites — causing overproduction, stockouts, and constant firefighting.\n"
        "Task: Own demand planning and bring accuracy to a level where Operations could trust the plan.\n"
        "Action: Restructured the forecasting process — introduced statistical baseline models in Arkieva, added consensus review cycles with Sales and Finance, and created exception-based alerts for high-variance SKUs. Built a Power BI dashboard so every site saw their accuracy trend weekly.\n"
        "Result: Went from 55% to 82% forecast accuracy (+27%) in 18 months. Stockouts dropped, overproduction costs reduced, and S&OP meetings became strategic rather than reactive."
    ),
    "inventory": (
        "📌 STAR — Reducing Holding Costs at Nike:\n"
        "Situation: At Nike EMEA, the distribution network had high holding costs due to suboptimal stock placement across nodes.\n"
        "Task: Analyse the network and recommend improvements to inventory positioning.\n"
        "Action: Built demand optimizer simulations modelling cost-to-serve across distribution scenarios, then worked with logistics to redesign stock placement — moving from central holding to regional buffers for fast movers.\n"
        "Result: Holding costs reduced by 20%, and service levels improved because stock was closer to where demand was actually happening."
    ),
    "stakeholder": (
        "📌 STAR — Cross-Functional Alignment at Ontex:\n"
        "Situation: Sales wanted higher forecasts, Finance wanted lower inventory, Operations wanted stable production plans — all conflicting.\n"
        "Task: Build one agreed 18-month rolling plan all three functions could commit to.\n"
        "Action: Structured a monthly S&OP process — pre-work with each function separately, then a joint consensus meeting with trade-offs presented visually in a dashboard.\n"
        "Result: Three competing plans became one agreed rolling plan within two cycles. Forecast accuracy improved 27% and Sales started using the plan for revenue forecasting."
    ),
    "conflict": (
        "📌 STAR — Resolving Cross-Functional Conflict at Ontex:\n"
        "Situation: Sales submitted a demand spike that Operations said was physically impossible without significant overtime costs.\n"
        "Task: Mediate and find a solution serving the customer without blowing the cost budget.\n"
        "Action: Modelled three scenarios in Arkieva — full fulfilment with overtime, partial fulfilment with backorder, and phased delivery split. Presented cost and service trade-offs to both teams with clear numbers.\n"
        "Result: Agreed on phased delivery — customer informed early, no relationship damage, saved €80K in unnecessary overtime."
    ),
    "sap": (
        "📌 STAR — SAP ERP Implementation at QuEST Global:\n"
        "Situation: A manufacturing client was running supply planning on spreadsheets — no visibility, no MRP discipline, constant firefighting.\n"
        "Task: Functional lead to implement SAP MM/PP modules and train the planning team.\n"
        "Action: Configured material master, purchasing workflows, MRP run parameters, BOM structure, and lot sizing rules. Designed EOQ and safety stock models within SAP. Built functional test cases for PO creation, MRP runs, and production order management.\n"
        "Result: After go-live, manual PO errors dropped by 60% and planning cycle time went from days to hours."
    ),
    "dashboard": (
        "📌 STAR — Automating KPI Dashboards at Ontex:\n"
        "Situation: The team spent 6-8 hours every week manually compiling OTIF, DIO, and forecast accuracy reports in Excel for the S&OP meeting.\n"
        "Task: Streamline the reporting process.\n"
        "Action: Built automated Power BI dashboards pulling live data from SAP and Arkieva — showing OTIF by site, DIO trends, forecast accuracy by product family, and supply risk flags. Set up auto-refresh and email alerts for KPI breaches.\n"
        "Result: Weekly reporting time dropped from 8 hours to under 30 minutes. S&OP meeting quality improved because data was always fresh and leaders could drill down live."
    ),
    "npi": (
        "📌 STAR — NPI Supply Chain Readiness at Ontex:\n"
        "Situation: New product launch with procurement, production, and logistics working in silos — no integrated readiness view.\n"
        "Task: Lead the supply chain workstream to ensure on-time launch.\n"
        "Action: Built a readiness tracker covering supplier qualification, material availability, production trial scheduling, and initial stock build plan. Ran weekly cross-functional syncs to surface blockers early.\n"
        "Result: Launch hit its original target date — the first NPI in two years to do so with zero supply-related delays."
    ),
    "strength": (
        "My core strength is bridging data and operations. I can take a complex supply chain problem — a forecast gap, "
        "a capacity crunch, a service failure — and translate it into a structured analysis that Sales, Finance, and "
        "Operations can all agree on. I've done this across Ontex, Nike, Solvay, and QuEST in very different environments, "
        "and the skill that travels is making trade-offs visible with data so decisions get made faster."
    ),
    "weakness": (
        "I used to go very deep into data analysis before presenting findings — which is thorough, but in a fast-moving "
        "S&OP environment it can slow decisions. I've learned to timebox analysis phases: give myself a clear deadline, "
        "present with a confidence level attached to the numbers, and flag what additional analysis would change the recommendation. "
        "It's made me much more effective in cross-functional settings."
    ),
    "pressure": (
        "📌 STAR — Managing Pressure at Ontex:\n"
        "Situation: During a key retail season, two of 12 manufacturing sites had unplanned downtime simultaneously, creating a major supply shortfall.\n"
        "Task: Contain the service impact and communicate clearly to commercial teams.\n"
        "Action: Ran a priority model in Arkieva — ranked open orders by customer tier and contractual penalties. Reallocated existing stock to protect top-tier accounts, built a phased recovery plan, and prepared a one-page summary for Sales to communicate delays proactively.\n"
        "Result: Protected top 3 accounts with zero service failures. Tier 2/3 customers received early notifications — complaint escalations reduced by 70% compared to previous disruption events."
    ),
    "failure": (
        "📌 STAR — Learning from a Forecasting Failure:\n"
        "Situation: Early at Ontex, I trusted a promotional forecast from Sales without statistical validation. We over-produced by 15% for a product with limited shelf life.\n"
        "Task: Manage excess stock and fix the process to prevent recurrence.\n"
        "Action: Absorbed the lesson, then redesigned the promotional forecasting workflow — added a mandatory statistical sanity check comparing promo uplift to historical precedent, and introduced an Operations sign-off step before any promo-driven production order was released.\n"
        "Result: In the 12 months following the change, promotional forecast accuracy improved 34% and we had zero repeat over-production events from promotional spikes."
    ),
    "achieve": (
        "One achievement I'm most proud of is the S&OP transformation at Ontex. When I joined, the monthly planning "
        "meeting was largely a blame session — teams showing up with different numbers and no agreed view. Over 18 months "
        "I rebuilt it from scratch: standardised data inputs, introduced consensus review cycles, automated KPI reporting "
        "in Power BI, and shifted the agenda from reporting the past to making decisions about the future. Forecast accuracy "
        "went from 55% to 82%, and the process became something teams actually valued rather than dreaded."
    ),
    "team": (
        "📌 STAR — Building Team Capability at Ontex:\n"
        "Situation: The planning team had strong Excel skills but no exposure to statistical forecasting or structured S&OP processes.\n"
        "Task: Upskill the team while simultaneously running live planning operations.\n"
        "Action: Ran internal training sessions on Arkieva, statistical baseline methods, and S&OP process design. Created standard operating procedures and playbooks so the knowledge wasn't dependent on me personally.\n"
        "Result: Two team members took over regional planning ownership independently within 6 months. When I left, the process continued without disruption."
    ),
    "change": (
        "📌 STAR — Managing Change Resistance at Ontex:\n"
        "Situation: When I introduced the new consensus forecasting process, some Sales managers resisted — they felt it reduced their ability to push optimistic forecasts into the plan.\n"
        "Task: Get buy-in without creating political friction.\n"
        "Action: Instead of enforcing top-down, ran a pilot with one region and showed accuracy improvement data after two cycles. Invited the resistant managers to help design the exception rules — giving them ownership.\n"
        "Result: Process adopted globally within three months. The managers who were most resistant became its strongest advocates."
    ),
    "tight deadline": (
        "📌 STAR — Delivering Under Tight Deadline at Ontex:\n"
        "Situation: The CFO requested a full inventory health report across all 12 sites within 48 hours for a board presentation.\n"
        "Task: Build a clear, accurate inventory analysis at short notice.\n"
        "Action: Prioritised the SAP data pull, built a structured Power BI dashboard overnight covering DIO by site, slow-mover flags, and excess stock value. Added a one-page executive summary with three recommended actions.\n"
        "Result: Delivered on time. The CFO used it in the board presentation and it became a monthly standing report afterwards."
    ),
    "difficult stakeholder": (
        "📌 STAR — Handling a Difficult Stakeholder at Ontex:\n"
        "Situation: A regional Sales Director consistently over-inflated forecasts to protect against potential stockouts — distorting the production plan and creating waste.\n"
        "Task: Correct the forecast without damaging the relationship.\n"
        "Action: Met privately, showed him the data on how his overages caused overproduction costs, and framed it as a shared problem. Gave him a formal safety stock buffer mechanism so he felt protected without needing to inflate the forecast.\n"
        "Result: His over-forecasting dropped 80% in the following quarter. He became one of the most collaborative partners in the S&OP process."
    ),
    "process improvement": (
        "📌 STAR — Process Automation at Ontex:\n"
        "Situation: Planning team spent 6-8 hours weekly manually compiling S&OP reports in Excel from multiple SAP exports.\n"
        "Task: Automate the reporting to free up analyst time for value-added work.\n"
        "Action: Built Power BI dashboards connecting live to SAP and Arkieva — covering OTIF, DIO, forecast accuracy, and supply risk. Scheduled refresh and KPI breach alerts.\n"
        "Result: Reporting time dropped from 8 hours to 30 minutes. Team redirected time into scenario planning and exception management."
    ),
    "tell me about yourself": (
        "I'm a supply chain professional with 7 years of experience across demand and supply planning, S&OP, "
        "inventory optimisation, and ERP systems — working at Ontex, Nike, Solvay, and QuEST Global across "
        "Belgium, France, and India.\n\n"
        "My most recent role was at Ontex as a Supply Chain Consultant, where I led planning for 12 global "
        "manufacturing sites — improving forecast accuracy by 27%, automating KPI dashboards in Power BI, and "
        "leading NPI supply readiness programmes. Before that I was at Nike in Belgium managing their €2B EMEA "
        "retail network, where I reduced holding costs by 20% through distribution network optimisation.\n\n"
        "I'm particularly strong at translating complex supply chain data into decisions that Sales, Finance, and "
        "Operations can align on — with hands-on experience in Arkieva, Kinaxis, SAP, Power BI, and Tableau.\n\n"
        "I'm based in Paris, open to relocation, and looking for a senior planning or S&OP role where I can add "
        "immediate value to a complex planning environment."
    ),
}

WHY_LEAVE = {
    "ontex": "The Ontex role ended due to a company restructuring — my position was made redundant as part of a broader reorganisation of the global planning function. It wasn't performance-related; I was actually asked to document processes before I left because the team valued the structure I'd built.",
    "nike": "Nike was a fixed-term contract role — always planned as a 6-month engagement. I was brought in specifically for an EMEA demand planning project and when the contract ended I moved on.",
    "solvay": "Solvay was my MSc internship — a structured 4-month placement as part of my degree at EM Normandie. It always had a defined end date.",
    "quest": "I left QuEST Global to pursue my MSc in Supply Chain Management in France — a deliberate investment in my education and to gain international experience in Europe.",
}

KEYWORD_MAP = [
    (["tell me about yourself", "introduce yourself", "walk me through", "about yourself"], "tell me about yourself"),
    (["forecast", "forecast accuracy", "demand planning", "demand forecast"], "forecast accuracy"),
    (["inventory", "holding cost", "stock", "stockout", "excess"], "inventory"),
    (["stakeholder", "align", "alignment", "cross-functional", "sales and finance"], "stakeholder"),
    (["conflict", "disagree", "push back", "competing priorities"], "conflict"),
    (["sap", "erp", "mrp", "module", "implementation"], "sap"),
    (["dashboard", "reporting", "kpi", "otif", "dio", "automat"], "dashboard"),
    (["npi", "new product", "launch"], "npi"),
    (["strength", "best quality", "what are you good at"], "strength"),
    (["weakness", "improve", "area of development"], "weakness"),
    (["pressure", "stressful", "tight situation", "crisis", "disruption"], "pressure"),
    (["failure", "mistake", "went wrong", "lesson"], "failure"),
    (["achievement", "proud", "biggest win", "impact", "accomplish"], "achieve"),
    (["team", "colleague", "collaborate", "mentor"], "team"),
    (["change", "resistance", "adopt", "new process"], "change"),
    (["deadline", "urgent", "last minute", "short notice"], "tight deadline"),
    (["difficult stakeholder", "difficult person", "hard to work with"], "difficult stakeholder"),
    (["process improvement", "efficiency", "reduce time"], "process improvement"),
]


def _build_messages(question: str, cv: str, job_role: str, context: list) -> list:
    system_prompt = (
        f"You are an expert AI Interview Copilot helping Manjunath Sajjan — a Senior Supply Chain professional — "
        f"answer interview questions in real-time.\n"
        f"He is applying for: '{job_role or 'a supply chain / planning role'}'.\n"
        f"Write a natural teleprompter script he can read aloud. 3-5 sentences. First-person, confident, conversational. "
        f"No bullet points. Start directly with the answer.\n"
        f"Be specific: mention tools (Arkieva, SAP, Kinaxis, Power BI, Tableau), metrics (+27% forecast accuracy, "
        f"-20% holding costs, €2B EMEA, 12 global sites), and companies (Ontex, Nike, Solvay, QuEST Global) when relevant.\n"
        f"Never say 'As an AI'. Never repeat the question. Do NOT start the answer with 'I'.\n\n"
        f"Key experience stories available:\n"
        f"- Ontex: 12 global sites, Arkieva, forecast 55→82% (+27%), Power BI automation (8h→30min), NPI leadership, S&OP redesign\n"
        f"- Nike: €2B EMEA retail, Tableau, -20% holding costs, demand optimizer simulations\n"
        f"- Solvay: €150M raw material MRP, SAP master data, supplier coordination\n"
        f"- QuEST: SAP MM/PP implementations, EOQ/safety stock models, FMCG/manufacturing clients\n\n"
        f"Candidate's CV:\n{cv or '(not provided)'}"
    )
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

    # 1. Groq (fastest — free)
    if groq_key:
        try:
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=320,
                temperature=0.65,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq failed: {e}")

    # 2. Gemini (free tier)
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
                    "generationConfig": {"maxOutputTokens": 320, "temperature": 0.65},
                },
                timeout=15,
            )
            text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            if text:
                return text
        except Exception as e:
            print(f"Gemini failed: {e}")

    # 3. OpenRouter (free Llama-3.3)
    if openrouter_key:
        try:
            res = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                json={"model": "meta-llama/llama-3.3-70b-instruct:free", "messages": messages, "max_tokens": 320, "temperature": 0.65},
                timeout=15,
            )
            text = res.json()["choices"][0]["message"]["content"]
            if text:
                return text
        except Exception as e:
            print(f"OpenRouter failed: {e}")

    # 4. Offline smart fallback — always works, no internet needed
    return _smart_hint(question, job_role)


def _smart_hint(question: str, job_role: str) -> str:
    """Returns real STAR stories or structured hints from Manjunath's actual experience."""
    q = question.lower()

    # Why did you leave — per company
    if any(x in q for x in ["why leave", "why did you leave", "why quit", "reason for leaving"]):
        for company, reason in WHY_LEAVE.items():
            if company in q:
                return f"📌 HINT — Why Leave:\n{reason}"
        return (
            "📌 HINT — Why Leave (general):\n"
            "• QuEST Global → left for higher education (MSc Supply Chain, France)\n"
            "• Solvay → MSc internship with a fixed end date\n"
            "• Nike → fixed-term contract that concluded as planned\n"
            "• Ontex → role made redundant in company restructuring (not performance-related)"
        )

    # Role summaries per company
    for company, summary in ROLE_SUMMARIES.items():
        if company in q:
            return f"📌 HINT — {company.title()} Role:\n{summary}"

    # Route to STAR stories via keyword map
    for keywords, story_key in KEYWORD_MAP:
        if any(kw in q for kw in keywords):
            story = STAR_STORIES.get(story_key)
            if story:
                return story

    # Tools & systems
    if any(x in q for x in ["tool", "system", "software", "kinaxis", "arkieva", "omp", "power bi", "tableau", "excel"]):
        return (
            "📌 HINT — Tools & Systems:\n"
            "• Arkieva: demand/supply planning at Ontex (12 global sites, 18-month rolling plans)\n"
            "• Kinaxis RapidResponse: functional consulting and supply planning\n"
            "• SAP MM/PP/MRP: ERP implementations at QuEST, master data at Solvay\n"
            "• Power BI: automated OTIF, DIO, forecast accuracy dashboards at Ontex\n"
            "• Tableau: supplier KPI dashboards at Nike EMEA\n"
            "• Excel: advanced modelling — pivot tables, solver, statistical functions\n"
            "• Python/SQL: data automation and API development (SupplyMind AI)"
        )

    # S&OP
    if any(x in q for x in ["s&op", "sales and operations", "planning process"]):
        return (
            "📌 HINT — S&OP:\n"
            "• Ran full S&OP cycles at Ontex: statistical baseline → consensus review → supply feasibility → exec decision\n"
            "• Standardised agenda, automated data inputs via Power BI\n"
            "• Shifted conversation from reporting the past to making forward trade-off decisions\n"
            "• Result: +27% forecast accuracy, cross-functional alignment across Sales/Finance/Operations"
        )

    # Motivation
    if any(x in q for x in ["motivation", "passion", "why supply chain", "why this role"]):
        return (
            "📌 HINT — Motivation:\n"
            "Supply chain sits at the intersection of data, people, and operations — every improvement "
            "has a direct, measurable impact on service levels and costs. What keeps me engaged is the complexity: "
            "no two planning problems are identical, and I enjoy building structured solutions to messy, "
            f"cross-functional challenges. This {job_role} role is a strong match for my background in "
            "demand/supply planning with tools like Arkieva, Kinaxis, SAP, and Power BI."
        )

    # Generic fallback with real numbers
    return (
        f"📌 HINT — Key points for: '{question[:55]}...':\n"
        f"• Ontex: 12 global sites, Arkieva, +27% forecast accuracy, Power BI dashboards\n"
        f"• Nike: €2B EMEA retail, Tableau, -20% holding costs, demand optimizer\n"
        f"• Solvay: €150M MRP, SAP master data, supplier coordination\n"
        f"• QuEST Global: SAP ERP implementations, EOQ/safety stock models\n"
        f"• Lead with a number → name the tool → state the outcome"
    )
