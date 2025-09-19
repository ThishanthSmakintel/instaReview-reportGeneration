from dotenv import load_dotenv
from fetch_companies_dynamodb import get_all_companies

# Load environment variables
load_dotenv()

def test_company_ids():
    """Test if we can fetch company IDs from DynamoDB"""
    print("Testing DynamoDB connection and company ID retrieval...")
    
    companies = get_all_companies()
    
    if not companies:
        print("❌ No companies found or connection failed")
        return
    
    print(f"✅ Found {len(companies)} companies")
    print("\nFirst 5 companies:")
    
    for i, company in enumerate(companies[:5]):
        company_id = company.get('id')
        company_name = company.get('companyName', 'Unknown')
        
        print(f"{i+1}. ID: {company_id}")
        print(f"   Name: {company_name}")
        print(f"   Keys: {list(company.keys())}")
        print()
    
    # Check if all companies have 'id' field
    companies_with_id = [c for c in companies if c.get('id')]
    companies_without_id = [c for c in companies if not c.get('id')]
    
    print(f"Companies with 'id' field: {len(companies_with_id)}")
    print(f"Companies without 'id' field: {len(companies_without_id)}")
    
    if companies_without_id:
        print("\nCompanies missing 'id' field:")
        for company in companies_without_id[:3]:
            print(f"- {company}")

if __name__ == "__main__":
    test_company_ids()