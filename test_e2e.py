from playwright.sync_api import sync_playwright

def test_e2e():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000")
        page.wait_for_timeout(1000)

        errors = []
        page.on("pageerror", lambda err: errors.append("PAGEERROR: " + err.message))
        page.on("console", lambda msg: errors.append("CONSOLE " + msg.type + ": " + msg.text) if msg.type == "error" else None)

        page.locator("#job-role").fill("Software Engineer")
        page.locator("#start-interview-btn").click()
        page.wait_for_timeout(1000)

        print("Clicking float btn...")
        page.evaluate("document.getElementById('float-btn').click()")
        page.wait_for_timeout(1000)

        overlay_mode = page.evaluate("overlayMode")
        print("Overlay mode:", overlay_mode)

        page.locator("#interviewer-transcript").fill("How are you doing?")
        page.locator("#generate-btn").click()
        page.wait_for_timeout(3000)

        print("ai script:")
        print(page.locator("#ai-script").inner_text())

        print("Errors:")
        for err in errors:
            print(err)

        browser.close()

if __name__ == "__main__":
    test_e2e()
