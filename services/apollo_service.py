import os
import re
import time
import random
import requests
import urllib.parse
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

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

def resolve_lead_via_duckduckgo_page(page, first_name, obfuscated_last, title, company_name, domain):
    """
    Performs the search using a shared Playwright page instance with built-in retries and jitter.
    """
    query = f"{first_name} {obfuscated_last} — {title} Company: {company_name} ({domain})"
    print(f"🦆 DuckDuckGo Visual Search Query: {query}")

    # Retry loop implementing exponential backoff safety
    for attempt in range(2):
        try:
            # Human-like random jitter delay before each search execution
            if attempt > 0:
                print("🔄 Retrying search with backoff pause...")
                time.sleep(random.uniform(10.0, 15.0))
            else:
                time.sleep(random.uniform(3.0, 6.0))

            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            page.goto(search_url, timeout=25000)
            
            # Wait for results container to render
            try:
                page.wait_for_selector(".result", timeout=7000)
            except Exception:
                time.sleep(3)

            # Query all result links on the page
            links = page.query_selector_all("a.result__url, a.result__snippet, a")

            for link in links:
                href = link.get_attribute("href") or ""
                
                # Unwrap DuckDuckGo redirect link if present
                if "uddg=" in href:
                    try:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        if "uddg" in parsed:
                            href = parsed["uddg"][0]
                    except Exception:
                        pass

                if "linkedin.com/in/" in href:
                    clean_url = href.split("?")[0].rstrip("/")

                    # Extract text from surrounding title or snippet to recover the unmasked name
                    parent_result = link.evaluate_handle("node => node.closest('.result')")
                    snippet_text = parent_result.inner_text() if parent_result else ""

                    recovered_first = first_name
                    recovered_last = obfuscated_last

                    if snippet_text:
                        # Parse out name components from result block
                        raw_name = re.split(r'[\–\-\|\:\,]', snippet_text)[0].strip()
                        raw_name = re.sub(r'(?i)^linkedin\s*[\.\·\-]?\s*', '', raw_name).strip()
                        
                        parts = raw_name.split()
                        if len(parts) >= 2:
                            recovered_first = parts[0]
                            recovered_last = " ".join(parts[1:])

                    # Fallback extraction from profile slug if needed
                    if "*" in recovered_last or recovered_last == obfuscated_last:
                        if "linkedin.com/in/" in clean_url:
                            slug = clean_url.split("linkedin.com/in/")[1].split("/")[0]
                            slug_parts = [p.capitalize() for p in slug.split("-") if not p.isdigit() and len(p) > 1]
                            if len(slug_parts) >= 2:
                                recovered_first = slug_parts[0]
                                recovered_last = " ".join(slug_parts[1:])

                    print(f"✨ [DuckDuckGo Resolution Success] Unmasked Name: {recovered_first} {recovered_last}")
                    print(f"🔗 [DuckDuckGo Resolution Success] Direct LinkedIn: {clean_url}")

                    return {
                        "full_name": f"{recovered_first} {recovered_last}",
                        "first_name": recovered_first,
                        "last_name": recovered_last,
                        "linkedin_url": clean_url
                    }
            
            # If no links matched on attempt 0, break to retry once
            break

        except Exception as e:
            print(f"⚠️ [DuckDuckGo Playwright Exception on attempt {attempt+1}]: {str(e)}")

    print("⚠️ [DuckDuckGo Resolution Notice] Fallback triggered: No direct profile isolated from search results.")
    return {
        "full_name": f"{first_name} {obfuscated_last}",
        "first_name": first_name,
        "last_name": obfuscated_last,
        "linkedin_url": f"https://www.linkedin.com/pub/dir/{first_name}/{company_name}"
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
        # Added safety jitter pause before hitting the Apollo API endpoint
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
        
        # Initialize a single shared browser session for the entire batch pool
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=50)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

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

                # Execute resolution using the shared browser page instance
                print(f"🔎 Resolving profile for: {first_name} {last_name} at {company_name}...")
                resolved = resolve_lead_via_duckduckgo_page(page, first_name, last_name, title, company_name, domain)

                results.append({
                    "first_name": resolved["first_name"],
                    "last_name": resolved["last_name"],
                    "title": title if title else "Decision Maker",
                    "company": company_name,
                    "domain": domain,
                    "city": city,
                    "country": country,
                    "linkedin_url": resolved["linkedin_url"],
                    "authority_level": seniorities[0] if seniorities else "Executive"
                })

                if len(results) >= limit:
                    break

            browser.close()

        return results

    except Exception as e:
        print(f"[Apollo Service Exception] {str(e)}")
        return []