import os
from dotenv import load_dotenv
from google_sheets_client import GoogleSheetsClient

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def test_dropdown_options():
    client = GoogleSheetsClient(SERVICE_ACCOUNT_FILE, SCOPES)
    
    # Using the spreadsheet ID and sheet name from bot.py
    spreadsheet_id = "1BW64-NPp563ga3JlT4_oLKY8FAJ685Mx-llMLQLv0Y4"
    sheet_name = "View Gas"
    cell_label = "G2" # User updated this cell in bot.py, likely a dropdown
    
    print(f"Testing get_dropdown_options for {sheet_name}!{cell_label}...")
    options = client.get_dropdown_options(spreadsheet_id, sheet_name, cell_label)
    
    if options is not None:
        print(f"Options found: {options}")
    else:
        print("Failed to retrieve options.")

if __name__ == "__main__":
    test_dropdown_options()
