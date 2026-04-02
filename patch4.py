import re

with open("llm_service.py", "r") as f:
    content = f.read()

# Make sure job_role and cv are properly used in the system prompt.
new_prompt = r"""    # 1. Identity & Framing
    system_prompt = "You are a candidate speaking in a live job interview. You read answers directly on screen. Write EXACTLY what the candidate would say — in their voice, grounded in their real career history.\n\n"

    # 2. Target role context
    system_prompt += f"ROLE BEING INTERVIEWED FOR (INCLUDING TARGET COMPANY): {job_role}\n\n"

    # 3. Question-type routing
    intent = detect_question_routing(question)
    system_prompt += f"QUESTION TYPE DETECTED: {intent}\n\n"

    # 4. Full Candidate Profile (CV)
    system_prompt += f"CANDIDATE CV / PROFILE:\n{cv}\n\n"

    # 5. Answer format rules
    system_prompt += '''RULES:
- ALWAYS prioritize information from the provided CANDIDATE CV over any internal generic knowledge.
- If the interviewer asks "what do you know about this company" or similar, use the TARGET COMPANY from the ROLE context.
- Natural spoken English.
- STAR structure woven invisibly.
- 3-4 paragraphs, blank line between each.
- Use conversational connectors: "So,", "Basically,", "What I did was,", "Honestly,", "At the end of the day."
- NEVER start with: "Certainly", "Great question", "Absolutely", "Sure".
- First person ("I") only. Max 2-3 sentences per paragraph.
- ONLY return the raw spoken script. Do not output INTENT or CV_FACTS tags, just the script directly.'''
"""

content = re.sub(
    r'    # 1\. Identity & Framing.*?system_prompt \+= """RULES:.*?just the script directly\."""\n',
    new_prompt,
    content,
    flags=re.DOTALL
)

with open("llm_service.py", "w") as f:
    f.write(content)
