import os
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from logger import setup_logger
from fetch_companies_dynamodb import get_all_companies
from fetch_customer_data import fetch_company_details, process_customer_data
from create_pdf_report import generate_pdf, upload_to_s3
from send_email import send_reports_for_companies

# Load environment variables
load_dotenv()

# Setup logging
logger, timestamp = setup_logger()

async def process_company_report(company_id):
    """Process report for a single company"""
    try:
        # Set company ID for this process
        os.environ['COMPANY_ID'] = company_id
        
        logger.info(f"Processing company: {company_id}")
        
        # Check if company has data
        filtered_data = process_customer_data()
        if not filtered_data or len(filtered_data) == 0:
            logger.info(f"No data found for company {company_id}, skipping report generation")
            return None, None
        
        logger.info(f"Found {len(filtered_data)} records for company {company_id}")
        
        # Generate PDF report
        from create_pdf_report import generate_pdf
        pdf_path = await generate_pdf()
        
        if not pdf_path or not os.path.exists(pdf_path):
            logger.error(f"Failed to generate PDF for company {company_id}")
            return None, None
        
        # Upload to S3
        week_num = datetime.now().isocalendar()[1]
        s3_key = f"instareview-reports/{company_id}/w{week_num}.pdf"
        
        if upload_to_s3(pdf_path, company_id, week_num):
            logger.info(f"Report uploaded to S3 for company {company_id}")
            return company_id, s3_key
        else:
            logger.error(f"Failed to upload report to S3 for company {company_id}")
            return None, None
            
    except Exception as e:
        logger.error(f"Error processing company {company_id}: {e}")
        return None, None

async def main():
    """Main function to process all companies"""
    try:
        logger.info("Starting batch report generation for all companies")
        
        # Get all companies from DynamoDB
        companies = get_all_companies()
        if not companies:
            logger.error("No companies found in DynamoDB")
            return
        
        logger.info(f"Found {len(companies)} companies to process")
        
        # Process each company
        companies_with_reports = []
        
        for company in companies:
            company_id = company.get('id')
            if not company_id:
                logger.warning("Company missing ID, skipping")
                continue
            
            # Check if company has email
            company_email = company.get('email')
            if not company_email:
                logger.warning(f"Company {company_id} has no email, will skip email sending")
            
            # Process report
            processed_id, s3_key = await process_company_report(company_id)
            
            if processed_id and s3_key:
                companies_with_reports.append((company, s3_key))
                logger.info(f"Successfully processed report for {company_id}")
            else:
                logger.info(f"Skipped report for {company_id} (no data or error)")
        
        # Send emails for companies with reports
        if companies_with_reports:
            logger.info(f"Sending emails for {len(companies_with_reports)} companies with reports")
            success_count, total_count = send_reports_for_companies(companies_with_reports)
            logger.info(f"Email sending completed: {success_count}/{total_count} emails sent")
        else:
            logger.info("No companies had data for reports, no emails sent")
        
        logger.info("Batch report generation completed successfully")
        
    except Exception as e:
        logger.error(f"Batch report generation failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())