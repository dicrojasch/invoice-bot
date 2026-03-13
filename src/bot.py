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
    
    # --- PREVIOUS EXECUTION (COMMENTED OUT) ---
    '''
    all_files = drive_client.list_files_by_relative_path("1ZysWGtJTAcYhqu8Af92mP37VccBuF6P8", "2026/03/mediciones_energia")

    # Find the files that contain "202" or "203" in their names
    # target_files = [f for f in all_files if "203" in f['name'] or "202" in f['name']]
    target_files = [f for f in all_files if "kwh_piso2" in f['name']]
    
    if not target_files:
        print("Error: No files found containing '202' or '203' in their names.")
        return

    print(f"2. Downloading {len(target_files)} images from Google Drive...")
    image = [drive_client.download_image_from_drive(f['id']) for f in target_files]
    extracted_data_files = []
    for target_file in target_files:
        image = drive_client.download_image_from_drive(target_file['id'])
        # print("2. Downloading image from Google Drive...")
        # image = drive_client.download_image_from_drive(DRIVE_FILE_ID)
        
        print("3. Extracting energy data using Google Gemini...")
        gemini = GeminiClient(GEMINI_API_KEY)
        
        # Use the found target file
        extracted_data = gemini.extract_data_energy_measurement_codensa_kwh(
            image, 
            target_file['name'],
            file_date=target_file.get('originalTime')
        )
        
        # # Placeholder for testing as in the original code
        # extracted_data = json.loads('{"fechas": "23 Ene. 2026", "concepto":"CONSUMO GAS : 73990.89   FIJO", "costo": "78180.44", "fecha_pago_oportuno": "12 Mar. 2026"}')
        
        if extracted_data:
            print("--- Extracted Data ---")
            print(json.dumps(extracted_data, indent=2))
            extracted_data_files.append(extracted_data)
        
    #     print("4. Uploading extracted data to Google Sheets...")
    #     google_sheets_client.upload_to_sheets(gc, SPREADSHEET_ID, SHEET_NAME, extracted_data)
    '''

    # --- NEW EXECUTION FOR VIEW GAS ---
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