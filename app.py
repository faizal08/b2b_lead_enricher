import os
import streamlit as st

# Import backend features from our modular services folder
from services.apollo_service import fetch_apollo_leads
from services.smtp_service import verify_email_smtp
from services.leadcanal_service import fetch_phone_lead_canal
from services.excel_service import build_custom_excel
from services.company_search_service import fetch_companies_by_criteria

# Cache company discovery results so Apollo isn't re-queried on multiselect interactions
@st.cache_data(show_spinner=False)
def get_cached_companies(industry_keyword, country_name):
    return fetch_companies_by_criteria(industry_keyword, country_name)

# Set up Streamlit Page Configuration
st.set_page_config(
    page_title="Lead Intelligence Automation Tool",
    page_icon="⚡",
    layout="centered"
)

st.title("⚡ B2B Lead Enrichment Engine")
st.write("Extract, verify, and enrich decision-maker profiles across target companies.")

# Check environment flag for SMTP Verification
enable_smtp = os.getenv("ENABLE_SMTP_CHECK", "false").strip().lower() == "true"

# --- SEARCH MODE SELECTION ---
search_mode = st.radio(
    "Choose Target Mode:",
    ["🏢 Search by Industry & Country Discovery", "🎯 Direct Single Company Input"],
    horizontal=True
)

st.markdown("---")

# Industry keyword mapping for Apollo Organization Search
INDUSTRY_KEYWORD_MAP = {
    "Construction & Engineering": "construction",
    "Real Estate & Property Development": "real estate",
    "Software Development & IT": "software",
    "Oil, Gas & Energy": "oil and energy",
    "Logistics & Supply Chain": "logistics",
    "Financial Services & Banking": "financial services",
    "Healthcare & Pharmaceuticals": "pharmaceuticals",
    "Manufacturing & Industrial": "manufacturing"
}

COUNTRY_OPTIONS = ["India", "Saudi Arabia", "United Arab Emirates", "United States", "United Kingdom", "Qatar", "Kuwait"]

discovered_companies_map = {}
target_companies = []
location = "India"

# =========================================================================
# DYNAMIC DISCOVERY SECTION (CACHED TO PREVENT RELOADS ON MULTISELECT)
# =========================================================================
if search_mode == "🏢 Search by Industry & Country Discovery":
    col1, col2 = st.columns(2)
    
    with col1:
        selected_industry = st.selectbox("1. Select Industry / Sector:", options=list(INDUSTRY_KEYWORD_MAP.keys()))
    with col2:
        selected_country = st.selectbox("2. Select Target Country:", options=COUNTRY_OPTIONS)
        
    location = selected_country
    industry_query_keyword = INDUSTRY_KEYWORD_MAP[selected_industry]
    
    # Fetch matching companies (uses cached result unless industry or country changes)
    discovered_companies = get_cached_companies(industry_query_keyword, selected_country)
    
    if discovered_companies:
        company_options = [c["name"] for c in discovered_companies]
        discovered_companies_map = {c["name"]: c.get("domain", "") for c in discovered_companies}
    else:
        company_options = []
        
    selected_companies = st.multiselect(
        "3. Select Target Companies Discovered in this Market:",
        options=company_options,
        default=[],
        placeholder="Choose target company/companies from dropdown...",
        help="Choose one or multiple companies to extract decision-makers from."
    )
    target_companies = [c for c in selected_companies if c]

else:
    # Manual single company input mode
    company_name_input = st.text_input("Company Name / Domain (e.g., techmahindra.com, flipkart.com):", value="")
    location = st.text_input("Location (e.g., India, Saudi Arabia, Dubai):", value="India")
    target_companies = [company_name_input.strip()] if company_name_input.strip() else []

st.markdown("---")

# =========================================================================
# EXTRACTION SETTINGS FORM
# =========================================================================
with st.form("lead_search_form"):
    st.subheader("Extraction Settings")
    
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
    
    max_leads_per_company = st.slider("Maximum Decision Makers to Extract per Company:", min_value=1, max_value=50, value=5)
    
    submit_button = st.form_submit_button("🚀 Start Multi-Company Extraction & Enrichment")

