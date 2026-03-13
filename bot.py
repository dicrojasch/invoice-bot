import os
from dotenv import load_dotenv
import json
import sys
import stat

# Import our new modules
from google_drive_client import GoogleDriveClient
from gemini_client import GeminiClient
import google_sheets_client

# --- Configuration Section ---
def check_env_permissions(env_file='.env'):
    """Checks if the .env file has secure permissions (chmod 600)."""
    if not os.path.exists(env_file):
        return # Skip if file doesn't exist (e.g. using real env vars)

    # st_mode contains the file type and permissions
    file_stats = os.stat(env_file)
    # Mask to get only the permission bits
    permissions = stat.S_IMODE(file_stats.st_mode)
    
    # Check if permissions are exactly 600 (owner read/write only)
    if permissions != 0o600:
        print(f"ERROR: Secure permissions required for {env_file}.")
        print(f"Current permissions: {oct(permissions)}")
        print(f"Please run: chmod 600 {env_file}")
        sys.exit(1)

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
    print("1. Authenticating Google Services...")
    # Authenticate Drive and Sheets using the new modules
    drive_client = GoogleDriveClient(SERVICE_ACCOUNT_FILE, SCOPES)
    gc = google_sheets_client.authenticate_sheets(SERVICE_ACCOUNT_FILE, SCOPES)
    

    all_files = drive_client.list_files_by_relative_path("1ZysWGtJTAcYhqu8Af92mP37VccBuF6P8", "2026/03/mediciones_energia")

    # Find the files that contain "202" or "203" in their names
    target_files = [f for f in all_files if "203" in f['name'] or "202" in f['name']]
    
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
        extracted_data = gemini.extract_data_energy_measurement_202_203(
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

if __name__ == '__main__':
    main()