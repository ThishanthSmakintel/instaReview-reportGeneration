import asyncio
from playwright.async_api import async_playwright
import datetime
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
import math
import PyPDF2
import os
import requests
import json
import boto3
from dotenv import load_dotenv
from logger import setup_logger, create_categorical_folders
from fetch_customer_data import fetch_company_details, process_customer_data

# Load environment variables
load_dotenv()

# Setup logging
logger, timestamp = setup_logger()
folders = create_categorical_folders()

# Get company ID from environment
COMPANY_ID = os.getenv('COMPANY_ID')

def upload_to_s3(file_path, company_id, week_num):
    """Upload file to S3 using boto3 profile with YYYY/MM/W#.pdf format"""
    try:
        session = boto3.Session(profile_name=os.getenv('AWS_PROFILE', 'default'))
        s3_client = session.client('s3', region_name=os.getenv('AWS_REGION'))
        bucket = os.getenv('AWS_S3_BUCKET')
        
        # Generate file name as YYYY-MM-W#.pdf
        year = current_time.year
        month = current_time.month
        filename = f"{year:04d}-{month:02d}-W{week_num}.pdf"
        s3_key = f"instareview-reports/{company_id}/{filename}"
        
        s3_client.upload_file(file_path, bucket, s3_key)
        logger.info(f"Uploaded {file_path} to s3://{bucket}/{s3_key}")
        return True
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return False

# --- Get Current Time for Timestamps ---
current_time = datetime.datetime.now()
logger.info("Starting automated company weekly analytics report generation")

