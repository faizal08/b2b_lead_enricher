import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_custom_excel(records, company_name, search_location=""):
    """
    Formats extracted records into a clean, fully populated Excel workbook 
    containing ONLY real data collected from pipeline phases.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Master_Database"
    
    # Custom ordered & renamed headers matching exact user pipeline specifications
    headers = [
        'Record ID', 
        'Lead Full Name', 
        'Company Name', 
        'Job Title', 
        'Direct Email', 
        'Contact Number', 
        'LinkedIn URL', 
        'Company LinkedIn URL', 
        'Country', 
        'Website URL'
    ]
    
    # Styling Configuration
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
    
    # Write Headers
    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        
    # Write Data Rows
    for idx, row_data in enumerate(records, start=1):
        record_id = f"REC-2026-{idx:05d}"
        
        comp_name = row_data.get('company_name') or row_data.get('company') or company_name or 'Target Corp'
        domain = row_data.get('domain', '')
        
        # --- FIXED COUNTRY RESOLUTION ---
        # Extract raw country strings and ignore dummy values like 'N/A' or empty strings
        raw_country = (
            row_data.get('country') or 
            row_data.get('person_country') or 
            row_data.get('organization_country') or 
            ''
        ).strip()
        
        # If raw_country is missing or equal to 'N/A', fall back to search_location
        if not raw_country or raw_country.upper() == 'N/A':
            country = search_location.strip().title() if search_location else 'N/A'
        else:
            country = raw_country.title()
        
        row = [
            record_id,                                                                     # 1. Record ID
            f"{row_data.get('first_name', '')} {row_data.get('last_name', '')}".strip(),  # 2. Lead Full Name
            comp_name,                                                                     # 3. Company Name
            row_data.get('title', ''),                                                     # 4. Job Title
            row_data.get('email', ''),                                                     # 5. Direct Email
            row_data.get('phone', ''),                                                     # 6. Contact Number
            row_data.get('linkedin_url', ''),                                              # 7. LinkedIn URL
            f"https://www.linkedin.com/company/{comp_name.lower().replace(' ', '')}" if comp_name else '', # 8. Company LinkedIn URL
            country,                                                                       # 9. Country
            f"https://{domain}" if domain else ''                                          # 10. Website URL
        ]
        ws.append(row)
        
    # Apply cell data fonts and borders
    for r in range(2, len(records) + 2):
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = data_font
            cell.border = thin_border
            
    # Auto-adjust column widths with padding so content is clean and legible
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 6, 15)
        
    safe_company_name = company_name.replace(' ', '_') if company_name else "Target"
    output_filename = f"Enriched_Leads_{safe_company_name}.xlsx"
    wb.save(output_filename)
    return output_filename