# =========================================================================
# UI EXECUTION FLOW
# =========================================================================
if submit_button:
    if not target_companies:
        st.error("Please select or enter at least one target company!")
    else:
        total_steps = 4 if enable_smtp else 3
        st.info(f"⚙️ Background engine started. Processing batch across {len(target_companies)} companies ({total_steps} execution steps per company)...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # LOG INPUT PARAMETERS
        print("\n" + "="*80)
        print("📥 [LAYER 0: APP.PY FORM INPUT RECEIVED]")
        print("="*80)
        print(f" 🔹 Search Mode     : {search_mode}")
        print(f" 🔹 Target Companies: {target_companies}")
        print(f" 🔹 Location        : {location}")
        print(f" 🔹 Seniority Levels: {seniority_levels}")
        print(f" 🔹 Max Leads/Co    : {max_leads_per_company}")
        print(f" 🔹 SMTP Check      : {'ENABLED' if enable_smtp else 'DISABLED (Skipped)'}")
        print("="*80 + "\n")
        
        master_all_enriched_leads = []
        total_companies_count = len(target_companies)

        for comp_idx, comp_identifier in enumerate(target_companies, start=1):
            target_domain_or_name = discovered_companies_map.get(comp_identifier, comp_identifier)
            
            st.markdown(f"### 🏢 Processing Company [{comp_idx}/{total_companies_count}]: **{comp_identifier}**")
            
            # =========================================================================
            # STEP 1: Query Apollo / Extract Prospects
            # =========================================================================
            status_text.text(f"[{comp_identifier}] Step 1/{total_steps}: Extracting prospect LinkedIn URLs from Apollo...")
            print(f"➡️ [APP -> APOLLO] Requesting raw leads for '{comp_identifier}' ({target_domain_or_name})...")
            
            raw_prospects = fetch_apollo_leads(target_domain_or_name, location, seniority_levels, max_leads_per_company)
            
            print("\n" + "-"*80)
            print("⬅️ [LAYER 1: APOLLO -> APP TRANSITION AUDIT]")
            print(f" 📦 Total Raw Records Received for {comp_identifier}: {len(raw_prospects) if raw_prospects else 0}")
            print("-"*80)
            
            if not raw_prospects:
                st.warning(f"⚠️ No leads found for '{comp_identifier}'. Skipping to next target.")
                continue
                
            for i, prospect in enumerate(raw_prospects):
                print(f"  📌 Prospect [{i+1}/{len(raw_prospects)}]:")
                print(f"     • Name        : {prospect.get('first_name', '')} {prospect.get('last_name', '')}")
                print(f"     • Title       : {prospect.get('title', '')}")
                print(f"     • Company     : {prospect.get('company_name', '')}")
                print(f"     • Domain      : {prospect.get('domain', '')}")
                print(f"     • LinkedIn URL: {prospect.get('linkedin_url', '')}")
            print("-"*80 + "\n")
            
            # =========================================================================
            # STEP 2: SMTP Email Permutations & Verification (Conditional)
            # =========================================================================
            if enable_smtp:
                status_text.text(f"[{comp_identifier}] Step 2/{total_steps}: Verifying SMTP Email Permutations...")
                smtp_verified_prospects = []
                
                print("="*80)
                print("➡️ [LAYER 2: APP -> SMTP SERVICE TRANSITION AUDIT]")
                print("="*80)
                
                for idx, prospect in enumerate(raw_prospects):
                    first_name = prospect.get('first_name', '')
                    last_name = prospect.get('last_name', '')
                    domain = prospect.get('domain', '')

                    print(f"\n📧 --- Processing Prospect [{idx+1}/{len(raw_prospects)}]: {first_name} {last_name} ---")
                    
                    smtp_email, status = verify_email_smtp(first_name, last_name, domain)
                    verified_smtp_email = smtp_email if status == "Valid" else ""
                    
                    print(f"  ⬅️ Received from SMTP  -> Verified Email: '{verified_smtp_email}' | Status: [{status}]")

                    prospect['smtp_email'] = verified_smtp_email
                    smtp_verified_prospects.append(prospect)
                    
            else:
                print("="*80)
                print("⏭️ [LAYER 2: SMTP SERVICE SKIPPED]")
                print("   ENABLE_SMTP_CHECK=false in .env. Skipping permutation probing to protect IP reputation.")
                print("="*80 + "\n")
                
                smtp_verified_prospects = []
                for prospect in raw_prospects:
                    prospect['smtp_email'] = ""
                    smtp_verified_prospects.append(prospect)

            # =========================================================================
            # STEP 3: LeadCanal Scraping (Phones & Work Emails)
            # =========================================================================
            current_step_num = 3 if enable_smtp else 2
            status_text.text(f"[{comp_identifier}] Step {current_step_num}/{total_steps}: Fetching Phone numbers & Emails via LeadCanal...")
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
                
                final_email_str, final_phone_str = fetch_phone_lead_canal(linkedin_url, verified_smtp_email)
                
                print(f"  ⬅️ Received from LeadCanal -> Merged Emails: '{final_email_str}' | Scraped Phones: '{final_phone_str}'")

                prospect['email'] = final_email_str
                prospect['phone'] = final_phone_str
                prospect.pop('smtp_email', None)

                enriched_list.append(prospect)

            master_all_enriched_leads.extend(enriched_list)
            
            # Update batch progress bar
            batch_p_val = int((comp_idx / total_companies_count) * 90)
            progress_bar.progress(batch_p_val)

        # =========================================================================
        # STEP 4: Excel File Generation & Master Batch Export
        # =========================================================================
        if master_all_enriched_leads:
            current_step_num = 4 if enable_smtp else 3
            status_text.text(f"Step {current_step_num}/{total_steps}: Formatting master batch into Excel template...")
            
            print("="*80)
            print("➡️ [LAYER 4: APP -> EXCEL BUILDER FULL PAYLOAD VERIFICATION]")
            print("="*80)
            print(f"📦 Total Master Records Being Sent to Excel: {len(master_all_enriched_leads)}")
            print("-"*80)

            batch_title = target_companies[0] if len(target_companies) == 1 else f"Batch_{location}"
            file_path = build_custom_excel(master_all_enriched_leads, batch_title, search_location=location)
            
            print(f"\n⬅️ [EXCEL SERVICE RESPONSE] Master Excel File Compiled Successfully -> File Path: '{file_path}'")
            print("="*80 + "\n")
            
            progress_bar.progress(100)
            st.success(f"🎉 Extraction & Enrichment Complete! Total Enriched Leads: {len(master_all_enriched_leads)}")
            
            with open(file_path, "rb") as file:
                st.download_button(
                    label="📥 Download Master Enriched Leads Excel File",
                    data=file,
                    file_name=file_path,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error("❌ No enriched leads could be extracted for any of the selected companies.")