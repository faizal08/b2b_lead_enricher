import streamlit as st

# Import backend features from our modular services folder
from services.apollo_service import fetch_apollo_leads
from services.smtp_service import verify_email_smtp
from services.leadcanal_service import fetch_phone_lead_canal
from services.excel_service import build_custom_excel

# Set up Streamlit Page Configuration
st.set_page_config(
    page_title="Lead Intelligence Automation Tool",
    page_icon="⚡",
    layout="centered"
)

st.title("⚡ B2B Lead Enrichment Engine")
st.write("Enter the company filters below to automatically extract, verify, and enrich decision-maker profiles.")

# --- FRONTEND INPUT FORM ---
with st.form("lead_search_form"):
    st.subheader("Search Parameters")
    
    company_name = st.text_input("Company Name (e.g., Dubizzle, Bayut)", value="")
    location = st.text_input("Location (e.g., Saudi Arabia, Dubai, New York)", value="")
    
    seniority_levels = st.multiselect(
        "Select Decision Maker Authority Levels / Titles:",
        options=[
            "C-Suite (CEO, CTO, COO, CFO)",
            "VP / Vice President",
            "Director / Head of Department",
            "Owner / Founder",
            "General Manager / Manager"
        ],
        default=["C-Suite (CEO, CTO, COO, CFO)", "VP / Vice President", "Director / Head of Department"]
    )
    
    max_leads = st.slider("Maximum Decision Makers to Extract:", min_value=5, max_value=100, value=20)
    
    submit_button = st.form_submit_button("🚀 Start Background Extraction & Enrichment")

