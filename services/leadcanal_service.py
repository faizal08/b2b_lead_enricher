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
            # Add a natural human pause before taking screenshot/solving
            time.sleep(random.uniform(0.8, 1.5))
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
    lc_emails_list = []
    lc_phones_list = []

    if not linkedin_url:
        return smtp_email, ""

    formatted_url = linkedin_url.strip()
    formatted_url = re.sub(r'^https?://', '', formatted_url)
    formatted_url = re.sub(r'^www\.', '', formatted_url)
    formatted_url = formatted_url.rstrip('/')

    try:
        with sync_playwright() as p:
            user_data_dir = os.path.join(os.getcwd(), "playwright_profile")
            print(f"🔗 Launching stealth browser context using profile: {user_data_dir}")

            # Enhanced launch arguments to completely mask automation fingerprinting
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                slow_mo=random.randint(60, 110),  # Randomized slow_mo to mimic human movement variance
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--start-maximized",
                    "--disable-extensions",
                    "--disable-popup-blocking"
                ],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900}
            )
            
            page = browser_context.new_page()

            # --- ADVANCED STEALTH INJECTION PATCHES ---
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page.add_init_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            page.add_init_script("""
                window.chrome = {
                    runtime: {}
                };
            """)

            # Diagnostic network logging
            page.on("response", lambda response: print(f"📡 [API Response {response.status}]: {response.url}") if "contact" in response.url or "search" in response.url or "api" in response.url else None)

            page.goto("https://leadcanal.com/linkedin-contact-finder/", timeout=30000)
            
            # ANTI-BOT SAFEGUARD: Randomized jitter pause after page load
            time.sleep(random.uniform(3.0, 5.0))

            # 1. Fill URL using human-like typing cadence
            input_selector = "input[placeholder*='linkedin.com']"
            page.wait_for_selector(input_selector, timeout=10000)
            
            page.click(input_selector)
            time.sleep(random.uniform(0.4, 0.9))
            
            page.type(input_selector, formatted_url, delay=random.randint(45, 95))
            print(f"✍️ Filled Cleaned LinkedIn URL with human cadence: {formatted_url}")
            time.sleep(random.uniform(1.2, 2.0))

            # 2. Captcha Solving with Tesseract OCR
            print(f"\n[LeadCanal Automation] Processing URL: {formatted_url}")
            captcha_answer = solve_math_captcha(page)

            if captcha_answer:
                answer_input = page.locator("input[placeholder='?']:visible").first
                if answer_input.count() == 0:
                    answer_input = page.locator("input[type='text']:visible").last
                
                if answer_input.count() > 0:
                    answer_input.click()
                    time.sleep(random.uniform(0.3, 0.7))
                    answer_input.type(captcha_answer, delay=random.randint(60, 120))
                    print(f"✍️ Filled captcha answer '{captcha_answer}' into input box.")
                    time.sleep(random.uniform(1.0, 1.8))
            else:
                print("⚠️ Automatic OCR couldn't resolve the captcha...")
                time.sleep(5)

            # 3. Click submit
            submit_btn = page.locator("button[type='submit'].lct-btn, button:has-text('Get contact info')").first
            if submit_btn.count() > 0:
                print("🚀 Clicking 'Get contact info' button...")
                time.sleep(random.uniform(0.5, 1.2))
                submit_btn.click()

            # 4. Wait for results, scroll into view, and parse data
            try:
                page.wait_for_selector(".lct-kvs, .lct-empty, p.lct-empty", timeout=25000)
                time.sleep(3.0)  # Generous buffer for background API data return
                
                # Scroll down so the results card is fully visible in the viewport
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1.5)

                # --- PRECISION AGGREGATION FROM INSPECTED DOM ---
                # Extract all unique phone numbers from tel links
                phone_elements = page.locator("a[href^='tel:']").all()
                for p_el in phone_elements:
                    p_text = p_el.inner_text().strip()
                    if p_text and p_text not in lc_phones_list:
                        lc_phones_list.append(p_text)
                
                if lc_phones_list:
                    print(f"📞 Extracted All Phones Found: {lc_phones_list}")

                # Extract all unique valid emails from result containers
                email_elements = page.locator(".lct-point-val").all()
                for e_el in email_elements:
                    e_text = e_el.inner_text().strip().lower()
                    if "@" in e_text and "get a quote" not in e_text and "contact us" not in e_text:
                        if e_text not in lc_emails_list:
                            lc_emails_list.append(e_text)

                if lc_emails_list:
                    print(f"📧 Extracted All Emails Found: {lc_emails_list}")

            except Exception as e:
                print(f"⚠️ Timeout or extraction error: {e}")
                html_content = page.content()
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                page.screenshot(path="debug_timeout_screen.png")

            print("\n🔍 [Inspection Hold] Keeping browser open for 15 seconds to review results...")
            time.sleep(15)
            browser_context.close()

    except Exception as e:
        print(f"❌ Error during LeadCanal automation: {e}")

    # --- Comprehensive Cleaning, Matching & Merging Logic ---
    smtp_email = smtp_email.strip().lower()

    # Build the final merged unique email list starting with SMTP email if provided
    final_emails_list = []
    if smtp_email:
        final_emails_list.append(smtp_email)

    # Append scraped LeadCanal emails if they are not already in the list (deduplication)
    for email in lc_emails_list:
        if email not in final_emails_list:
            final_emails_list.append(email)

    final_email_str = ", ".join(final_emails_list)
    final_phone_str = ", ".join(lc_phones_list)

    return final_email_str, final_phone_str