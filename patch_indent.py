with open("llm_service.py", "r") as f:
    lines = f.readlines()

out = []
for line in lines:
    if 'lower_q = question.lower()' in line:
        out.append('    lower_q = question.lower()\n')
    elif 'if "company" in lower_q' in line:
        out.append('    if "company" in lower_q or "know about us" in lower_q or "why us" in lower_q:\n')
    else:
        out.append(line)

with open("llm_service.py", "w") as f:
    f.writelines(out)
