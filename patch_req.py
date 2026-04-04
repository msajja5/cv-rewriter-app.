import os

with open("requirements.txt", "r") as f:
    content = f.read()

if "aiohttp" not in content:
    with open("requirements.txt", "a") as f:
        f.write("\naiohttp")

if "httpx" not in content:
    with open("requirements.txt", "a") as f:
        f.write("\nhttpx")
