from services.apollo_service import fetch_apollo_leads

print("🔍 Testing Apollo Service (Metadata-Only / Credit Saver)...")

# Test with a target domain
test_company = "apple.com"
leads = fetch_apollo_leads(
    company=test_company, 
    location="", 
    seniorities=["C-Suite (CEO, CTO, COO, CFO)"], 
    limit=5
)

if leads:
    print(f"\n✅ Success! Fetched {len(leads)} decision-maker profiles (0 credits used):\n")
    for idx, lead in enumerate(leads, 1):
        print(f"{idx}. {lead['first_name']} {lead['last_name']} — {lead['title']}")
        print(f"   Company: {lead['company']} ({lead['domain']})")
        print(f"   Location: {lead['city']}, {lead['country']}")
        print(f"   LinkedIn: {lead['linkedin_url']}")
        
        # Display sample email permutations generated for SMTP testing
        fn = lead['first_name'].lower()
        ln = lead['last_name'].lower()
        dom = lead['domain']
        print(f"   Generated SMTP Targets: {fn}.{ln}@{dom}, {fn}@{dom}, {fn[0] if fn else ''}{ln}@{dom}\n")
else:
    print("\n⚠️ No leads returned or an error occurred. Check your terminal output above for API error details.")