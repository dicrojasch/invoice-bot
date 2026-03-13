import os
from dotenv import load_dotenv
from google_sheets_client import GoogleSheetsClient

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def test_get_all_sheets():
    client = GoogleSheetsClient(SERVICE_ACCOUNT_FILE, SCOPES)
    spreadsheet_id = "1BW64-NPp563ga3JlT4_oLKY8FAJ685Mx-llMLQLv0Y4"
    
    print(f"Testing get_all_sheet_names for spreadsheet {spreadsheet_id}...")
    try:
        sheet_names = client.get_all_sheet_names(spreadsheet_id)
        print(f"Sheet names found: {sheet_names}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_get_all_sheets()
