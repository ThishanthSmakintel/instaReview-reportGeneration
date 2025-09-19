# Company Weekly Analytics Report Generation System

This system generates professional PDF reports using real customer feedback and survey data from API sources.

## Files Overview

- `fetch_customer_data.py` - Fetches real customer feedback data from API
- `process_feedback.py` - Processes raw data into meaningful metrics and insights
- `create_pdf_report.py` - **Main standalone script** for automated report generation (cron-ready)
- `process_all_companies.py` - **Batch processing script** for all companies with email delivery
- `send_email.py` - Email delivery module using AWS SES
- `fetch_companies_dynamodb.py` - Fetches company data from DynamoDB
- `run_report_generation.py` - Alternative script to run the report generation
- `logger.py` - Logging utility with timestamped logs
- `requirements.txt` - Required Python packages

## Data Structure

### Real API Response Format
```python
{
    "companyId": "123456789A_123456_01-01_FNB",
    "quess": [
        {"question": "Staff attitude", "answer": 3.0, "questionId": "q1"},
        {"question": "Food quality", "answer": 4.0, "questionId": "q2"}
    ],
    "userEmail": "customer@email.com",
    "metaData": {
        "audioId": "1756653729548_123456789A_123456_01-01_FNB",
        "detectedLanguage": "en-US",
        "audioDurationSec": 58,
        "feedbackAnalysis": {
            "overallSentiment": "Negative",
            "tonePrimary": "Frustrated",
            "positiveIndicators": ["good flavor", "impressive"],
            "negativeIndicators": ["not enough cheese", "little meat"],
            "complaintsDetected": true,
            "recommendations": ["Increase cheese quantity", "Improve quality"],
            "retentionRisk": "Medium"
        }
    }
}
```

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

## Usage

### Automated Report Generation (Recommended for Cron)
```bash
python create_pdf_report.py
```

### Batch Processing for All Companies (with Email)
```bash
python process_all_companies.py
```

### Manual Data Fetching
```bash
python fetch_customer_data.py
```

### Alternative Report Generation
```bash
python run_report_generation.py
```

### Cron Setup Example
```bash
# Run batch processing for all companies every Monday at 8 AM
0 8 * * 1 cd /path/to/reprortGeneration && python process_all_companies.py

# Run single company report every day at 9 AM
0 9 * * * cd /path/to/reprortGeneration && python create_pdf_report.py
```

## Report Features

- **Real-time Data**: Fetches live customer feedback from API
- **Dynamic Company Info**: Extracts company name from API data
- **Survey Analysis**: Question averages and response counts from real data
- **Audio Feedback**: Sentiment analysis and theme extraction
- **Visual Charts**: Sentiment trends, ratings distribution, channel breakdown
- **Key Insights**: Positive/negative themes, customer quotes, recommendations
- **Professional PDF**: Headers, footers, branded styling
- **Timestamped Storage**: All data and reports saved with timestamps
- **Automated Email Delivery**: Sends reports via AWS SES with presigned URLs
- **Smart Processing**: Only generates reports for companies with data

## Generated Files Structure

```
data/
├── api_response_TIMESTAMP.json          # Raw API data
├── customer_feedback_TIMESTAMP.json     # Filtered feedback
└── analytics_summary_TIMESTAMP.json     # Report metrics

reports/
└── Company_Weekly_Analytics_TIMESTAMP.pdf

logs/
└── feedback_processing_TIMESTAMP.log    # Complete operation logs
```

## Email Configuration

### Environment Variables
```bash
SES_FROM_EMAIL=reports@instareview.ai  # Sender email address
```

### AWS SES Setup
1. Verify sender email in AWS SES console
2. Ensure AWS profile has SES permissions
3. Companies must have valid email addresses in DynamoDB

### Email Features
- Professional HTML email template
- Presigned S3 URLs for secure report access (7-day expiration)
- Only sends emails for companies with generated reports
- Comprehensive logging of email delivery status

## Customization

1. **API Endpoint**: Update the URL in `fetch_api_data()` function
2. **Filtering Logic**: Modify the `target_audio_id` or filtering criteria
3. **Company Branding**: Update header/footer templates in `create_pdf_report.py`
4. **Report Metrics**: Customize analytics calculations in `generate_report_data()`
5. **Email Template**: Modify email content in `send_email.py`

## Output Examples

**Success:**
```
SUCCESS: Company Weekly Analytics Report generated at reports/Company_Weekly_Analytics_20250905_172837.pdf
```

**Error Handling:**
- Complete logging with timestamps
- Proper exit codes for cron monitoring
- Detailed error messages for troubleshooting

The system automatically processes real customer data and generates professional analytics reports ready for business use.