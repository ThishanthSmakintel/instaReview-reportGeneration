import json
import os
from logger import setup_logger, create_categorical_folders
from datetime import datetime

# Setup logging
logger, timestamp = setup_logger()
folders = create_categorical_folders()

def process_filtered_data():
    logger.info("Starting data processing...")
    
    # Load filtered data - try compatibility file first, then timestamped files
    filtered_data = None
    try:
        with open("output_data/customer_feedback.json", "r") as f:
            filtered_data = json.load(f)
        logger.info(f"Loaded {len(filtered_data)} filtered items from compatibility file")
    except FileNotFoundError:
        try:
            with open("output_data/filtered_data.json", "r") as f:
                filtered_data = json.load(f)
            logger.info(f"Loaded {len(filtered_data)} filtered items from old compatibility file")
        except FileNotFoundError:
            # Try to find the latest timestamped filtered data file
            import glob
            data_files = glob.glob("data/customer_feedback_*.json") + glob.glob("data/filtered_data_*.json")
            if data_files:
                latest_file = max(data_files)
                with open(latest_file, "r") as f:
                    filtered_data = json.load(f)
                logger.info(f"Loaded {len(filtered_data)} filtered items from {latest_file}")
            else:
                logger.error("No customer feedback files found")
                return None
    
    survey_data = []
    audio_feedback_data = []
    
    for item in filtered_data:
        # Process survey data to DynamoDB format
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
        
        # Process audio feedback data
        if item.get("metaData"):
            meta_data = item["metaData"]
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
    
    # Create structured output
    structured_data = {
        "survey_data": survey_data,
        "audio_feedback_data": audio_feedback_data
    }
    
    # Save structured data with timestamp
    structured_data_file = os.path.join(folders['data'], f"processed_feedback_{timestamp}.json")
    with open(structured_data_file, "w") as f:
        json.dump(structured_data, f, indent=2)
    logger.info(f"Saved processed feedback to {structured_data_file}")
    
    # Save to output_data for compatibility
    os.makedirs("output_data", exist_ok=True)
    with open("output_data/processed_feedback.json", "w") as f:
        json.dump(structured_data, f, indent=2)
    logger.info("Saved processed feedback to output_data/processed_feedback.json for compatibility")
    
    logger.info(f"Processed {len(survey_data)} survey items and {len(audio_feedback_data)} audio feedback items")
    return structured_data

def generate_report_data():
    """Generate report data for the InstaReview report"""
    logger.info("Generating report data...")
    structured_data = process_filtered_data()
    
    if not structured_data:
        logger.error("No structured data available")
        return None
    
    # Calculate survey metrics
    survey_metrics = {
        "total_responses": len(structured_data["survey_data"]),
        "question_averages": {}
    }
    
    # Calculate question averages from DynamoDB format
    question_totals = {}
    question_counts = {}
    
    for item in structured_data["survey_data"]:
        question = item["M"]["question"]["S"]
        answer = float(item["M"]["answer"]["N"])
        
        if question not in question_totals:
            question_totals[question] = 0
            question_counts[question] = 0
        
        question_totals[question] += answer
        question_counts[question] += 1
    
    for question in question_totals:
        survey_metrics["question_averages"][question] = round(question_totals[question] / question_counts[question], 1)
    
    # Calculate audio metrics
    audio_data = structured_data["audio_feedback_data"]
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    positive_themes = set()
    negative_themes = set()
    recommendations = []
    transcripts = []
    
    for item in audio_data:
        sentiment = item["feedbackAnalysis"]["overallSentiment"]
        sentiment_counts[sentiment] += 1
        
        positive_themes.update(item["feedbackAnalysis"]["positiveIndicators"])
        negative_themes.update(item["feedbackAnalysis"]["negativeIndicators"])
        recommendations.extend(item["feedbackAnalysis"]["recommendations"])
        
        if item["transcript"]:
            transcripts.append(item["transcript"])
        else:
            transcripts.append("Customer provided feedback about product quality")
    
    total_audio = len(audio_data)
    audio_metrics = {
        "total_feedback": total_audio,
        "sentiment_distribution": sentiment_counts,
        "positive_themes": list(positive_themes)[:5],
        "negative_themes": list(negative_themes)[:5],
        "recommendations": recommendations[:3],
        "sample_transcripts": transcripts[:3]
    }
    
    # Calculate overall stats
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
    
    # Save report data with timestamp
    report_data_file = os.path.join(folders['data'], f"analytics_summary_{timestamp}.json")
    with open(report_data_file, "w") as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Saved analytics summary to {report_data_file}")
    
    logger.info("Report data generation completed")
    return report_data

if __name__ == "__main__":
    process_filtered_data()