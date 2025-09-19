import requests
import json
import os
from dotenv import load_dotenv
from logger import setup_logger, create_categorical_folders

# Load environment variables
load_dotenv()

# Setup logging
if __name__ == "__main__":
    logger, timestamp = setup_logger()
    folders = create_categorical_folders()
else:
    import logging
    logger = logging.getLogger('InstaReview')
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folders = {'data': 'data', 'reports': 'reports', 'logs': 'logs'}
    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)

# --- Data Fetching Functions ---
def fetch_company_details():
    try:
        company_id = os.getenv('COMPANY_ID')
        api_key = os.getenv('X_API_KEY_COMPANY_DETAILS_URL')
        base_url = os.getenv('COMPANY_DETAILS_URL')
        url = f"{base_url}?companyId={company_id}"
        headers = {"x-api-key": api_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Company details fetched successfully")
            return data
        print(f"Company details API request failed with status {response.status_code}")
    except Exception as e:
        print(f"Error fetching company details: {e}")
    return None

def fetch_api_data():
    try:
        logger.info("Fetching customer feedback data from API...")
        company_id = os.getenv('COMPANY_ID')
        base_url = os.getenv('REVIEWS_URL')
        url = f"{base_url}?companyId={company_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"API returned {len(data)} customer feedback items")
            return data
        else:
            logger.error(f"API request failed with status {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching customer feedback data: {e}")
    return []

def process_customer_data():
    logger.info("Starting customer feedback data processing...")
    api_data = fetch_api_data()
    
    # Save raw API data
    raw_data_file = os.path.join(folders['data'], f"api_response_{timestamp}.json")
    with open(raw_data_file, "w") as f:
        json.dump(api_data, f, indent=2)
    logger.info(f"Saved raw customer feedback data to {raw_data_file}")
    
    # Process all data - keep items with valid metaData
    filtered = []
    
    logger.info("Processing all customer feedback items with valid metaData")
    for item in api_data:
        meta_data = item.get("metaData")
        if not meta_data:
            continue
        
        if isinstance(meta_data, str):
            try:
                meta_data = json.loads(meta_data)
            except:
                continue
        
        filtered_item = {
            "companyId": item.get("companyId"),
            "quess": item.get("quess"),
            "userEmail": item.get("userEmail"),
            "metaData": meta_data
        }
        filtered.append(filtered_item)
    
    logger.info(f"Processed {len(filtered)} customer feedback items with valid metaData")
    
    # Save filtered data
    filtered_data_file = os.path.join(folders['data'], f"customer_feedback_{timestamp}.json")
    with open(filtered_data_file, "w") as f:
        json.dump(filtered, f, indent=2)
    logger.info(f"Saved filtered customer feedback to {filtered_data_file}")
    
    # Also save to output_data for compatibility
    output_dir = "output_data"
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "customer_feedback.json"), "w") as f:
        json.dump(filtered, f, indent=2)
    logger.info(f"Saved customer feedback to {output_dir}/customer_feedback.json for compatibility")
    
    return filtered

if __name__ == "__main__":
    logger.info("Starting data fetch and processing...")
    filtered_data = process_customer_data()
    
    # Fetch and save company details
    company_details = fetch_company_details()
    if company_details:
        company_details_file = os.path.join(folders['data'], f"company_details_{timestamp}.json")
        with open(company_details_file, "w") as f:
            json.dump(company_details, f, indent=2)
        logger.info(f"Saved company details to {company_details_file}")
    
    logger.info("Data processing completed successfully")