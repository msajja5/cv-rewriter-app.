import json

with open('vercel.json', 'r') as f:
    data = json.load(f)

# Change the build to target main:app
data['builds'] = [
    {
        "src": "main.py",
        "use": "@vercel/python"
    }
]

data['routes'] = [
    {
        "src": "/(.*)",
        "dest": "main.py"
    }
]

with open('vercel.json', 'w') as f:
    json.dump(data, f, indent=4)
