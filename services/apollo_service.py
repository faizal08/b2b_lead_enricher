import os
import re
import time
import random
import requests
import urllib.parse
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"

SENIORITY_MAP = {
    "C-Suite (CEO, CTO, COO, CFO)": "c_suite",
    "VP": "vp",
    "Director": "director",
    "Manager": "manager",
    "Individual Contributor": "individual_contributor",
    "Owner / Founder": "owner"
}

def clean_extracted_name(raw_name):
    """
    Strips out trailing job titles, company noise, and LinkedIn tags from raw result headers.
    """
    if not raw_name:
        return ""
    
    # Remove leading 'LinkedIn' or similar tags
    name = re.sub(r'(?i)^linkedin\s*[\.\·\-]?\s*', '', raw_name).strip()
    
    # Split on common separators used in result titles (-, |, :, —, etc.)
    name_parts = re.split(r'[\–\-\|\:\,]', name)
    first_part = name_parts[0].strip()
    
    # Remove any stray profile numbers or hash IDs (e.g., 1a868110)
    first_part = re.sub(r'\b[a-f0-9]{6,}\b', '', first_part, flags=re.IGNORECASE).strip()
    
    return first_part

def parse_name_from_slug(clean_url):
    """
    Extracts and sanitizes a name from a LinkedIn profile slug, stripping hex IDs/hashes.
    """
    if "linkedin.com/in/" not in clean_url:
        return "", ""
    
    slug = clean_url.split("linkedin.com/in/")[1].split("/")[0]
    # Remove trailing hashes/alphanumeric IDs commonly added by LinkedIn
    slug_clean = re.sub(r'-[a-f0-9]{6,}$', '', slug, flags=re.IGNORECASE)
    slug_clean = re.sub(r'[\-\.]', ' ', slug_clean)
    
    parts = [p.capitalize() for p in slug_clean.split() if not p.isdigit() and len(p) > 1]
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    return "", ""

def resolve_lead_via_duckduckgo_package(first_name, obfuscated_last, title, company_name, domain):
    """
    Resolves LinkedIn URLs and unmasks obfuscated last names using a multi-layered extraction system.
    """
    query = f"{first_name} {obfuscated_last} — {title} Company: {company_name} ({domain})"
    print(f"🦆 DuckDuckGo Search Query: {query}")

    clean_last_stub = obfuscated_last.replace("*", "").strip()
    recovered_first = first_name
    recovered_last = clean_last_stub if clean_last_stub else "Executive"
    
    fallback_url = f"https://www.linkedin.com/search/results/all/?keywords={urllib.parse.quote(f'{first_name} {company_name}')}"
    clean_url = fallback_url

    for attempt in range(2):
        try:
            if attempt > 0:
                print("🔄 Retrying search with backoff pause...")
                time.sleep(random.uniform(3.0, 5.0))
            else:
                time.sleep(random.uniform(1.0, 2.0))

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=8))
                
                for r in results:
                    href = r.get("href", "")
                    title_text = r.get("title", "")
                    body_text = r.get("body", "")

                    if "linkedin.com/in/" in href:
                        clean_url = href.split("?")[0].rstrip("/")

                        # STAGE 1: Try extracting clean full name from the result Title header
                        extracted_name_str = clean_extracted_name(title_text or body_text)
                        parts = extracted_name_str.split()

                        if len(parts) >= 2 and len(parts[0]) <= 15 and len(parts[1]) <= 20:
                            recovered_first = parts[0]
                            recovered_last = " ".join(parts[1:])
                        else:
                            # STAGE 2: Fallback to sanitized LinkedIn slug parsing
                            slug_first, slug_last = parse_name_from_slug(clean_url)
                            if slug_first and slug_last:
                                recovered_first = slug_first
                                recovered_last = slug_last
                            else:
                                recovered_first = first_name
                                recovered_last = clean_last_stub

                        print(f"✨ [DuckDuckGo Resolution Success] Unmasked Name: {recovered_first} {recovered_last}")
                        print(f"🔗 [DuckDuckGo Resolution Success] Direct LinkedIn: {clean_url}")

                        return {
                            "full_name": f"{recovered_first} {recovered_last}",
                            "first_name": recovered_first,
                            "last_name": recovered_last,
                            "linkedin_url": clean_url
                        }
            break

        except Exception as e:
            print(f"⚠️ [DuckDuckGo Package Exception on attempt {attempt+1}]: {str(e)}")

    print("⚠️ [DuckDuckGo Resolution Notice] Fallback triggered: Using generated profile target.")
    return {
        "full_name": f"{first_name} {clean_last_stub}",
        "first_name": first_name,
        "last_name": clean_last_stub,
        "linkedin_url": fallback_url
    }

def fetch_apollo_leads(company, location, seniorities, limit=20):
    domain_query = ""
    if company:
        domain_query = company.strip().lower()
        domain_query = domain_query.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    else:
        domain_query = "apple.com"

    payload = {
        "q_organization_domains_list": [domain_query] if domain_query else ["apple.com"],
        "per_page": min(limit, 50)
    }

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

    params = {
        "api_key": APOLLO_API_KEY
    }

    try:
        time.sleep(random.uniform(1.0, 2.0))
        print(f"🔍 Sending request to Apollo API for domain: {domain_query}...")
        response = requests.post(APOLLO_SEARCH_URL, params=params, json=payload, headers=headers, timeout=20)
        
        print(f"📡 Apollo Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Response Content: {repr(response.text)}")
            return []

        data = response.json()
        people = data.get("people", []) or data.get("contacts", []) or data.get("accounts", [])
        
        results = []

        for person in people:
            first_name = person.get("first_name", "").strip()
            
            last_name = person.get("last_name", "").strip()
            if not last_name:
                raw_obf = person.get("last_name_obfuscated", "").strip()
                last_name = raw_obf if raw_obf else "Executive"
            
            title = person.get("title", "").strip()
            
            org = person.get("organization", {}) or {}
            city = person.get("city", "").strip() or org.get("city", "").strip() or "N/A"
            country = person.get("country", "").strip() or org.get("country", "").strip() or "N/A"
            
            company_name = org.get("name") or company or "Target Corp"
            domain = org.get("primary_domain") or domain_query

            print(f"🔎 Resolving profile for: {first_name} {last_name} at {company_name}...")
            resolved = resolve_lead_via_duckduckgo_package(first_name, last_name, title, company_name, domain)

            results.append({
                "first_name": resolved["first_name"],
                "last_name": resolved["last_name"],
                "title": title if title else "Decision Maker",
                "company_name": company_name,
                "domain": domain,
                "city": city,
                "country": country,
                "linkedin_url": resolved["linkedin_url"],
                "authority_level": seniorities[0] if seniorities else "Executive"
            })

            if len(results) >= limit:
                break

        return results

    except Exception as e:
        print(f"[Apollo Service Exception] {str(e)}")
        return []