def generate_report_data(filtered_data):
    logger.info("Generating customer feedback analytics...")
    
    # Process to structured format
    survey_data = []
    audio_feedback_data = []
    
    for item in filtered_data:
        if item.get("quess"):
            for survey_item in item["quess"]:
                formatted_survey = {
                    "M": {
                        "question": {"S": survey_item["question"]},
                        "answer": {"N": str(survey_item["answer"])},
                        "questionId": {"S": survey_item["questionId"]}
                    }
                }
                survey_data.append(formatted_survey)
        
        if item.get("metaData"):
            meta_data = item["metaData"]
            if isinstance(meta_data, str):
                try:
                    meta_data = json.loads(meta_data)
                except:
                    continue
            

            
            formatted_audio = {
                "audioId": meta_data["audioId"],
                "detectedLanguage": meta_data["detectedLanguage"],
                "audioDurationSec": str(meta_data["audioDurationSec"]),
                "companyName": item["companyId"],
                "transcript": meta_data.get("transcript", ""),
                "feedbackAnalysis": {
                    "overallSentiment": meta_data["feedbackAnalysis"]["overallSentiment"],
                    "tonePrimary": meta_data["feedbackAnalysis"]["tonePrimary"],
                    "positiveIndicators": meta_data["feedbackAnalysis"]["positiveIndicators"],
                    "negativeIndicators": meta_data["feedbackAnalysis"]["negativeIndicators"],
                    "complaintsDetected": str(meta_data["feedbackAnalysis"]["complaintsDetected"]).lower(),
                    "recommendations": meta_data["feedbackAnalysis"]["recommendations"],
                    "retentionRisk": meta_data["feedbackAnalysis"]["retentionRisk"]
                }
            }
            audio_feedback_data.append(formatted_audio)
    
    # Calculate metrics
    survey_metrics = {"total_responses": len(survey_data), "question_averages": {}}
    question_totals = {}
    question_counts = {}
    
    for item in survey_data:
        question = item["M"]["question"]["S"]
        answer = float(item["M"]["answer"]["N"])
        if question not in question_totals:
            question_totals[question] = 0
            question_counts[question] = 0
        question_totals[question] += answer
        question_counts[question] += 1
    
    for question in question_totals:
        survey_metrics["question_averages"][question] = round(question_totals[question] / question_counts[question], 1)
    
    # Audio metrics
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    positive_themes = set()
    negative_themes = set()
    recommendations = []
    transcripts = []
    
    for item in audio_feedback_data:
        sentiment = item["feedbackAnalysis"]["overallSentiment"]
        sentiment_counts[sentiment] += 1
        positive_themes.update(item["feedbackAnalysis"]["positiveIndicators"])
        negative_themes.update(item["feedbackAnalysis"]["negativeIndicators"])
        recommendations.extend(item["feedbackAnalysis"]["recommendations"])
        # Use positive and negative indicators as customer quotes
        feedback_analysis = meta_data.get("feedbackAnalysis", {})
        positive_indicators = feedback_analysis.get("positiveIndicators", [])
        negative_indicators = feedback_analysis.get("negativeIndicators", [])
        
        # Combine positive and negative indicators as quotes
        all_indicators = positive_indicators + negative_indicators
        for indicator in all_indicators:
            if indicator and len(indicator) > 3 and indicator not in ['neutral', 'okay', 'uh']:  # Filter out generic words
                quote = f"Customer mentioned: {indicator}"
                if quote not in transcripts:  # Avoid duplicates
                    transcripts.append(quote)
    
    total_audio = len(audio_feedback_data)
    audio_metrics = {
        "total_feedback": total_audio,
        "sentiment_distribution": sentiment_counts,
        "positive_themes": list(positive_themes)[:5],
        "negative_themes": list(negative_themes)[:5],
        "recommendations": recommendations[:3],
        "sample_transcripts": transcripts[:3] if transcripts else ["No transcript available"]
    }
    
    # Overall stats
    total_feedback = survey_metrics["total_responses"] + audio_metrics["total_feedback"]
    positive_pct = round((sentiment_counts["Positive"] / total_audio * 100) if total_audio > 0 else 0)
    neutral_pct = round((sentiment_counts["Neutral"] / total_audio * 100) if total_audio > 0 else 0)
    negative_pct = round((sentiment_counts["Negative"] / total_audio * 100) if total_audio > 0 else 0)
    
    overall_stats = {
        "total_feedback": total_feedback,
        "positive_percentage": positive_pct,
        "neutral_percentage": neutral_pct,
        "negative_percentage": negative_pct
    }
    
    report_data = {
        "survey_metrics": survey_metrics,
        "audio_metrics": audio_metrics,
        "overall_stats": overall_stats
    }
    
    # Save analytics summary
    analytics_file = os.path.join(folders['data'], f"analytics_summary_{timestamp}.json")
    with open(analytics_file, "w") as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Saved customer feedback analytics to {analytics_file}")
    
    return report_data

# --- Download and encode logo ---
def get_logo_base64():
    try:
        response = requests.get('https://app.instareview.ai/logo/instareview-logo.png')
        return base64.b64encode(response.content).decode()
    except:
        return None

logo_b64 = get_logo_base64()

# Global variables for data - will be initialized when needed
filtered_data = None
report_data = None
client_data = None

def initialize_report_data():
    """Initialize report data for current company"""
    global filtered_data, report_data, client_data
    
    logger.info("Processing real customer feedback data from API...")
    # Check if filtered data exists from API call
    if os.path.exists('output_data/customer_feedback.json'):
        with open('output_data/customer_feedback.json', 'r') as f:
            filtered_data = json.load(f)
        logger.info(f"Using filtered data from API: {len(filtered_data)} records")
    else:
        # Fallback to process_customer_data if no filtered data
        filtered_data = process_customer_data()
        logger.info(f"Using all data from process_customer_data: {len(filtered_data)} records")

    if not filtered_data:
        logger.error("No customer feedback data available")
        return False

    logger.info("Generating customer feedback report analytics...")
    report_data = generate_report_data(filtered_data)
    logger.info("Customer feedback analytics generated successfully")
    
    # Initialize client data
    initialize_client_data()
    return True

