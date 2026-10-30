import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API Key
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

# Official public people search endpoint
APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"

# Map UI seniority labels to Apollo API seniority parameter keys
SENIORITY_MAP = {
    "C-Suite (CEO, CTO, COO, CFO)": "c_suite",
    "VP": "vp",
    "Director": "director",
    "Manager": "manager",
    "Individual Contributor": "individual_contributor",
    "Owner / Founder": "owner"
}


def fetch_apollo_leads(company, location, seniorities, limit=20):
    """
    Queries Apollo API using api_search without unlocking email/phone credits.
    Extracts core identity metadata (names, title, company, domain, location)
    so downstream services (smtp_service.py) can generate and verify email permutations.
    """
    domain_query = ""
    if company:
        domain_query = company.strip().lower()
        domain_query = domain_query.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    else:
        domain_query = "apple.com"

    payload = {
        "q_organization_domains": [domain_query] if domain_query else [],
        "per_page": min(limit, 50)
    }

    # Map human-readable seniorities to Apollo API string keys
    if seniorities:
        api_seniorities = []
        for s in seniorities:
            clean_key = SENIORITY_MAP.get(s, s.lower().replace(" ", "_"))
            api_seniorities.append(clean_key)
        payload["person_seniorities"] = api_seniorities

    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY
    }

    try:
        response = requests.post(APOLLO_SEARCH_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[Apollo API Error] Status Code {response.status_code}")
            print(f"Response Content: {repr(response.text)}")
            return []

        data = response.json()
        people = data.get("people", []) or data.get("contacts", [])
        
        results = []
        for person in people:
            first_name = person.get("first_name", "").strip()
            last_name = person.get("last_name", "").strip()
            title = person.get("title", "").strip()
            city = person.get("city", "").strip() or "N/A"
            country = person.get("country", "").strip() or "N/A"
            
            # Optional local location filtering
            if location and location.strip().lower() not in city.lower() and location.strip().lower() not in country.lower():
                continue

            org = person.get("organization", {}) or {}
            company_name = org.get("name") or company or "Target Corp"
            domain = org.get("primary_domain") or domain_query
            linkedin_url = person.get("linkedin_url", "").strip()
            employee_count = str(org.get("estimated_num_employees", "50-100"))

            # Save clean lead profile for SMTP permutation generation
            results.append({
                "first_name": first_name if first_name else "Unknown",
                "last_name": last_name if last_name else "Executive",
                "title": title if title else "Decision Maker",
                "company": company_name,
                "domain": domain,
                "city": city,
                "country": country,
                "linkedin_url": linkedin_url,
                "employee_count": employee_count,
                "authority_level": seniorities[0] if seniorities else "Executive"
            })

            if len(results) >= limit:
                break

        return results

    except Exception as e:
        print(f"[Apollo Service Exception] {str(e)}")
        return []