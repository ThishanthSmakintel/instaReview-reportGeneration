import asyncio
import os
from dotenv import load_dotenv
from logger import setup_logger
from fetch_companies_dynamodb import get_all_companies
from fetch_customer_data import process_customer_data
from create_pdf_report import generate_pdf

# Load environment variables
load_dotenv()

# Setup logging only if not already configured
if not hasattr(setup_logger, '_configured'):
    logger, _ = setup_logger()
    setup_logger._configured = True
else:
    import logging
    logger = logging.getLogger(__name__)

async def main():
    """Generate reports for all companies"""
    logger.info("Starting report generation for all companies...")
    
    # Step 1: Get all company IDs
    companies = get_all_companies()
    if not companies:
        logger.error("No companies found in DynamoDB")
        return
    
    logger.info(f"Found {len(companies)} companies to process")
    
    success_count = 0
    
    # Step 2: Process each company
    for i, company in enumerate(companies, 1):
        company_id = company.get('id')
        company_name = company.get('companyName', 'Unknown')
        
        if not company_id:
            logger.warning(f"Skipping company with no ID: {company_name}")
            continue
        
        print(f"Processing {i}/{len(companies)}: {company_name} ({company_id})")
        logger.info(f"Processing company: {company_name} ({company_id})")
        
        # Step 3: Set company ID and process data
        os.environ['COMPANY_ID'] = company_id
        
        try:
            # Check if data is available
            filtered_data = process_customer_data()
            
            if not filtered_data:
                print(f"⚠ No data available for {company_name} - skipping")
                logger.warning(f"No data available for {company_name}")
                continue
            
            # Step 4: Create PDF report
            pdf_path = await generate_pdf()
            success_count += 1
            
            print(f"✓ Report generated and uploaded for {company_name}")
            logger.info(f"Report generated successfully for {company_name}: {pdf_path}")
            
        except Exception as e:
            print(f"✗ Error processing {company_name}: {e}")
            logger.error(f"Error processing {company_name}: {e}")
    
    print(f"\nCompleted: {success_count}/{len(companies)} reports generated successfully")
    logger.info(f"Report generation completed: {success_count}/{len(companies)} successful")

if __name__ == "__main__":
    asyncio.run(main())