import asyncio
import os
from dotenv import load_dotenv
from fetch_companies_dynamodb import get_all_companies
from fetch_customer_data import process_customer_data
from create_pdf_report import generate_pdf

# Load environment variables
load_dotenv()

async def main():
    """Generate reports for all companies"""
    print("Starting report generation for all companies...")
    
    # Step 1: Get all company IDs
    companies = get_all_companies()
    if not companies:
        print("No companies found in DynamoDB")
        return
    
    print(f"Found {len(companies)} companies to process")
    
    success_count = 0
    
    # Step 2: Process each company
    for i, company in enumerate(companies, 1):
        company_id = company.get('id')
        company_name = company.get('companyName', 'Unknown')
        
        if not company_id:
            print(f"Skipping company with no ID: {company_name}")
            continue
        
        print(f"Processing {i}/{len(companies)}: {company_name} ({company_id})")
        
        # Step 3: Set company ID and process data
        os.environ['COMPANY_ID'] = company_id
        
        try:
            # Check if data is available
            filtered_data = process_customer_data()
            
            if not filtered_data:
                print(f"⚠ No data available for {company_name} - skipping")
                continue
            
            # Step 4: Create PDF report
            pdf_path = await generate_pdf()
            success_count += 1
            
            print(f"✓ Report generated and uploaded for {company_name}")
            
        except Exception as e:
            print(f"✗ Error processing {company_name}: {e}")
    
    print(f"\nCompleted: {success_count}/{len(companies)} reports generated successfully")

if __name__ == "__main__":
    asyncio.run(main())