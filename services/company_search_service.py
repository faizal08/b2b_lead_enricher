import os
import requests
from dotenv import load_dotenv

load_dotenv()
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

def fetch_companies_by_criteria(industry_keyword, country_name):
    """
    Queries Apollo Organization Search API dynamically using robust text matching 
    for industries and locations without consuming credits.
    """
    url = "https://api.apollo.io/api/v1/mixed_companies/search"
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY
    }
    
    # Properly format payload parameters for Apollo's organization search engine
    payload = {
        "q_organization_keyword_tags": [industry_keyword],
        "organization_locations": [country_name],
        "page": 1,
        "per_page": 50
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"📡 [Apollo Org Search Response Code]: {response.status_code} for Industry: '{industry_keyword}' | Country: '{country_name}'")
        
        if response.status_code == 200:
            data = response.json()
            organizations = data.get("organizations", [])
            
            # Fallback if strict keyword tags return empty: try general query matching
            if not organizations:
                payload["q_organization_name"] = industry_keyword
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                if response.status_code == 200:
                    organizations = response.json().get("organizations", [])

            company_list = []
            for org in organizations:
                name = org.get("name")
                domain = org.get("primary_domain") or org.get("website_url")
                loc = org.get("country") or ""
                
                if name:
                    company_list.append({
                        "name": name,
                        "domain": domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/") if domain else "",
                        "country": loc
                    })
            return company_list
        else:
            print(f"⚠️ Apollo Organization Search Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error connecting to Apollo Organization Search: {e}")
        return []