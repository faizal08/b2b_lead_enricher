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
        st.info("⚙️ Background engine started. Fetching, verifying, and enriching leads...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Query Apollo / Extract Prospects (Names, Titles, Domain, LinkedIn URL)
        status_text.text("Step 1/3: Extracting prospect LinkedIn URLs from Apollo...")
        raw_prospects = fetch_apollo_leads(company_name, location, seniority_levels, max_leads)
        
        if not raw_prospects:
            st.warning("⚠️ No leads found matching the specified company/location criteria. Please refine your inputs.")
            st.stop()
            
        progress_bar.progress(33)
        
        # Step 2: Run Local Permutations & Lead Canal Phone Enrichment
        status_text.text("Step 2/3: Verifying SMTP Emails & Fetching Phone numbers via Lead Canal...")
        enriched_list = []
        for idx, prospect in enumerate(raw_prospects):
            first_name = prospect.get('first_name', '')
            last_name = prospect.get('last_name', '')
            domain = prospect.get('domain', '')
            linkedin_url = prospect.get('linkedin_url', '')

            # Run local SMTP verification against generated permutations
            email, status = verify_email_smtp(first_name, last_name, domain)
            
            # If valid SMTP match, append email. If invalid, keep email field as empty string ""
            prospect['email'] = email if status == "Valid" else ""

            # Fetch phone number from LeadCanal using LinkedIn URL (and email if valid)
            phone = fetch_phone_lead_canal(linkedin_url, prospect['email'])
            prospect['phone'] = phone

            # Retain the lead record regardless of whether an email was found
            enriched_list.append(prospect)
            
            p_val = 33 + int(((idx + 1) / len(raw_prospects)) * 34)
            progress_bar.progress(p_val)
            
        # Step 3: Excel Compilation
        status_text.text("Step 3/3: Formatting data into master Excel template...")
        file_path = build_custom_excel(enriched_list, company_name)
        progress_bar.progress(100)
        
        st.success("🎉 Extraction & Enrichment Complete!")
        
        with open(file_path, "rb") as file:
            st.download_button(
                label="📥 Download Enriched Leads Excel File",
                data=file,
                file_name=file_path,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )