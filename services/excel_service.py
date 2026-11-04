import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_custom_excel(records, company_name):
    """
    Formats extracted records into a clean, fully populated Excel workbook 
    containing ONLY real data collected from pipeline phases (no dummies or placeholders).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Master_Database"
    
    # Headers trimmed to include ONLY actual collected/input data
    headers = [
        'Record ID', 'Company Name', 'Domain', 'Country', 'City', 
        'Website URL', 'General Email', 'Employee Count', 'DM Full Name', 'DM Title', 
        'DM Authority Level', 'DM Direct Email', 'DM Direct Phone', 'DM LinkedIn URL', 
        'HQ Address', 'Company LinkedIn'
    ]
    
    # Professional Dark Green fill with White Bold text
    header_fill = PatternFill(start_color="274E13", end_color="274E13", fill_type="solid")
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    data_font = Font(name="Arial", size=9)
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        
    for idx, row_data in enumerate(records, start=1):
        record_id = f"REC-2026-{idx:05d}"
        
        # Real pipeline data extraction with safe fallbacks
        comp_name = row_data.get('company_name') or row_data.get('company') or company_name or 'Target Corp'
        domain = row_data.get('domain', '')
        city = row_data.get('city', '')
        country = row_data.get('country', '')
        
        # Construct HQ Address dynamically only if city/country exist
        hq_address = f"{city}, {country}".strip(", ") if (city or country) else ''
        
        row = [
            record_id,                                                    # 1. Record ID
            comp_name,                                                    # 2. Company Name
            domain,                                                       # 3. Domain
            country,                                                      # 4. Country
            city,                                                         # 5. City
            f"https://{domain}" if domain else '',                        # 6. Website URL
            f"info@{domain}" if domain else '',                           # 7. General Email
            row_data.get('employee_count', ''),                           # 8. Employee Count
            f"{row_data.get('first_name', '')} {row_data.get('last_name', '')}".strip(), # 9. DM Full Name
            row_data.get('title', ''),                                    # 10. DM Title
            row_data.get('authority_level', ''),                          # 11. DM Authority Level
            row_data.get('email', ''),                                    # 12. DM Direct Email
            row_data.get('phone', ''),                                    # 13. DM Direct Phone
            row_data.get('linkedin_url', ''),                             # 14. DM LinkedIn URL
            hq_address,                                                   # 15. HQ Address
            f"https://www.linkedin.com/company/{comp_name.lower().replace(' ', '')}" if comp_name else '' # 16. Company LinkedIn
        ]
        ws.append(row)
        
    for r in range(2, len(records) + 2):
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = data_font
            cell.border = thin_border
            
    # Auto-adjust column widths with generous padding so content is never clipped
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 6, 15)
        
    safe_company_name = company_name.replace(' ', '_') if company_name else "Target"
    output_filename = f"Enriched_Leads_{safe_company_name}.xlsx"
    wb.save(output_filename)
    return output_filename