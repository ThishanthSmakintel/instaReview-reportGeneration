import asyncio
import sys
import os

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from create_pdf_report import generate_pdf

async def main():
    """Generate the report"""
    print("Starting customer feedback report generation...")
    try:
        await generate_pdf()
        print("Customer feedback report generation completed successfully!")
    except Exception as e:
        print(f"Error generating customer feedback report: {e}")

if __name__ == "__main__":
    asyncio.run(main())