# --- UI EXECUTION FLOW ---
if submit_button:
    if not company_name and not location:
        st.error("Please provide at least a Company Name or Location!")
    else:
        st.info("⚙️ Background engine started. Processing pipeline across 4 execution steps...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # LOG INPUT PARAMETERS
        print("\n" + "="*80)
        print("📥 [LAYER 0: APP.PY FORM INPUT RECEIVED]")
        print("="*80)
        print(f" 🔹 Company Name    : {company_name}")
        print(f" 🔹 Location        : {location}")
        print(f" 🔹 Seniority Levels: {seniority_levels}")
        print(f" 🔹 Max Leads Limit : {max_leads}")
        print("="*80 + "\n")
        
        # =========================================================================
        # STEP 1: Query Apollo / Extract Prospects
        # =========================================================================
        status_text.text("Step 1/4: Extracting prospect LinkedIn URLs from Apollo...")
        print("➡️ [APP -> APOLLO] Requesting raw leads from Apollo Service...")
        
        raw_prospects = fetch_apollo_leads(company_name, location, seniority_levels, max_leads)
        
        print("\n" + "-"*80)
        print(f"⬅️ [LAYER 1: APOLLO -> APP TRANSITION AUDIT]")
        print(f" 📦 Total Raw Records Received: {len(raw_prospects) if raw_prospects else 0}")
        print("-"*80)
        
        if not raw_prospects:
            st.warning("⚠️ No leads found matching the specified company/location criteria. Please refine your inputs.")
            st.stop()
            
        # Log out the exact extracted fields for each raw prospect dictionary
        for i, prospect in enumerate(raw_prospects):
            print(f"  📌 Prospect [{i+1}/{len(raw_prospects)}]:")
            print(f"     • Name        : {prospect.get('first_name', '')} {prospect.get('last_name', '')}")
            print(f"     • Title       : {prospect.get('title', '')}")
            print(f"     • Company     : {prospect.get('company_name', '')}")
            print(f"     • Domain      : {prospect.get('domain', '')}")
            print(f"     • LinkedIn URL: {prospect.get('linkedin_url', '')}")
        print("-"*80 + "\n")
            
        progress_bar.progress(25)
        
        # =========================================================================
        # STEP 2: SMTP Email Permutations & Verification
        # =========================================================================
        status_text.text("Step 2/4: Verifying SMTP Email Permutations...")
        smtp_verified_prospects = []
        
        print("="*80)
        print("➡️ [LAYER 2: APP -> SMTP SERVICE TRANSITION AUDIT]")
        print("="*80)
        
        for idx, prospect in enumerate(raw_prospects):
            first_name = prospect.get('first_name', '')
            last_name = prospect.get('last_name', '')
            domain = prospect.get('domain', '')

            print(f"\n📧 --- Processing Prospect [{idx+1}/{len(raw_prospects)}]: {first_name} {last_name} ---")
            print(f"  ➡️ Sent to SMTP Engine -> First Name: '{first_name}', Last Name: '{last_name}', Domain: '{domain}'")
            
            smtp_email, status = verify_email_smtp(first_name, last_name, domain)
            verified_smtp_email = smtp_email if status == "Valid" else ""
            
            print(f"  ⬅️ Received from SMTP  -> Verified Email: '{verified_smtp_email}' | Verification Status: [{status}]")

            # Attach verified SMTP email to the prospect payload
            prospect['smtp_email'] = verified_smtp_email
            smtp_verified_prospects.append(prospect)
            
            # Progress calculation between 25% and 50%
            p_val = 25 + int(((idx + 1) / len(raw_prospects)) * 25)
            progress_bar.progress(p_val)
            
        print("\n" + "-"*80)
        print("✅ STEP 2 COMPLETE: All prospects processed through SMTP Verification.")
        print("-"*80 + "\n")

        # =========================================================================
        # STEP 3: LeadCanal Scraping (Phones & Work Emails)
        # =========================================================================
        status_text.text("Step 3/4: Fetching Phone numbers & Emails via LeadCanal...")
        enriched_list = []
        
        print("="*80)
        print("➡️ [LAYER 3: APP -> LEADCANAL SERVICE TRANSITION AUDIT]")
        print("="*80)
        
        for idx, prospect in enumerate(smtp_verified_prospects):
            first_name = prospect.get('first_name', '')
            last_name = prospect.get('last_name', '')
            linkedin_url = prospect.get('linkedin_url', '')
            verified_smtp_email = prospect.get('smtp_email', '')

            print(f"\n📞 --- Processing Prospect [{idx+1}/{len(smtp_verified_prospects)}]: {first_name} {last_name} ---")
            print(f"  ➡️ Sent to LeadCanal Engine -> LinkedIn URL: '{linkedin_url}', SMTP Email Buffer: '{verified_smtp_email}'")
            
            final_email_str, final_phone_str = fetch_phone_lead_canal(linkedin_url, verified_smtp_email)
            
            print(f"  ⬅️ Received from LeadCanal -> Merged Emails: '{final_email_str}' | Scraped Phones: '{final_phone_str}'")

            # Update dictionary payload with final enriched attributes
            prospect['email'] = final_email_str
            prospect['phone'] = final_phone_str
            
            # Remove temporary intermediate key
            prospect.pop('smtp_email', None)

            enriched_list.append(prospect)
            
            # Progress calculation between 50% and 75%
            p_val = 50 + int(((idx + 1) / len(smtp_verified_prospects)) * 25)
            progress_bar.progress(p_val)

        print("\n" + "-"*80)
        print("✅ STEP 3 COMPLETE: LeadCanal Phone & Email Enrichment Finished.")
        print("-"*80 + "\n")

        # =========================================================================
        # STEP 4: Excel File Generation & Data Verification
        # =========================================================================
        status_text.text("Step 4/4: Formatting data into master Excel template...")
        
        print("="*80)
        print("➡️ [LAYER 4: APP -> EXCEL BUILDER FULL PAYLOAD VERIFICATION]")
        print("="*80)
        print(f"📦 Total Master Records Being Sent to Excel: {len(enriched_list)}")
        print("-"*80)

        for i, lead in enumerate(enriched_list):
            print(f"  📊 Lead Record #{i+1}:")
            print(f"     • Full Name    : {lead.get('first_name', '')} {lead.get('last_name', '')}")
            print(f"     • Job Title    : {lead.get('title', '')}")
            print(f"     • Company      : {lead.get('company_name', '')}")
            print(f"     • Domain       : {lead.get('domain', '')}")
            print(f"     • LinkedIn URL : {lead.get('linkedin_url', '')}")
            print(f"     • Final Emails : {lead.get('email', '(None)')}")
            print(f"     • Final Phones : {lead.get('phone', '(None)')}")
            print("     " + "-"*60)

        file_path = build_custom_excel(enriched_list, company_name)
        
        print(f"\n⬅️ [EXCEL SERVICE RESPONSE] Master Excel File Compiled Successfully -> File Path: '{file_path}'")
        print("="*80 + "\n")
        
        progress_bar.progress(100)
        st.success("🎉 Extraction & Enrichment Complete!")
        
        with open(file_path, "rb") as file:
            st.download_button(
                label="📥 Download Enriched Leads Excel File",
                data=file,
                file_name=file_path,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )