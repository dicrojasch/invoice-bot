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
    

    TARGET_SPREADSHEET_ID = os.getenv('TARGET_SPREADSHEET_ID')
    TARGET_SHEET_NAME = "View Gas"

    all_sheet_names = sheets_client.get_all_sheet_names(TARGET_SPREADSHEET_ID)
    view_sheet_names = [sheet_name for sheet_name in all_sheet_names if sheet_name.startswith("View")]


    # for view_sheet_name in view_sheet_names:
        # process_sheet_view(view_sheet_name)

    # process_sheet_view(TARGET_SPREADSHEET_ID, "View Total", sheets_client, "2026", "Marzo", "C2", "E2")
    # process_sheet_credito_facil_view(TARGET_SPREADSHEET_ID, sheets_client, "2026", "Marzo")
    # process_sheet_gas_view(TARGET_SPREADSHEET_ID, sheets_client, "2026", "Marzo")
    # process_sheet_codensa_kwh_view(TARGET_SPREADSHEET_ID, sheets_client, "2026", "Marzo")
    # process_sheet_mediciones_101_view(TARGET_SPREADSHEET_ID, sheets_client, "2026", "Marzo")
    # process_sheet_energia_local_101_view(TARGET_SPREADSHEET_ID, sheets_client, "2026", "Marzo")
    process_sheet_energia_local_103_view(TARGET_SPREADSHEET_ID, sheets_client, "2026", "Marzo")
    

def set_year_and_month(spreadsheet_id, sheets_client, view_sheet_name, year_to_set, month_to_set, cell_year, cell_month):
    years = sorted(list(set(sheets_client.get_dropdown_options(spreadsheet_id, view_sheet_name, cell_year))))
    months = sorted(list(set(sheets_client.get_dropdown_options(spreadsheet_id, view_sheet_name, cell_month))))

    if year_to_set not in years:
        print(f"Error: '{year_to_set}' is not a valid year. Allowed values for {cell_year} are: {years}")
        return False
    if month_to_set not in months:
        print(f"Error: '{month_to_set}' is not a valid month. Allowed values for {cell_month} are: {months}")
        return False

    print(f"2. Updating dropdown cell {cell_year} to '{year_to_set}'...")
    sheets_client.update_dropdown_cell(spreadsheet_id, view_sheet_name, cell_year, year_to_set)
    print(f"3. Updating dropdown cell {cell_month} to '{month_to_set}'...")
    sheets_client.update_dropdown_cell(spreadsheet_id, view_sheet_name, cell_month, month_to_set)
    return True

def export_and_convert_sheet(spreadsheet_id, sheets_client, view_sheet_name, file_path, item_prefix=""):
    prefix = f"{item_prefix} - " if item_prefix else ""
    
    print("4. Extracting columns F and N to text file...")
    # Column F is index 6, Column N is index 14
    text = sheets_client.get_formatted_text_from_columns(
        spreadsheet_id=spreadsheet_id,
        sheet_name=view_sheet_name,
        column1_index=3,
        column2_index=5
    )

    print(f"5. {prefix}Exporting '{view_sheet_name}' to PDF...")
    pdf_content = sheets_client.get_pdf_content(
        spreadsheet_id=spreadsheet_id,
        sheet_name=view_sheet_name
    )
    if pdf_content:
        print(f"4.1. {prefix}Saving PDF content to file...")
        sheets_client.save_pdf_to_file(pdf_content, file_path + '.pdf')
        
    print(f"6. {prefix}Converting '{view_sheet_name}' PDF to Image...")
    sheets_client.convert_pdf_to_image(
        pdf_content=pdf_content,
        output_image_path=file_path + '.png'
    )

def process_sheet_with_iteration(spreadsheet_id, sheets_client, view_sheet_name, year_to_set, month_to_set, cell_year, cell_month, cell_item):
    if not set_year_and_month(spreadsheet_id, sheets_client, view_sheet_name, year_to_set, month_to_set, cell_year, cell_month):
        return

    items = sorted(list(set(sheets_client.get_dropdown_options(spreadsheet_id, view_sheet_name, cell_item))))
    
    name_for_file_view = view_sheet_name.replace(" ", "_").lower()
    file_path_base = f"output/sheets/{name_for_file_view}/{year_to_set}_{month_to_set}"
    os.makedirs(file_path_base, exist_ok=True)
    
    for item in items:
        print(f"4. {item} - Updating dropdown cell {cell_item} to '{item}'...")
        sheets_client.update_dropdown_cell(spreadsheet_id, view_sheet_name, cell_item, item)

        file_path = f"{file_path_base}/{item.replace(' ', '_').lower()}"
        export_and_convert_sheet(spreadsheet_id, sheets_client, view_sheet_name, file_path, item)

def process_sheet_view(spreadsheet_id, view_sheet_name, sheets_client, year_to_set, month_to_set, cell_year, cell_month):
    if not set_year_and_month(spreadsheet_id, sheets_client, view_sheet_name, year_to_set, month_to_set, cell_year, cell_month):
        return

    name_for_file_view = view_sheet_name.replace(" ", "_").lower()
    file_path_base = f"output/sheets/{name_for_file_view}/{year_to_set}_{month_to_set}"
    file_path = f"{file_path_base}/{name_for_file_view}"
    os.makedirs(file_path_base, exist_ok=True)
    
    export_and_convert_sheet(spreadsheet_id, sheets_client, view_sheet_name, file_path)

def process_sheet_credito_facil_view(spreadsheet_id, sheets_client, year_to_set, month_to_set):
    process_sheet_with_iteration(spreadsheet_id, sheets_client, "View credito facil", year_to_set, month_to_set, "F2", "H2", "M2")

def process_sheet_gas_view(spreadsheet_id, sheets_client, year_to_set, month_to_set):
    process_sheet_with_iteration(spreadsheet_id, sheets_client, "View Gas", year_to_set, month_to_set, "D4", "E4", "G2")

def process_sheet_codensa_kwh_view(spreadsheet_id, sheets_client, year_to_set, month_to_set):
    process_sheet_with_iteration(spreadsheet_id, sheets_client, "View Codensa kWh", year_to_set, month_to_set, "D4", "E4", "I2")

def process_sheet_mediciones_101_view(spreadsheet_id, sheets_client, year_to_set, month_to_set):
    process_sheet_view(spreadsheet_id, "View Mediciones Local 101", sheets_client, year_to_set, month_to_set, "D4", "E4")

def process_sheet_energia_local_101_view(spreadsheet_id, sheets_client, year_to_set, month_to_set):
    process_sheet_view(spreadsheet_id, "View Energia Local 101", sheets_client, year_to_set, month_to_set, "D4", "E4")

def process_sheet_energia_local_103_view(spreadsheet_id, sheets_client, year_to_set, month_to_set):
    process_sheet_view(spreadsheet_id, "View Energia Local 103", sheets_client, year_to_set, month_to_set, "D4", "E4")


if __name__ == '__main__':
    main()