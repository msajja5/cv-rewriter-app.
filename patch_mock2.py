with open("llm_service.py", "r") as f:
    lines = f.readlines()

out = []
for line in lines:
    if 'lower_q = question.lower()' in line:
        out.append('    response = {}\n')
        out.append(line)
    else:
        out.append(line)

with open("llm_service.py", "w") as f:
    f.writelines(out)
