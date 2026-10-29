import time
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def fetch_apollo_leads(company, location, seniorities, limit):
    """
    Simulates or calls Apollo API / Backend fetch for Decision Makers.
    Extracts First Name, Last Name, Title, Domain, LinkedIn URL, etc.
    """
    # Replace this block with your actual Apollo API endpoints if using paid API keys
    # Endpoint: https://api.apollo.io/v1/mixed_people/search
    
    results = []
    for i in range(1, limit + 1):
        results.append({
            "first_name": f"Lead_{i}",
            "last_name": "Executive",
            "title": "Director of Operations",
            "company": company if company else "Target Corp",
            "domain": "targetcorp.com",
            "city": location if location else "Riyadh",
            "country": "Saudi Arabia",
            "linkedin_url": f"http://www.linkedin.com/in/lead-executive-{i}",
            "employee_count": "50-100",
            "authority_level": "VP / Director"
        })
    return results

def verify_email_smtp(first_name, last_name, domain):
    """
    Placeholder for your local SMTP permutation verifier.
    """
    email_candidate = f"{first_name.lower()}.{last_name.lower()}@{domain}"
    # In live usage, import/call your actual SMTP verification logic here
    return email_candidate, "Valid"

def fetch_phone_lead_canal(linkedin_url, email):
    """
    Sends the LinkedIn URL or verified email to Lead Canal API in the background.
    """
    # API Integration Example:
    # response = requests.post("https://api.leadcanal.com/v1/enrich", json={"linkedin_url": linkedin_url, "email": email})
    time.sleep(0.2)  # Jitter delay
    return "+966 50 123 4567"

def build_custom_excel(records, company_name):
    """
    Formats the extracted records into an Excel workbook matching the Master_Database template.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Master_Database"
    
    headers = [
        'Record id', 'Company Name', 'Company type', 'Primary Industry', 'Country', 'City', 
        'Primary phone', 'Whatsapp number', 'Website URL', 'General Email', 'Employee count', 
        'DM Full name', 'DM Title', 'DM Authority Level', 'DM Direct Email', 'DM Direct phone', 
        'DM Linkedin URL', 'HQ Address', 'Company Linkedin'
    ]
    
    # Style definitions
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    data_font = Font(name="Arial", size=9)
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    # Write Headers
    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        
    # Write Rows
    for idx, row_data in enumerate(records, start=1):
        record_id = f"REC-2026-{idx:05d}"
        row = [
            record_id,
            row_data.get('company', ''),
            'Private Corporate Entity',
            'Technology / Real Estate',
            row_data.get('country', ''),
            row_data.get('city', ''),
            '',  # Primary phone
            '',  # Whatsapp
            f"https://{row_data.get('domain', '')}",
            f"info@{row_data.get('domain', '')}",
            row_data.get('employee_count', ''),
            f"{row_data.get('first_name', '')} {row_data.get('last_name', '')}",
            row_data.get('title', ''),
            row_data.get('authority_level', ''),
            row_data.get('email', ''),
            row_data.get('phone', ''),
            row_data.get('linkedin_url', ''),
            f"{row_data.get('city', '')}, {row_data.get('country', '')}",
            f"https://www.linkedin.com/company/{row_data.get('company', '').lower().replace(' ', '')}"
        ]
        ws.append(row)
        
    # Apply cell borders & styling
    for r in range(2, len(records) + 2):
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = data_font
            cell.border = thin_border
            
    # Autofit column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    safe_company_name = company_name.replace(' ', '_') if company_name else "Target"
    output_filename = f"Enriched_Leads_{safe_company_name}.xlsx"
    wb.save(output_filename)
    return output_filename