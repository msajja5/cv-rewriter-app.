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
    r'elif "company" in lower_q or "know about us" in lower_q:.*?response\["script"\] = f".*?"',
    r'elif "company" in lower_q or "know about us" in lower_q:\n        response["intent"] = "Company Knowledge / Fit"\n        response["answer_strategy"] = "Company research -> align values with profile"\n        response["script"] = f"That\'s a great question. Based on the job description for {job_role}, I know you are looking for someone who can drive efficiency and build strong cross-functional relationships. My background as outlined in my CV aligns perfectly with this, as I have a proven track record of reducing operational delays and improving forecast accuracy. I am very impressed by your company\'s recent growth and focus on innovation, and I am excited about the opportunity to bring my analytical approach to your team."',
    mock_body,
    flags=re.DOTALL
)

content = content[:mock_func_start] + new_mock_body + content[mock_func_end:]

with open("llm_service.py", "w") as f:
    f.write(content)
