import re

with open("llm_service.py", "r") as f:
    content = f.read()

# Update the mock response router to use cv and job_role instead of hardcoded strings
mock_func_start = content.find("def _mock_response(")
mock_func_end = content.find("def", mock_func_start + 1)
if mock_func_end == -1:
    mock_func_end = len(content)

mock_body = content[mock_func_start:mock_func_end]

# Modify the "what do you know about this company" prompt
new_mock_body = re.sub(
    r'def _mock_response\(question: str, role_family: str = "Supply Chain", style: str = "normal"\) -> Dict\[str, str\]:',
    r'def _mock_response(question: str, job_role: str, cv: str, role_family: str = "Supply Chain", style: str = "normal") -> Dict[str, str]:',
    mock_body
)

# Replace the first `if "company" in lower_q` to handle the new case.
# Note: it looks like it didn't exist before, or was overwritten. Let's add it before `elif "forecast" in lower_q`.
new_mock_body = re.sub(
    r'(    if "forecast" in lower_q or "demand" in lower_q or "s&op" in lower_q:)',
    r'''    if "company" in lower_q or "know about us" in lower_q:
        response["intent"] = "Company Knowledge / Fit"
        response["answer_strategy"] = "Company research -> align values with profile"
        response["script"] = f"That's a great question. Based on the job description for {job_role}, I know you are looking for someone who can drive efficiency and build strong cross-functional relationships. My background as outlined in my CV aligns perfectly with this, as I have a proven track record of reducing operational delays and improving forecast accuracy. I am very impressed by your company's recent growth and focus on innovation, and I am excited about the opportunity to bring my analytical approach to your team."

    elif "forecast" in lower_q or "demand" in lower_q or "s&op" in lower_q:''',
    new_mock_body
)


content = content[:mock_func_start] + new_mock_body + content[mock_func_end:]

# Update the call to _mock_response
content = re.sub(
    r'_mock_response\(question=question, role_family=resolved_role_family, style=response_style\)',
    r'_mock_response(question=question, job_role=job_role, cv=cv, role_family=resolved_role_family, style=response_style)',
    content
)

with open("llm_service.py", "w") as f:
    f.write(content)
