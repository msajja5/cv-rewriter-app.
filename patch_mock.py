import re

with open("llm_service.py", "r") as f:
    content = f.read()

# Make the mock router fallback much more intelligent with string splitting and regex-like robustness,
# so if the question accuracy is poor, it still grasps the main noun.
new_mock_logic = r'''    lower_q = question.lower()

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
        response["script"] = f"That's a really good point, and a specific example that perfectly illustrates this comes to mind. We were facing a pretty significant cross-functional breakdown within our team. The core situation was that different departments were using completely different sets of numbers, which was leading to constant friction and severely delayed outputs. My task was to establish a single source of truth and rebuild trust across those stakeholders.\n\nI realized the issue wasn't a lack of effort, but a complete lack of visibility. So, I took the initiative to dive deep into our raw systems and build out a centralized, automated tracking dashboard. It took some intense, deep-focus analytical work to get the underlying logic right, but I eventually rolled it out to the leadership team, walking them through exactly how it worked so they trusted the numbers.\n\nAs a direct result, it immediately aligned everyone on the exact same real-time KPIs. We stopped arguing over whose spreadsheet was right and started actually solving problems, which significantly reduced our operational delays across the board."'''

# Find the block and replace
start_idx = content.find("lower_q = question.lower()")
end_idx = content.find("if style == \"concise\":")

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_mock_logic + "\n\n    " + content[end_idx:]

with open("llm_service.py", "w") as f:
    f.write(content)
