with open('main.py', 'r') as f:
    content = f.read()

# Let's add `application = app` just to be safe
content = content.replace("app = FastAPI()", "app = FastAPI()\napplication = app\nhandler = app")

with open('main.py', 'w') as f:
    f.write(content)
