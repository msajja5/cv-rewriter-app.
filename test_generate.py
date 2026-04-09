from playwright.sync_api import sync_playwright

def test_generate():
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

        page.locator("#interviewer-transcript").fill("Tell me about yourself.")

        print("clicking generate...")
        page.locator("#generate-btn").click()
        page.wait_for_timeout(3000)

        print("Errors recorded:")
        for err in errors:
            print(err)

        box_text = page.locator("#ai-script").inner_text()
        print("AI Script box text:", box_text)

        browser.close()

if __name__ == "__main__":
    test_generate()
