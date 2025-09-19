import boto3
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
import logging
logger = logging.getLogger('InstaReview')
if not logger.handlers:
    logger, _ = setup_logger()

def generate_presigned_url(s3_key, expiration=604800):  # 7 days
    """Generate presigned URL for S3 object"""
    try:
        session = boto3.Session(profile_name=os.getenv('AWS_PROFILE', 'default'))
        s3_client = session.client('s3', region_name=os.getenv('AWS_REGION'))
        bucket = os.getenv('AWS_S3_BUCKET')
        
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': s3_key},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        return None

def send_report_email(company_data, pdf_s3_key, recipient_email):
    """Send weekly report email using SMTP"""
    try:
        # Generate presigned URL
        report_url = generate_presigned_url(pdf_s3_key)
        if not report_url:
            logger.error("Failed to generate presigned URL for report")
            return False
        
        company_name = company_data.get('companyName', 'Your Company')
        
        # Email content
        subject = f"Your Weekly InstaReview Report is Ready - {company_name}"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; background: #f8fafc; }}
        .email-container {{ max-width: 600px; margin: 0 auto; background: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; }}
        .logo {{ width: 80px; height: 80px; border-radius: 12px; margin: 0 auto 20px; overflow: hidden; }}
        .logo img {{ width: 100%; height: 100%; object-fit: contain; }}
        .header h1 {{ color: white; font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
        .header p {{ color: rgba(255,255,255,0.9); font-size: 16px; }}
        .content {{ padding: 40px 30px; }}
        .greeting {{ font-size: 18px; color: #1a202c; margin-bottom: 24px; }}
        .description {{ font-size: 16px; color: #4a5568; line-height: 1.6; margin-bottom: 32px; }}
        .features {{ background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); border-radius: 12px; padding: 24px; margin: 32px 0; }}
        .features h3 {{ color: #2d3748; font-size: 18px; margin-bottom: 16px; display: flex; align-items: center; }}
        .feature-item {{ display: flex; align-items: center; margin: 12px 0; color: #4a5568; }}
        .feature-icon {{ margin-right: 12px; font-size: 16px; flex-shrink: 0; }}
        .cta-section {{ text-align: center; margin: 40px 0; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); transition: transform 0.2s; }}
        .cta-button:hover {{ transform: translateY(-2px); }}
        .portal-link {{ text-align: center; margin: 24px 0; padding: 20px; background: #f7fafc; border-radius: 8px; }}
        .portal-link a {{ color: #667eea; text-decoration: none; font-weight: 500; }}
        .footer {{ background: #2d3748; color: #a0aec0; padding: 30px; text-align: center; }}
        .footer-brand {{ color: white; font-weight: 600; margin-bottom: 8px; }}
        .footer-links {{ font-size: 14px; }}
        .footer-links a {{ color: #667eea; text-decoration: none; }}
        @media (max-width: 600px) {{
            .content {{ padding: 30px 20px; }}
            .header {{ padding: 30px 20px; }}
            .header h1 {{ font-size: 24px; }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <div class="logo"><img src="https://instareview.ai/logo.png" alt="InstaReview Logo"></div>
            <h1>📊 Weekly Analytics Report</h1>
            <p>Your customer insights are ready</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {company_name} 👋</div>
            
            <div class="description">
                Your weekly consolidated InstaReview report is now available. This report highlights actionable insights gathered from your customer reviews over the past week, helping you identify trends and areas of improvement quickly.
            </div>
            
            <div class="features">
                <h3>📊 What's inside this report:</h3>
                <div class="feature-item">
                    <div class="feature-icon">📈</div>
                    <span>Key performance highlights and metrics</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">💡</div>
                    <span>Actionable insights and recommendations</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">📊</div>
                    <span>Customer sentiment trends analysis</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">⭐</div>
                    <span>Detailed analytics and visual charts</span>
                </div>
            </div>
            
            <div class="cta-section">
                <a href="{report_url}" class="cta-button" style="color: white !important;">📥 Download Your Report</a>
            </div>
            
            <div class="portal-link">
                <p>💻 Access your dashboard anytime at <a href="https://app.instareview.ai/">app.instareview.ai</a></p>
            </div>
            
            <div style="margin-top: 32px; color: #4a5568; line-height: 1.6;">
                <p>Thank you for choosing InstaReview to power your customer experience journey.</p>
                <br>
                <p><strong>Best regards,</strong><br>The InstaReview Team</p>
            </div>
        </div>
        
        <div class="footer">
            <div class="footer-brand">InstaReview.ai</div>
            <div class="footer-links">
                <a href="mailto:support@instareview.ai">Mail Us</a> • 
                <a href="https://instareview.ai/live-chat">Live Chat</a> • 
                <a href="https://instareview.ai/">Visit Website</a>
            </div>
            <div style="margin-top: 12px; font-size: 14px; color: #cbd5e0;">
                © {datetime.now().year} InstaReview.ai. All rights reserved.
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        text_body = f"""
Hello {company_name},

Your weekly consolidated InstaReview report is now available. This report highlights actionable insights gathered from your customer reviews over the past week, helping you identify trends and areas of improvement quickly.

📊 What's inside:
• Key performance highlights and metrics
• Actionable insights and recommendations  
• Customer sentiment trends analysis
• Detailed analytics and visual charts

👉 Download your report here: {report_url}

💻 Access your dashboard anytime at: https://app.instareview.ai/

Thank you for choosing InstaReview to power your customer experience journey.

Best regards,
The InstaReview Team
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = os.getenv('SMTP_FROM_EMAIL', 'reports@instareview.ai')
        msg['To'] = recipient_email
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email via SMTP
        server = smtplib.SMTP_SSL(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT')))
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")
        return False

def send_reports_for_companies(companies_with_reports):
    """Send emails for multiple companies with reports"""
    success_count = 0
    total_count = len(companies_with_reports)
    
    for company_data, s3_key in companies_with_reports:
        company_email = company_data.get('email')
        company_name = company_data.get('companyName', 'Unknown')
        
        if not company_email:
            logger.warning(f"No email found for company {company_name}")
            continue
            
        if send_report_email(company_data, s3_key, company_email):
            success_count += 1
            logger.info(f"Report email sent successfully to {company_name} ({company_email})")
        else:
            logger.error(f"Failed to send report email to {company_name} ({company_email})")
    
    logger.info(f"Email sending completed: {success_count}/{total_count} emails sent successfully")
    return success_count, total_count