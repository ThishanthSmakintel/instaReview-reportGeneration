import os
from playwright.sync_api import sync_playwright
import json

def create_pdf_report_with_data(report_data, output_path):
    """Create PDF report with provided data"""
    
    # Generate HTML content
    html_content = generate_html_report(report_data)
    
    # Create PDF using Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.pdf(
            path=output_path,
            format='A4',
            print_background=True,
            margin={'top': '1in', 'bottom': '1in', 'left': '0.5in', 'right': '0.5in'}
        )
        browser.close()

def generate_html_report(data):
    """Generate HTML content for the report"""
    company_name = data.get('company_name', 'Company')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
            .metrics {{ display: flex; justify-content: space-around; margin: 30px 0; }}
            .metric {{ text-align: center; }}
            .metric h3 {{ margin: 0; color: #666; }}
            .metric .value {{ font-size: 2em; font-weight: bold; color: #333; }}
            .section {{ margin: 30px 0; }}
            .section h2 {{ color: #333; border-bottom: 1px solid #ccc; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{company_name} Weekly Analytics Report</h1>
            <p>Generated on {data.get('report_date', 'N/A')}</p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <h3>Total Responses</h3>
                <div class="value">{data.get('total_responses', 0)}</div>
            </div>
            <div class="metric">
                <h3>Average Rating</h3>
                <div class="value">{data.get('average_rating', 0):.1f}</div>
            </div>
            <div class="metric">
                <h3>Satisfaction</h3>
                <div class="value">{data.get('satisfaction_percentage', 0):.1f}%</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Key Insights</h2>
            <ul>
                {''.join([f'<li>{insight}</li>' for insight in data.get('insights', [])])}
            </ul>
        </div>
    </body>
    </html>
    """