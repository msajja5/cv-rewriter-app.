import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            permissions=["microphone"]
        )
        page = await context.new_page()

        errors = []
        page.on("console", lambda msg: print(f"CONSOLE: {msg.type} {msg.text}"))
        page.on("pageerror", lambda err: errors.append(err.message))

        await page.goto("http://localhost:5000/")

        # Click float overlay
        await page.click("#float-btn")
        await page.wait_for_timeout(1000)

        # Simulate AI stream
        print("Starting stream simulation")
        await page.evaluate("""
            window.ctrl = new AbortController();
            window.sse = new EventSource('/stream');
            window.sse.onmessage = function(e) {
                console.log("SSE msg:", e.data);
            };
            window.sse.onerror = function(e) {
                console.log("SSE error");
            };
        """)

        await page.wait_for_timeout(3000)

        if errors:
            print("PAGE ERRORS:", errors)

        await browser.close()

asyncio.run(main())
