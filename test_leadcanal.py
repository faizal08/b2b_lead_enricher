import sys
import os

# Ensure the services directory is discoverable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.leadcanal_service import fetch_phone_lead_canal

def run_leadcanal_test():
    print("==================================================")
    print("🔍 Testing LeadCanal Service Isolation (Playwright + OCR)")
    print("==================================================\n")

    # Sample test parameters
    test_linkedin_url = "https://www.linkedin.com/in/rafiq-ahamed"
    
    # Test Scenario: Simulating a dummy SMTP email to test email comparison & merging logic
    # (Change this to test different merging paths: matching email, differing email, or empty string "")
    test_smtp_email = "rafiq@eitworks.com"

    print(f"Target LinkedIn URL : {test_linkedin_url}")
    print(f"Incoming SMTP Email : '{test_smtp_email}'")
    print("Launching browser automation and attempting automated OCR captcha solving...\n")

    # Call the LeadCanal service function
    final_email, final_phone = fetch_phone_lead_canal(test_linkedin_url, test_smtp_email)

    print("\n==================================================")
    print("✅ LeadCanal Service Test Results:")
    print("==================================================")
    print(f" 🔹 Final Merged Email(s) : {final_email}")
    print(f" 🔹 Extracted Phone Number: {final_phone if final_phone else '(No phone found / Left blank)'}")
    print("==================================================")

if __name__ == "__main__":
    run_leadcanal_test()