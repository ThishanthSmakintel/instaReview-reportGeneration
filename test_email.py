#!/usr/bin/env python3
"""
Test script for email functionality
"""
import os
from dotenv import load_dotenv
from send_email import send_report_email

# Load environment variables
load_dotenv()

def test_email():
    """Test email sending functionality"""
    
    # Mock company data
    test_company = {
        'companyName': 'Test Restaurant',
        'email': 'dev15.smakintel@gmail.com'  # Replace with your test email
    }
    
    # Use existing report file
    test_s3_key = "instareview-reports/123456789A_123456_01-01_FNB/w38.pdf"
    
    print("Testing email functionality...")
    print(f"Company: {test_company['companyName']}")
    print(f"Email: {test_company['email']}")
    print(f"S3 Key: {test_s3_key}")
    
    # Send test email
    success = send_report_email(test_company, test_s3_key, test_company['email'])
    
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Test email failed!")
    
    return success

if __name__ == "__main__":
    test_email()