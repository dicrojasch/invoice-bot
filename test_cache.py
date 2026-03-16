import os
from dotenv import load_dotenv
from src.google_sheets_client import GoogleSheetsClient

load_dotenv()
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('TARGET_SPREADSHEET_ID')

def test():
    client = GoogleSheetsClient(SERVICE_ACCOUNT_FILE, SCOPES)
    print("Testing get_all_records_for_bill...")
    records = client.get_all_records_for_bill()
    print(f"Got {len(records)} records.")
    
    # Simulate multiple cell accesses to see if quota error triggers
    if records:
        sheet = records[0].get('sheet')
        if sheet:
            print(f"Testing rapid get_cell_value on sheet: {sheet}")
            for i in range(1, 20):
                val = client.get_cell_value(sheet, f"A{i}")
            print("Done rapid get_cell_value testing.")
            
if __name__ == '__main__':
    test()
