import os
from dotenv import load_dotenv
import json
import sys
import stat

# Import our new modules
import google_drive_client
import gemini_client
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
    drive_service = google_drive_client.authenticate_drive(SERVICE_ACCOUNT_FILE, SCOPES)
    gc = google_sheets_client.authenticate_sheets(SERVICE_ACCOUNT_FILE, SCOPES)
    


    
    # print("2. Downloading image from Google Drive...")
    # image = google_drive_client.download_image_from_drive(drive_service, DRIVE_FILE_ID)
    
    # print("3. Extracting data using Google Gemini...")
    # gemini_client.configure_gemini(GEMINI_API_KEY)
    # # extracted_data = gemini_client.extract_data_with_gemini(image)
    
    # # Placeholder for testing as in the original code
    # extracted_data = json.loads('{"fechas": "23 Ene. 2026", "concepto":"CONSUMO GAS : 73990.89   FIJO", "costo": "78180.44", "fecha_pago_oportuno": "12 Mar. 2026"}')
    
    # if extracted_data:
    #     print("--- Extracted Data ---")
    #     print(json.dumps(extracted_data, indent=2))
        
    #     print("4. Uploading extracted data to Google Sheets...")
    #     google_sheets_client.upload_to_sheets(gc, SPREADSHEET_ID, SHEET_NAME, extracted_data)

if __name__ == '__main__':
    main()