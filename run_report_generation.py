import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from create_pdf_report import generate_pdf
from fetch_companies_dynamodb import get_all_companies

async def generate_report_for_company(company_id):
    """Generate report for a specific company"""
    os.environ['COMPANY_ID'] = company_id
    return await generate_pdf()

async def main():
    """Generate reports for all companies"""
    print("Starting customer feedback report generation for all companies...")
    
    companies = get_all_companies()
    if not companies:
        print("No companies found in DynamoDB")
        return
    
    success_count = 0
    total_companies = len(companies)
    
    for company in companies:
        company_id = company.get('id')
        company_name = company.get('companyName', 'Unknown')
        
        if not company_id:
            print(f"Skipping company with no ID: {company_name}")
            continue
            
        print(f"Generating report for {company_name} ({company_id})...")
        
        try:
            await generate_report_for_company(company_id)
            success_count += 1
            print(f"✓ Report generated for {company_name}")
        except Exception as e:
            print(f"✗ Error generating report for {company_name}: {e}")
    
    print(f"\nCompleted: {success_count}/{total_companies} reports generated successfully")

if __name__ == "__main__":
    asyncio.run(main())