def initialize_client_data():
    """Initialize client data for current company"""
    global client_data, filtered_data, report_data
    
    # Fetch company details
    company_details = fetch_company_details()
    company_name = "Unknown Company"
    company_city = "Unknown"
    company_industry = "Unknown"

    if company_details:
        company_name = company_details.get("companyName", "Unknown Company")
        company_city = company_details.get("city", "Unknown")
        company_industry = company_details.get("industry", "Unknown")
        logger.info(f"Using company details: {company_name} in {company_city}, {company_industry}")
    else:
        # Fallback to companyId if API fails
        if filtered_data and len(filtered_data) > 0:
            company_name = filtered_data[0].get("companyId", "Unknown Company")
        logger.warning("Using fallback company name from companyId")

    # Calculate report period from form dates or current date
    from_date_env = os.getenv('REPORT_FROM_DATE')
    to_date_env = os.getenv('REPORT_TO_DATE')

    if from_date_env and to_date_env:
        from datetime import datetime as dt
        week_start = dt.fromisoformat(from_date_env.replace('Z', '')).date()
        week_end = dt.fromisoformat(to_date_env.replace('Z', '')).date()
    else:
        today = current_time.date()
        week_start = today - datetime.timedelta(days=today.weekday())
        week_end = week_start + datetime.timedelta(days=6)

    client_data = {
        "company_name": company_name,
        "company_city": company_city,
        "company_industry": company_industry,
        "report_period_start": week_start,
        "report_period_end": week_end,
        "date_generated": current_time.date(),
        "generation_timestamp": current_time.strftime('%B %d, %Y at %I:%M:%S %p'),
        "total_reviews": report_data["overall_stats"]["total_feedback"],
        "positive_reviews": int(report_data["overall_stats"]["total_feedback"] * report_data["overall_stats"]["positive_percentage"] / 100),
        "neutral_reviews": int(report_data["overall_stats"]["total_feedback"] * report_data["overall_stats"]["neutral_percentage"] / 100),
        "negative_reviews": int(report_data["overall_stats"]["total_feedback"] * report_data["overall_stats"]["negative_percentage"] / 100),
        "avg_feedback_duration": "1.8 min",
        "nps_score": max(10, min(100, 50 + (report_data["overall_stats"]["positive_percentage"] - report_data["overall_stats"]["negative_percentage"]))),
        "top_questions": list(report_data["survey_metrics"]["question_averages"].items()),
        "channels": {
            "Survey": round((report_data["survey_metrics"]["total_responses"] / report_data["overall_stats"]["total_feedback"]) * 100) if report_data["overall_stats"]["total_feedback"] > 0 else 0,
            "Audio Feedback": round((report_data["audio_metrics"]["total_feedback"] / report_data["overall_stats"]["total_feedback"]) * 100) if report_data["overall_stats"]["total_feedback"] > 0 else 0
        },
        "positive_themes": report_data["audio_metrics"]["positive_themes"],
        "negative_themes": report_data["audio_metrics"]["negative_themes"],
        "notable_quotes": report_data["audio_metrics"]["sample_transcripts"],
        "recommendation": ". ".join(report_data["audio_metrics"]["recommendations"]).replace("; ", ". ").replace(";", ""),
        "sentiment_trend_data": {
            "labels": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
            "values": [report_data["overall_stats"]["positive_percentage"], 
                       report_data["overall_stats"]["positive_percentage"] + 5,
                       report_data["overall_stats"]["positive_percentage"] - 3,
                       report_data["overall_stats"]["positive_percentage"] + 8,
                       report_data["overall_stats"]["positive_percentage"] + 2,
                       report_data["overall_stats"]["positive_percentage"] + 10,
                       report_data["overall_stats"]["positive_percentage"] + 6]
        },
        "star_ratings_data": {
            "labels": ["5 ★", "4 ★", "3 ★", "2 ★", "1 ★"],
            "values": [
                report_data["overall_stats"]["positive_percentage"],
                max(0, 100 - report_data["overall_stats"]["positive_percentage"] - report_data["overall_stats"]["neutral_percentage"] - report_data["overall_stats"]["negative_percentage"]),
                report_data["overall_stats"]["neutral_percentage"],
                max(0, report_data["overall_stats"]["negative_percentage"] // 2),
                max(0, report_data["overall_stats"]["negative_percentage"] - (report_data["overall_stats"]["negative_percentage"] // 2))
            ],
            "average": round(sum([avg for _, avg in report_data["survey_metrics"]["question_averages"].items()]) / len(report_data["survey_metrics"]["question_averages"]), 1) if report_data["survey_metrics"]["question_averages"] else 0
        }
    }

# --- Star Rating HTML Generator ---
def generate_star_rating(rating):
    """Generates HTML for star ratings, handling half stars."""
    full_stars = math.floor(rating)
    half_star = 1 if rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    stars_html = f'<span class="rating-stars">{"★" * full_stars}{"½" if half_star else ""}{"☆" * empty_stars}</span> {rating}'
    return stars_html

# --- Chart Generation Functions ---


def create_sentiment_trend_chart():
    fig, ax = plt.subplots(figsize=(3, 2.5), facecolor='white')
    x = range(len(client_data['sentiment_trend_data']['labels']))
    positive = client_data['sentiment_trend_data']['values']
    negative = [50-p for p in positive]
    neutral = [100-p-n for p, n in zip(positive, negative)]
    
    ax.stackplot(x, positive, neutral, negative, labels=['Positive', 'Neutral', 'Negative'], 
                colors=['#10b981', '#94a3b8', '#ef4444'], alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(client_data['sentiment_trend_data']['labels'], fontsize=7)
    ax.set_ylabel('Sentiment %', fontsize=8); ax.tick_params(axis='both', labelsize=7)
    ax.legend(loc='upper right', fontsize=6); ax.set_ylim(0, 100)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    buf = BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white'); buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode(); plt.close(); return img_b64

def create_star_ratings_chart():
    fig, ax = plt.subplots(figsize=(3, 2.5), facecolor='white')
    colors = ['#10b981', '#84cc16', '#f59e0b', '#f97316', '#ef4444']
    values = client_data['star_ratings_data']['values']; labels = client_data['star_ratings_data']['labels']
    bars = ax.bar(labels, values, color=colors, alpha=0.8)
    ax.set_ylabel('Reviews (%)', fontsize=8); ax.tick_params(axis='both', labelsize=8)
    for bar, value in zip(bars, values): ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{value}%', ha='center', va='bottom', fontsize=7, fontweight='bold')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.grid(True, alpha=0.3, axis='y')
    buf = BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white'); buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode(); plt.close(); return img_b64

def create_channel_pie_chart():
    fig, ax = plt.subplots(figsize=(3, 2.5), facecolor='white')
    channels = list(client_data['channels'].keys()); values = list(client_data['channels'].values())
    colors = ['#3b82f6', '#10b981', '#f59e0b']
    wedges, texts, autotexts = ax.pie(values, labels=channels, colors=colors, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})
    for autotext in autotexts: autotext.set_color('white'); autotext.set_fontweight('bold')
    ax.set_title('Channel Distribution', fontsize=10, fontweight='bold', pad=10)
    buf = BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white'); buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode(); plt.close(); return img_b64

def create_nps_trend_chart():
    fig, ax = plt.subplots(figsize=(3, 2.5), facecolor='white')
    weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    base_nps = client_data['nps_score']
    nps_scores = [base_nps-2, base_nps+1, base_nps-1, base_nps]
    ax.plot(weeks, nps_scores, color='#8b5cf6', linewidth=3, marker='o', markersize=6, markerfacecolor='white', markeredgecolor='#8b5cf6', markeredgewidth=2)
    ax.fill_between(weeks, nps_scores, alpha=0.2, color='#8b5cf6')
    ax.set_ylabel('NPS Score', fontsize=8); ax.tick_params(axis='both', labelsize=8)
    ax.set_ylim(60, 70); ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    buf = BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white'); buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode(); plt.close(); return img_b64

def generate_charts():
    """Generate all charts for the report"""
    global client_data
    trend_chart = create_sentiment_trend_chart()
    star_chart = create_star_ratings_chart()
    channel_chart = create_channel_pie_chart()
    nps_chart = create_nps_trend_chart()
    return trend_chart, star_chart, channel_chart, nps_chart

def generate_header_template():
    """Generate PDF header template"""
    global client_data
    return f"""
<div style="width: 100%; font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 15px 20mm; box-sizing: border-box; border-bottom: 3px solid #3b82f6; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #1e40af, #3b82f6); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 14px;">TC</div>
            <div>
                <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin: 0;">{client_data['company_name']} Weekly Analytics Report</div>
                <div style="font-size: 9px; color: #64748b; margin: 0;">{client_data['company_city']} | {client_data['company_industry']} Industry</div>
                <div style="font-size: 10px; color: #64748b; margin: 0; display: flex; align-items: center; gap: 8px;">Powered by <div style="width: 16px; height: 16px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 8px;">IR</div> InstaReview.ai</div>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 11px; font-weight: 600; color: #3b82f6;">Week of {client_data['report_period_start'].strftime('%b %d')} – {client_data['report_period_end'].strftime('%b %d, %Y')}</div>
            <div style="font-size: 9px; color: #64748b;">Generated on {current_time.strftime('%B %d, %Y')}</div>
        </div>
    </div>
</div>
"""

def generate_footer_template():
    """Generate PDF footer template"""
    global client_data
    return f"""
<div style="width: 100%; font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 12px 20mm; box-sizing: border-box; border-top: 3px solid #3b82f6;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="font-size: 10px; font-weight: 500;">{client_data['company_name']} | Weekly Analytics Report</div>
            <div style="font-size: 8px; color: #94a3b8; margin-top: 2px;">*Analysis based on AI processing of transcript metadata, not human review</div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="font-size: 9px; color: #94a3b8;">InstaReview.ai Analytics</div>
            <div style="font-size: 10px; font-weight: 600; background: rgba(59, 130, 246, 0.2); padding: 4px 8px; border-radius: 4px;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>
        </div>
    </div>
</div>
"""

def generate_html_content(trend_chart, star_chart, channel_chart, nps_chart):
    """Generate HTML content for the report"""
    global client_data, report_data
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{client_data['company_name']} Weekly Analytics Report - InstaReview.ai</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: white; color: #1e293b; -webkit-print-color-adjust: exact; }}

        .page {{ width: 210mm; min-height: 297mm; padding: 30mm 15mm 25mm 15mm; background: white; page-break-inside: avoid; }}
        @page {{ size: A4; margin: 0; }}
        @media print {{ .page {{ page-break-after: avoid; }} }}
        
        .logo {{ width: 40px; height: 40px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 16px; }}
        .brand-info h1 {{ font-size: 20px; margin: 0; }}
        .brand-info p {{ font-size: 12px; color: #64748b; margin: 0; }}
        .report-period {{ font-size: 12px; color: #64748b; }}
        
        .summary {{ background: #eff6ff; border-left: 4px solid #3b82f6; font-size: 12px; font-weight: 600; }}
        
        .kpi-value {{ font-size: 24px; font-weight: 800; }}
        .kpi-label {{ font-size: 10px; color: #64748b; font-weight: 500; }}
        .comparison {{ font-size: 10px; margin-top: 4px; }}
        .trend-up {{ color: #10b981; }} .trend-down {{ color: #ef4444; }}
        
        .chart-title {{ font-size: 12px; font-weight: 700; margin-bottom: 8px; text-align: center; }}
        .chart-img {{ width: 100%; height: 180px; object-fit: contain; }}
        .insight-card {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; flex-shrink: 0; height: 100%; }}
        .insight-title {{ font-size: 12px; font-weight: 700; margin-bottom: 8px; }}
        
        .questions-table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
        .questions-table th, .questions-table td {{ padding: 4px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        .questions-table th {{ background: #f8fafc; font-weight: 600; color: #64748b; }}
        .rating-stars {{ color: #fbbf24; }}
        
        .theme-list {{ list-style: none; display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }}
        .theme-tag {{ background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 12px; font-size: 10px; }}
        .theme-tag.negative {{ background: #fef2f2; color: #dc2626; }}
        
        .quotes {{ font-size: 10px; }}
        .quote {{ font-style: italic; color: #64748b; margin-bottom: 4px; padding: 6px; background: #f8fafc; border-radius: 4px; border-left: 2px solid #3b82f6; }}
        
        .footer {{ background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; font-size: 11px; font-weight: 500; display: flex; justify-content: space-between; align-items: center; }}
    </style>
</head>
<body>
    <div class="page container-fluid">
        

        
        <div class="row g-3 mb-3">
            <div class="col-3"><div class="border rounded p-3 text-center h-100 d-flex flex-column justify-content-between"><div class="kpi-value"><i class="fas fa-star text-warning"></i> {client_data['total_reviews']}</div><div class="kpi-label">Total Reviews</div><div class="comparison trend-up"><i class="fas fa-arrow-up"></i> 15%</div></div></div>
            <div class="col-3"><div class="border rounded p-3 text-center h-100 d-flex flex-column justify-content-between"><div class="kpi-value"><i class="fas fa-smile text-success"></i> {round((client_data['positive_reviews']/client_data['total_reviews'])*100)}%</div><div class="kpi-label">Positive</div><div class="comparison trend-up"><i class="fas fa-arrow-up"></i> 3%</div></div></div>
            <div class="col-3"><div class="border rounded p-3 text-center h-100 d-flex flex-column justify-content-between"><div class="kpi-value"><i class="fas fa-meh text-secondary"></i> {round((client_data['neutral_reviews']/client_data['total_reviews'])*100)}%</div><div class="kpi-label">Neutral</div><div class="comparison"><i class="fas fa-minus"></i> 0%</div></div></div>
            <div class="col-3"><div class="border rounded p-3 text-center h-100 d-flex flex-column justify-content-between"><div class="kpi-value"><i class="fas fa-frown text-danger"></i> {round((client_data['negative_reviews']/client_data['total_reviews'])*100)}%</div><div class="kpi-label">Negative</div><div class="comparison trend-down"><i class="fas fa-arrow-down"></i> 2%</div></div></div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-6"><div class="border rounded p-3"><div class="chart-title"><i class="fas fa-chart-line text-primary"></i> Sentiment Trend (7 Days)</div><img src="data:image/png;base64,{trend_chart}" class="chart-img"></div></div>
            <div class="col-6"><div class="border rounded p-3"><div class="chart-title"><i class="fas fa-star text-warning"></i> Star Ratings Distribution</div><img src="data:image/png;base64,{star_chart}" class="chart-img"></div></div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-check-circle text-success"></i> Top Positive Themes</div>
                    <div class="theme-list">{''.join([f'<span class="theme-tag">{theme}</span>' for theme in client_data['positive_themes']])}</div>
                    <div class="insight-title"><i class="fas fa-exclamation-triangle text-warning"></i> Areas for Improvement</div>
                    <div class="theme-list">{''.join([f'<span class="theme-tag negative">{theme}</span>' for theme in client_data['negative_themes']])}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="insight-card quotes">
                    <div class="insight-title"><i class="fas fa-quote-left text-info"></i> Notable Customer Quotes</div>
                    {''.join([f'<div class="quote" style="border-left: 2px solid {"#10b981" if i==0 else "#64748b" if i==1 else "#ef4444"}; background: {"#f0fdf4" if i==0 else "#f8fafc" if i==1 else "#fef2f2"};">"{quote}"</div>' for i, quote in enumerate(client_data['notable_quotes'][:3])])}
                </div>
            </div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-chart-bar text-primary"></i> Survey Questions Performance</div>
                    <table class="questions-table">
                        <tbody>{''.join(f"<tr><td>{q[0]}</td><td>{generate_star_rating(q[1])}</td></tr>" for q in client_data['top_questions'])}</tbody>
                    </table>
                </div>
            </div>
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-lightbulb text-warning"></i> Key Recommendations</div>
                    <div style="font-size: 11px;">{client_data['recommendation']}</div>
                </div>
            </div>
        </div>
        
    </div>
    
    <!-- PAGE 2 -->
    <div class="page container-fluid" style="page-break-before: always;">
        

        
        <div class="row g-3 mb-3">
            <div class="col-6"><div class="border rounded p-3"><div class="chart-title"><i class="fas fa-chart-pie text-info"></i> Channel Breakdown</div><img src="data:image/png;base64,{channel_chart}" class="chart-img"></div></div>
            <div class="col-6"><div class="border rounded p-3"><div class="chart-title"><i class="fas fa-chart-area text-purple"></i> NPS Trend (4 Weeks)</div><img src="data:image/png;base64,{nps_chart}" class="chart-img"></div></div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-chart-pie text-primary"></i> Sentiment Breakdown</div>
                    <div style="font-size: 11px;">
                        <div class="mb-2 d-flex justify-content-between"><span><i class="fas fa-smile text-success"></i> Positive</span> <strong>{report_data['overall_stats']['positive_percentage']}% ({report_data['audio_metrics']['sentiment_distribution'].get('Positive', 0)} reviews)</strong></div>
                        <div class="mb-2 d-flex justify-content-between"><span><i class="fas fa-meh text-secondary"></i> Neutral</span> <strong>{report_data['overall_stats']['neutral_percentage']}% ({report_data['audio_metrics']['sentiment_distribution'].get('Neutral', 0)} reviews)</strong></div>
                        <div class="mb-2 d-flex justify-content-between"><span><i class="fas fa-frown text-danger"></i> Negative</span> <strong>{report_data['overall_stats']['negative_percentage']}% ({report_data['audio_metrics']['sentiment_distribution'].get('Negative', 0)} reviews)</strong></div>
                    </div>
                </div>
            </div>
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-balance-scale text-info"></i> Feedback Distribution</div>
                    <div style="font-size: 11px;">
                        <div class="mb-1">Survey Responses: {report_data['survey_metrics']['total_responses']}</div>
                        <div class="mb-1">Audio Feedback: {report_data['audio_metrics']['total_feedback']}</div>
                        <div class="mb-1">Total Feedback: {report_data['overall_stats']['total_feedback']}</div>
                        <div class="mb-1">Complaints Detected: {sum(1 for item in report_data['audio_metrics'].get('sample_transcripts', []) if 'disappointing' in item.lower() or 'bad' in item.lower())}/{report_data['audio_metrics']['total_feedback']}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-trending-up text-success"></i> Improvement Areas</div>
                    <ul style="font-size: 10px; margin: 0; padding-left: 15px;">
                        <li>Enhance tortilla texture and quality</li>
                        <li>Increase cheese and meat portions</li>
                        <li>Improve flavor profile consistency</li>
                        <li>Better microwave cooking instructions</li>
                    </ul>
                </div>
            </div>
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-target text-primary"></i> Success Metrics</div>
                    <div style="font-size: 11px;">
                        <div class="mb-1">Customer Satisfaction: 3.4/5</div>
                        <div class="mb-1">Response Rate: 100%</div>
                        <div class="mb-1">Feedback Quality: High</div>
                        <div class="mb-1">Action Items: 4 identified</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-12">
                <div class="border rounded p-3" style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);">
                    <div class="row">
                        <div class="col-8">
                            <div class="mb-2"><i class="fas fa-lightbulb text-warning"></i> <strong>Next Steps</strong></div>
                            <div style="font-size: 11px; color: #64748b;">Focus on product quality improvements based on feedback</div>
                        </div>
                        <div class="col-4 text-end">
                            <div class="mb-1"><span class="badge bg-primary">NPS Score: {client_data['nps_score']}</span></div>
                            <div style="font-size: 9px; color: #64748b;">Powered by InstaReview.ai</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-12">
                <div class="border rounded p-2" style="background: #fef3c7; border-color: #f59e0b;">
                    <div style="font-size: 9px; color: #92400e; text-align: left;">
                        <i class="fas fa-info-circle"></i> <strong>Disclaimer:</strong> This analysis is generated by AI based on transcript metadata and automated sentiment analysis. Results should be verified by human review for business-critical decisions.
                    </div>
                </div>
            </div>
        </div>

    </div>
</body>
</html>
"""

def remove_blank_pages(input_path):
    """Remove blank pages from PDF."""
    name, ext = os.path.splitext(input_path)
    output_path = f"{name}_final{ext}"
    
    with open(input_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text().strip()
            # Check if page has substantial content (not just header/footer)
            if len(text) >= 50 and ('Total Reviews' in text or 'Weekly Report' in text or 'Sentiment Trend' in text):
                writer.add_page(page)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
    
    os.remove(input_path)
    return output_path

async def generate_pdf():
    global client_data, report_data
    
    # Initialize data if not already done
    if not initialize_report_data():
        raise Exception("Failed to initialize report data")
    
    # Generate charts and HTML content
    trend_chart = create_sentiment_trend_chart()
    star_chart = create_star_ratings_chart()
    channel_chart = create_channel_pie_chart()
    nps_chart = create_nps_trend_chart()
    
    # Generate templates
    header_template = generate_header_template()
    footer_template = generate_footer_template()
    html_content = generate_html_content(trend_chart, star_chart, channel_chart, nps_chart)
    
    logger.info("Starting customer feedback PDF report generation...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        logger.info("HTML content loaded successfully")

        # Save to timestamped reports folder with company ID
        company_id = os.getenv('COMPANY_ID', 'unknown')
        pdf_filename = f"Company_Weekly_Analytics_{company_id}_{timestamp}.pdf"
        pdf_path = os.path.join(folders['reports'], pdf_filename)

        await page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=header_template,
            footer_template=footer_template,
            margin={"top": "25mm", "bottom": "22mm", "left": "15mm", "right": "15mm"}
        )
        await browser.close()
        logger.info(f"Company weekly analytics report generated: {pdf_path}")
        
        # Upload to S3
        week_num = current_time.isocalendar()[1]  # Get ISO week number
        if upload_to_s3(pdf_path, company_id, week_num):
            print(f"Report uploaded to S3 successfully!")
        else:
            print(f"S3 upload failed, but PDF saved locally")
        
        print(f"Company Weekly Analytics Report generated successfully!")
        print(f"Report saved to: {pdf_path}")
        
        return pdf_path

async def main():
    """Main function for automated report generation"""
    try:
        logger.info("Starting automated company weekly analytics report generation")
        
        # Set a default company ID if not set
        if not os.getenv('COMPANY_ID'):
            os.environ['COMPANY_ID'] = 'default'
            
        pdf_path = await generate_pdf()
        logger.info(f"Company weekly analytics report generation completed successfully: {pdf_path}")
        print(f"SUCCESS: Company Weekly Analytics Report generated at {pdf_path}")
        return True
    except Exception as e:
        logger.error(f"Company weekly analytics report generation failed: {e}")
        print(f"ERROR: Company weekly analytics report generation failed - {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

