import os
from dotenv import load_dotenv
import json
import io
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import PIL.Image
import sys
import stat

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
    # 0o600 in octal is 384 in decimal
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

def authenticate_google_services():
    """Authenticates and returns clients for Google Drive and Google Sheets."""
    # Load credentials from the JSON file
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # Build the Drive service client
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Authorize gspread for Google Sheets
    gc = gspread.authorize(creds)
    
    return drive_service, gc

def download_image_from_drive(drive_service, file_id):
    """Downloads a file from Google Drive into memory and returns a PIL Image."""
    request = drive_service.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)
    
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download Progress: {int(status.progress() * 100)}%.")
        
    # Reset the stream position to the beginning before reading
    file_stream.seek(0)
    return PIL.Image.open(file_stream)

def extract_data_with_gemini(image):
    """Sends the image to Gemini and asks for specific data formatted as JSON."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    # Strict prompt to ensure we get a clean JSON response that Python can parse easily
    prompt = """
    Analyze this water bill image. Extract the following 4 values:
    1. Fecha, Lectura y Tipo (Datos de medicion) (values from two rows) 
    2. Concepto and Subtotal (include valor facturas vencidas)
    3. Total a Pagar
    4. Fecha Pago oportuno
    
    Respond ONLY with a valid JSON object. Do not include markdown formatting or backticks.
    Use these exact keys: "fechas", "concepto", "costo", "fecha_pago_oportuno".
    Keep the monetary values as clean numbers (e.g., "245713.39") and consumption as just the number (e.g., "73").
    Concepto is a list of objects with keys: "CONSUMO GAS", "FIJO", "AJUSTE DECENA"
    Costo Total used to be with no decimals
    """
    
    response = model.generate_content([prompt, image])
    
    try:
        # Clean potential markdown formatting (like ```json ... ```) just in case
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        data = json.loads(clean_text)
        return data
    except json.JSONDecodeError:
        print("Error: Could not parse Gemini response as JSON.")
        print("Raw response:", response.text)
        return None

def upload_to_sheets(gc, spreadsheet_id, sheet_name, data):
    """Appends the extracted data as a new row in the specified Google Sheet."""
    # Open the target spreadsheet and select the specific tab
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.worksheet(sheet_name)
    
    # Prepare the list of values matching your columns (assuming A, B, C, D)
    row = [
        data.get('fechas', ''),
        data.get('concepto', ''),
        data.get('costo', ''),
        data.get('fecha_pago_oportuno', '')
    ]
    
    # Append the row to the first available empty row
    worksheet.append_row(row)
    print("Success: Data uploaded to Google Sheets!")

def main():
    print("1. Authenticating Google Services...")
    drive_service, gc = authenticate_google_services()
    
    print("2. Downloading image from Google Drive...")
    image = download_image_from_drive(drive_service, DRIVE_FILE_ID)
    
    print("3. Extracting data using Google Gemini...")
    # extracted_data = extract_data_with_gemini(image)
    extracted_data = json.loads('{"fechas": "23 Ene. 2026", "concepto":"CONSUMO GAS : 73990.89   FIJO", "costo": "78180.44", "fecha_pago_oportuno": "12 Mar. 2026"}')
    
    if extracted_data:
        print("--- Extracted Data ---")
        print(json.dumps(extracted_data, indent=2))
        
        print("4. Uploading extracted data to Google Sheets...")
        upload_to_sheets(gc, SPREADSHEET_ID, SHEET_NAME, extracted_data)

if __name__ == '__main__':
    main()