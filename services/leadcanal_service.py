import time
import random
import re
import os
from PIL import Image
import pytesseract
from playwright.sync_api import sync_playwright

# Point Tesseract-OCR to your Windows installation binary
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def solve_math_captcha(page):
    try:
        captcha_box = page.locator("div:has-text('=')").first
        if captcha_box.count() > 0:
            captcha_screenshot_path = "captcha_temp.png"
            captcha_box.screenshot(path=captcha_screenshot_path)
            
            img = Image.open(captcha_screenshot_path)
            raw_text = pytesseract.image_to_string(img, config='--psm 7')
            
            cleaned_text = re.sub(r'[^0-9\+\-\*\/]', '', raw_text)
            
            if not cleaned_text or len(cleaned_text) < 3:
                dom_text = captcha_box.inner_text()
                cleaned_text = re.sub(r'[^0-9\+\-\*\/]', '', dom_text)

            if cleaned_text:
                answer = eval(cleaned_text)
                print(f"🤖 OCR Solved Captcha: '{cleaned_text}' = {answer}")
                return str(answer)
                
    except Exception as e:
        print(f"⚠️ Automatic OCR solver encountered an issue: {e}")
        
    return None

def fetch_phone_lead_canal(linkedin_url, smtp_email=""):
    lc_email = ""
    lc_phone = ""

    if not linkedin_url:
        return smtp_email, ""

    formatted_url = linkedin_url.strip()
    formatted_url = re.sub(r'^https?://', '', formatted_url)
    formatted_url = re.sub(r'^www\.', '', formatted_url)
    formatted_url = formatted_url.rstrip('/')

    try:
        with sync_playwright() as p:
            user_data_dir = os.path.join(os.getcwd(), "playwright_profile")

            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                slow_mo=50,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--start-maximized"
                ],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900}
            )
            
            page = browser_context.new_page()

            # --- DIAGNOSTIC INSPECTOR: Log all browser console logs & network requests ---
            page.on("console", lambda msg: print(f"🌐 [Browser Console]: {msg.text}"))
            page.on("response", lambda response: print(f"📡 [API Response {response.status}]: {response.url}") if "contact" in response.url or "search" in response.url or "api" in response.url else None)

            page.goto("https://leadcanal.com/linkedin-contact-finder/", timeout=30000)
            time.sleep(2.0)

            # 1. Fill URL
            input_selector = "input[placeholder*='linkedin.com']"
            page.wait_for_selector(input_selector, timeout=10000)
            page.click(input_selector)
            time.sleep(0.3)

            print(f"✍️ Typing Cleaned LinkedIn URL: {formatted_url}")
            for char in formatted_url:
                page.type(input_selector, char, delay=random.uniform(50, 100))
                
            time.sleep(0.5)

            # 2. Captcha Solving
            print(f"\n[LeadCanal Automation] Processing URL: {formatted_url}")
            captcha_answer = solve_math_captcha(page)

            if captcha_answer:
                answer_input = page.locator("input[placeholder='?']:visible").first
                if answer_input.count() == 0:
                    answer_input = page.locator("input[type='text']:visible").last
                
                if answer_input.count() > 0:
                    answer_input.click()
                    time.sleep(0.3)
                    
                    for char in captcha_answer:
                        answer_input.type(char, delay=random.uniform(60, 120))
                    
                    print(f"✍️ Typed captcha answer '{captcha_answer}' into input box.")
                    time.sleep(0.5)
            else:
                print("⚠️ Automatic OCR couldn't resolve the captcha...")
                time.sleep(5)

            # 3. Click submit and capture network behavior
            submit_btn = page.locator("button[type='submit'].lct-btn, button:has-text('Get contact info')").first
            if submit_btn.count() > 0:
                print("🚀 Clicking 'Get contact info' button and inspecting network traffic...")
                submit_btn.click()

            # 4. Wait for results or timeout with full HTML dump
            try:
                page.wait_for_selector("text=Mobile, text=Work", timeout=20000)
                time.sleep(2.0)
                page.evaluate("window.scrollBy(0, 450)")
                time.sleep(1.0)
            except Exception as e:
                print(f"⚠️ Timeout reached. Saving full page HTML dump to 'debug_page.html'...")
                html_content = page.content()
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                page.screenshot(path="debug_timeout_screen.png")

            # 5. Extraction logic
            try:
                phone_loc = page.locator("text=Mobile").locator("xpath=..").locator("div").first
                if phone_loc.count() > 0:
                    lc_phone = phone_loc.inner_text().strip()
                    print(f"📞 Extracted Phone: {lc_phone}")
            except Exception:
                pass

            try:
                email_loc = page.locator("text=Work").locator("xpath=..").locator("div").first
                if email_loc.count() > 0:
                    lc_email = email_loc.inner_text().strip().lower()
                    print(f"📧 Extracted Email: {lc_email}")
            except Exception:
                pass

            time.sleep(5.0)  # Keep open longer so you can inspect network logs in terminal
            browser_context.close()

    except Exception as e:
        print(f"❌ Error during LeadCanal automation: {e}")

    # --- Clean strings & merging ---
    lc_email = lc_email.strip().lower()
    lc_phone = lc_phone.strip()
    smtp_email = smtp_email.strip().lower()

    final_email = ""
    if not smtp_email:
        final_email = lc_email
    elif not lc_email:
        final_email = smtp_email
    elif smtp_email == lc_email:
        final_email = smtp_email
    else:
        final_email = f"{smtp_email}, {lc_email}"

    final_phone = lc_phone if lc_phone else ""

    return final_email, final_phone