import os
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

# Check environment flag for SMTP Verification
enable_smtp = os.getenv("ENABLE_SMTP_CHECK", "false").strip().lower() == "true"

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
        total_steps = 4 if enable_smtp else 3
        st.info(f"⚙️ Background engine started. Processing pipeline across {total_steps} execution steps...")
        
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
        print(f" 🔹 SMTP Verification: {'ENABLED' if enable_smtp else 'DISABLED (Skipped)'}")
        print("="*80 + "\n")
        
        # =========================================================================
        # STEP 1: Query Apollo / Extract Prospects
        # =========================================================================
        status_text.text(f"Step 1/{total_steps}: Extracting prospect LinkedIn URLs from Apollo...")
        print("➡️ [APP -> APOLLO] Requesting raw leads from Apollo Service...")
        
        raw_prospects = fetch_apollo_leads(company_name, location, seniority_levels, max_leads)
        
        print("\n" + "-"*80)
        print("⬅️ [LAYER 1: APOLLO -> APP TRANSITION AUDIT]")
        print(f" 📦 Total Raw Records Received: {len(raw_prospects) if raw_prospects else 0}")
        print("-"*80)
        
        if not raw_prospects:
            st.warning("⚠️ No leads found matching the specified company/location criteria. Please refine your inputs.")
            st.stop()
            
        # Log out extracted raw prospects
        for i, prospect in enumerate(raw_prospects):
            print(f"  📌 Prospect [{i+1}/{len(raw_prospects)}]:")
            print(f"     • Name        : {prospect.get('first_name', '')} {prospect.get('last_name', '')}")
            print(f"     • Title       : {prospect.get('title', '')}")
            print(f"     • Company     : {prospect.get('company_name', '')}")
            print(f"     • Domain      : {prospect.get('domain', '')}")
            print(f"     • LinkedIn URL: {prospect.get('linkedin_url', '')}")
        print("-"*80 + "\n")
            
        step1_progress = 25 if enable_smtp else 33
        progress_bar.progress(step1_progress)
        
        # =========================================================================
        # STEP 2: SMTP Email Permutations & Verification (Conditional)
        # =========================================================================
        if enable_smtp:
            status_text.text(f"Step 2/{total_steps}: Verifying SMTP Email Permutations...")
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

                prospect['smtp_email'] = verified_smtp_email
                smtp_verified_prospects.append(prospect)
                
                p_val = 25 + int(((idx + 1) / len(raw_prospects)) * 25)
                progress_bar.progress(p_val)
                
            print("\n" + "-"*80)
            print("✅ STEP 2 COMPLETE: All prospects processed through SMTP Verification.")
            print("-"*80 + "\n")
        else:
            print("="*80)
            print("⏭️ [LAYER 2: SMTP SERVICE SKIPPED]")
            print("   ENABLE_SMTP_CHECK=false in .env. Skipping permutation probing to protect IP reputation.")
            print("="*80 + "\n")
            
            # Pass raw prospects forward directly with an empty smtp_email buffer
            smtp_verified_prospects = []
            for prospect in raw_prospects:
                prospect['smtp_email'] = ""
                smtp_verified_prospects.append(prospect)

        # =========================================================================
        # STEP 3: LeadCanal Scraping (Phones & Work Emails)
        # =========================================================================
        current_step_num = 3 if enable_smtp else 2
        status_text.text(f"Step {current_step_num}/{total_steps}: Fetching Phone numbers & Emails via LeadCanal...")
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

            prospect['email'] = final_email_str
            prospect['phone'] = final_phone_str
            prospect.pop('smtp_email', None)

            enriched_list.append(prospect)
            
            # Calculate dynamic progress based on step count
            if enable_smtp:
                p_val = 50 + int(((idx + 1) / len(smtp_verified_prospects)) * 25)
            else:
                p_val = 33 + int(((idx + 1) / len(smtp_verified_prospects)) * 33)
                
            progress_bar.progress(p_val)

        print("\n" + "-"*80)
        print(f"✅ STEP {current_step_num} COMPLETE: LeadCanal Phone & Email Enrichment Finished.")
        print("-"*80 + "\n")

        # =========================================================================
        # STEP 4: Excel File Generation & Data Verification
        # =========================================================================
        current_step_num = 4 if enable_smtp else 3
        status_text.text(f"Step {current_step_num}/{total_steps}: Formatting data into master Excel template...")
        
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

        file_path = build_custom_excel(enriched_list, company_name, search_location=location)
        
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