import os
from dotenv import load_dotenv
import json
import sys

# Import our new modules
from utils import check_env_permissions
from google_drive_client import GoogleDriveClient
from gemini_client import GeminiClient
from google_sheets_client import GoogleSheetsClient

# --- Configuration Section ---
check_env_permissions()
load_dotenv()

# Path to your downloaded Google Cloud Service Account JSON key
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')

# Your Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# The ID of the image file in Google Drive (found in the shareable link)
DRIVE_FILE_ID = os.getenv('DRIVE_FILE_ID')

# The ID of the Google Sheet (found in the URL: docs.google.com/spreadsheets/d/THIS_IS_THE_ID/...)
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_NAME = "gas"

# Scopes define the level of access we are requesting from Google APIs
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]

def main():
    os.makedirs("output", exist_ok=True)
    print("1. Authenticating Google Services...")
    # Authenticate Drive and Sheets using the new modules
    # drive_client = GoogleDriveClient(SERVICE_ACCOUNT_FILE, SCOPES)
    sheets_client = GoogleSheetsClient(SERVICE_ACCOUNT_FILE, SCOPES)
    

    TARGET_SPREADSHEET_ID = "1BW64-NPp563ga3JlT4_oLKY8FAJ685Mx-llMLQLv0Y4"
    TARGET_SHEET_NAME = "View Gas"
    
    # print("2. Extracting columns F and N to text file...")
    # # Column F is index 6, Column N is index 14
    # sheets_client.extract_columns_to_text(
    #     spreadsheet_id=TARGET_SPREADSHEET_ID,
    #     sheet_name=TARGET_SHEET_NAME,
    #     column1_index=6,
    #     column2_index=14,
    #     output_txt_path='output/columnas_F_N.txt'
    # )
    
    # print("3. Exporting 'View Gas' to PDF...")
    pdf_path = "output/view_gas.pdf"
    # sheets_client.export_sheet_to_pdf(
    #     spreadsheet_id=TARGET_SPREADSHEET_ID,
    #     sheet_name=TARGET_SHEET_NAME,
    #     output_pdf_path=pdf_path
    # )
    
    print("4. Converting 'View Gas' PDF to Image...")
    image_path = "output/view_gas.png"
    sheets_client.convert_pdf_to_image(
        pdf_path=pdf_path,
        output_image_path=image_path
    )
    # option_to_update = "Apartamento 301"
    # options = sheets_client.get_dropdown_options(TARGET_SPREADSHEET_ID, TARGET_SHEET_NAME, 'G2')
    # if option_to_update not in options:
    #     print(f"Error: '{option_to_update}' is not a valid option. Allowed values for G2 are: {options}")
    #     return
    # print(f"'{option_to_update}' in options: {option_to_update in options}")
    # sheets_client.update_dropdown_cell(TARGET_SPREADSHEET_ID, TARGET_SHEET_NAME, 'G2', option_to_update)

if __name__ == '__main__':
    main()