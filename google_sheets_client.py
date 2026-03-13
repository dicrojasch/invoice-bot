import gspread
from google.oauth2.service_account import Credentials

def authenticate_sheets(service_account_file, scopes):
    """Authenticates and returns a gspread client."""
    creds = Credentials.from_service_account_file(
        service_account_file, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc

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
