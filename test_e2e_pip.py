import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            permissions=["microphone"]
        )
        page = await context.new_page()

        errors = []
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type} {msg.text}"))
        page.on("pageerror", lambda err: errors.append(err.message))

        await page.goto("http://localhost:5000/")

        # Test PiP button (using inline overlay as fallback)
        print("Clicking float button...")
        await page.click("#float-btn")

        # We simulate what a user might do if they skip setup section and go straight to PiP mode.
        # This will test if `window.sessionKeys` logic breaks the fetch.

        # Evaluate to show the hidden interview interface without running the setup step
        await page.evaluate('document.getElementById("interview-section").style.display = "block"')

        # Enter some transcript and generate to verify it doesn't crash
        await page.fill("#interviewer-transcript", "Hello, tell me about your supply chain experience.")
        print("Clicking generate...")
        await page.click("#generate-btn")

        # Wait a bit to let it fail if it fails
        await page.wait_for_timeout(2000)

        # Output the inner text of aiScriptBox
        ai_script = await page.evaluate('document.getElementById("ai-script").innerText')
        print("AI Script output:")
        print(ai_script)

        if errors:
            print("ERRORS CAUGHT:", errors)
        else:
            print("NO ERRORS CAUGHT!")

        await browser.close()

asyncio.run(main())
