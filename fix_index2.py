with open('templates/index.html', 'r') as f:
    content = f.read()

# Let's ensure userStyle and targetRoleFamily are handled properly if setup is skipped
content = content.replace(
    "                response_style: userStyle,",
    "                response_style: typeof userStyle !== 'undefined' ? userStyle : 'normal',"
)
content = content.replace(
    "                target_role_family: targetRoleFamily",
    "                target_role_family: typeof targetRoleFamily !== 'undefined' ? targetRoleFamily : 'Auto Detect'"
)

with open('templates/index.html', 'w') as f:
    f.write(content)
