from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
import os
import subprocess
import sys
from datetime import datetime
from fetch_customer_data import fetch_api_data, fetch_company_details
import json

app = Flask(__name__)
CORS(app)

# Create reports folder
REPORTS_FOLDER = 'api_reports'
os.makedirs(REPORTS_FOLDER, exist_ok=True)

@app.route('/reports/generate', methods=['POST'])
def generate_report():
    try:
        data = request.json
        company_id = data.get('companyId')
        from_date = data.get('from')
        to_date = data.get('to')
        
        if not all([company_id, from_date, to_date]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Set company ID for data fetching
        os.environ['COMPANY_ID'] = company_id
        
        # Fetch data
        api_data = fetch_api_data()
        company_details = fetch_company_details()
        
        # Filter by specific row IDs
        filtered_data = filter_by_date_range(api_data, from_date, to_date)
        
        if not filtered_data:
            return jsonify({'error': 'No data found for the specified row IDs (1757322288349, 1757322711026)'}), 404
        
        # Log filtered data count for verification
        print(f"Processing {len(filtered_data)} records with IDs: {[item.get('id') for item in filtered_data]}")
        
        # Save filtered data for existing system to use
        os.makedirs('output_data', exist_ok=True)
        with open('output_data/customer_feedback.json', 'w') as f:
            json.dump(filtered_data, f, indent=2)
        
        # Set date range environment variables for PDF generation
        os.environ['REPORT_FROM_DATE'] = from_date
        os.environ['REPORT_TO_DATE'] = to_date
        
        # Use existing PDF generation system
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{company_id}_{timestamp}.pdf"
        
        # Run existing PDF generation script
        result = subprocess.run([sys.executable, 'create_pdf_report.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode != 0:
            return jsonify({'error': f'PDF generation failed: {result.stderr}'}), 500
        
        # Find the generated PDF and move it to API reports folder
        import glob
        pdf_files = glob.glob('reports/Company_Weekly_Analytics_*.pdf')
        if not pdf_files:
            return jsonify({'error': 'Generated PDF not found'}), 500
        
        latest_pdf = max(pdf_files, key=os.path.getctime)
        pdf_path = os.path.join(REPORTS_FOLDER, filename)
        os.rename(latest_pdf, pdf_path)
        
        # Save HTML content for embedding
        html_file = filename.replace('.pdf', '.html')
        html_path = os.path.join(REPORTS_FOLDER, html_file)
        
        # Extract HTML from the PDF generation process
        with open('temp_report.html', 'w', encoding='utf-8') as f:
            f.write(get_report_html(filtered_data, company_details))
        
        os.rename('temp_report.html', html_path)
        
        # Generate URLs
        base_url = request.host_url.rstrip('/')
        view_url = f"{base_url}/reports/view/{filename}"
        download_url = f"{base_url}/reports/download/{filename}"
        html_url = f"{base_url}/reports/html-file/{html_file}"
        
        return jsonify({
            'viewUrl': view_url,
            'downloadUrl': download_url,
            'htmlUrl': html_url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reports/view/<filename>')
def view_report(filename):
    return send_file(os.path.join(REPORTS_FOLDER, filename), mimetype='application/pdf')

@app.route('/reports/download/<filename>')
def download_report(filename):
    return send_file(os.path.join(REPORTS_FOLDER, filename), as_attachment=True)

@app.route('/reports/html-file/<filename>')
def serve_html_report(filename):
    return send_file(os.path.join(REPORTS_FOLDER, filename), mimetype='text/html')

@app.route('/api/download-pdf', methods=['POST'])
def download_pdf():
    try:
        data = request.json
        company_id = data.get('companyId')
        from_date = data.get('fromDate')
        to_date = data.get('toDate')
        
        if not all([company_id, from_date, to_date]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Generate report first
        result = generate_report_internal(company_id, from_date, to_date)
        
        if 'error' in result:
            return jsonify(result), 500
        
        # Return the PDF file
        pdf_path = result['pdf_path']
        return send_file(pdf_path, as_attachment=True, download_name=f"{company_id}_report.pdf")
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_report_internal(company_id, from_date, to_date):
    try:
        os.environ['COMPANY_ID'] = company_id
        
        api_data = fetch_api_data()
        filtered_data = filter_by_date_range(api_data, from_date, to_date)
        
        if not filtered_data:
            return {'error': 'No data found for target IDs'}
        
        os.makedirs('output_data', exist_ok=True)
        with open('output_data/customer_feedback.json', 'w') as f:
            json.dump(filtered_data, f, indent=2)
        
        os.environ['REPORT_FROM_DATE'] = from_date
        os.environ['REPORT_TO_DATE'] = to_date
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{company_id}_{timestamp}.pdf"
        
        result = subprocess.run([sys.executable, 'create_pdf_report.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode != 0:
            return {'error': f'PDF generation failed: {result.stderr}'}
        
        import glob
        pdf_files = glob.glob('reports/Company_Weekly_Analytics_*.pdf')
        if not pdf_files:
            return {'error': 'Generated PDF not found'}
        
        latest_pdf = max(pdf_files, key=os.path.getctime)
        pdf_path = os.path.join(REPORTS_FOLDER, filename)
        os.rename(latest_pdf, pdf_path)
        
        return {'pdf_path': pdf_path}
        
    except Exception as e:
        return {'error': str(e)}

def get_report_html(filtered_data, company_details):
    # This should return the same HTML used in create_pdf_report.py
    # For now, return a simple version - you can copy the full HTML from create_pdf_report.py
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analytics Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .metric {{ border: 1px solid #ccc; padding: 15px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>Customer Feedback Analytics Report</h1>
        <p>Company: {company_details.get('companyName', 'N/A') if company_details else 'N/A'}</p>
        <p>Total Records: {len(filtered_data)}</p>
        
        {''.join([f'<div class="metric"><h3>Record {item.get("id")}</h3><p>Data processed</p></div>' for item in filtered_data])}
    </body>
    </html>
    """

def filter_by_date_range(data, from_date, to_date):
    # Filter by specific row IDs only
    target_row_ids = ['1757322288349', '1757322711026']
    
    print(f"Total API data received: {len(data)} records")
    
    filtered = []
    for item in data:
        # Check if item has an 'id' field that matches our target IDs
        item_id = str(item.get('id', ''))
        if item_id in target_row_ids:
            filtered.append(item)
            print(f"Found matching record with ID: {item_id}")
            print(f"Record data: {json.dumps(item, indent=2)}")
            print(f"MetaData type: {type(item.get('metaData'))}")
            print(f"MetaData content: {item.get('metaData')}")
            print("---")
    
    print(f"Filtered to {len(filtered)} records matching target IDs")
    return filtered

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/data')
def get_api_data():
    try:
        os.environ['COMPANY_ID'] = '123456789A_123456_01-01_FNB'
        api_data = fetch_api_data()
        return jsonify(api_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    # Get data stats for display
    try:
        os.environ['COMPANY_ID'] = '123456789A_123456_01-01_FNB'  # Default company
        api_data = fetch_api_data()
        target_row_ids = ['1757322288349', '1757322711026']
        
        filtered_data = []
        for item in api_data:
            item_id = str(item.get('id', ''))
            if item_id in target_row_ids:
                filtered_data.append(item)
        
        # Show full metadata for filtered records only
        metadata_info = []
        for item in filtered_data:
            meta = item.get('metaData', {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except:
                    meta = {}
            
            feedback_analysis = meta.get('feedbackAnalysis', {})
            metadata_info.append({
                'id': item.get('id'),
                'companyId': item.get('companyId', 'N/A'),
                'userEmail': item.get('userEmail', 'N/A'),
                'audioId': meta.get('audioId', 'N/A'),
                'language': meta.get('detectedLanguage', 'N/A'),
                'duration': meta.get('audioDurationSec', 'N/A'),
                'sentiment': feedback_analysis.get('overallSentiment', 'N/A'),
                'tone': feedback_analysis.get('tonePrimary', 'N/A'),
                'positives': ', '.join(feedback_analysis.get('positiveIndicators', [])) or 'None',
                'negatives': ', '.join(feedback_analysis.get('negativeIndicators', [])) or 'None',
                'complaints': str(feedback_analysis.get('complaintsDetected', 'N/A')),
                'recommendations': ', '.join(feedback_analysis.get('recommendations', [])) or 'None',
                'retention_risk': feedback_analysis.get('retentionRisk', 'N/A'),
                'quess': item.get('quess', []) or [],
                'raw_data': json.dumps(item, indent=2)
            })
        
        stats = {
            'total_records': len(api_data),
            'filtered_records': len(filtered_data),
            'target_ids': target_row_ids,
            'found_ids': [item.get('id') for item in filtered_data],
            'metadata': metadata_info
        }
    except Exception as e:
        stats = {'error': str(e)}
    
    return render_template('index.html', stats=stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)