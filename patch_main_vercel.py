with open('main.py', 'r') as f:
    content = f.read()

# Try renaming `app` to `application` or creating an alias, sometimes Vercel python requires it depending on the version
# Wait, Vercel builder `@vercel/python` usually looks for `app` variable in `main.py`. The error says it couldn't find it.
# Let's ensure the file parses successfully and there are no syntax errors.

# Let's verify syntax
import ast
try:
    ast.parse(content)
    print("Syntax is OK")
except SyntaxError as e:
    print(f"Syntax error! {e}")
