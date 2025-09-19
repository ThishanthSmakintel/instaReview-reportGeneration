import boto3
import os
import json
from dotenv import load_dotenv
from logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
logger, _ = setup_logger()

def get_all_companies():
    """Fetch all company details from DynamoDB"""
    try:
        session = boto3.Session(profile_name=os.getenv('AWS_PROFILE', 'default'))
        dynamodb = session.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
        
        table_name = os.getenv('DYNAMODB_COMPANIES_TABLE', 'companies')
        table = dynamodb.Table(table_name)
        
        response = table.scan()
        companies = response['Items']
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            companies.extend(response['Items'])
        
        logger.info(f"Retrieved {len(companies)} companies from DynamoDB")
        return companies
        
    except Exception as e:
        logger.error(f"Failed to fetch companies from DynamoDB: {e}")
        return []

def get_company_by_id(company_id):
    """Fetch specific company by ID from DynamoDB"""
    try:
        session = boto3.Session(profile_name=os.getenv('AWS_PROFILE', 'default'))
        dynamodb = session.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
        
        table_name = os.getenv('DYNAMODB_COMPANIES_TABLE', 'companies')
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'id': company_id})
        
        if 'Item' in response:
            logger.info(f"Retrieved company details for {company_id}")
            return response['Item']
        else:
            logger.warning(f"Company {company_id} not found in DynamoDB")
            return None
            
    except Exception as e:
        logger.error(f"Failed to fetch company {company_id} from DynamoDB: {e}")
        return None

if __name__ == "__main__":
    companies = get_all_companies()
    if companies:
        print(f"Found {len(companies)} companies:")
        for company in companies[:5]:  # Show first 5
            print(f"- {company.get('companyName', 'Unknown')} ({company.get('id', 'No ID')})")
        
        # Save to file
        with open('companies_list.json', 'w') as f:
            json.dump(companies, f, indent=2, default=str)
        print(f"All companies saved to companies_list.json")
    else:
        print("No companies found or error occurred")