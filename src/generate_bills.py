import os
from dotenv import load_dotenv
import json
import sys

# Import our new modules
from utils import check_env_permissions
from google_drive_client import GoogleDriveClient
from gemini_client import GeminiClient
from google_sheets_client import GoogleSheetsClient
from send_wa_message import WhatsAppClient

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
SPREADSHEET_ID = os.getenv('TARGET_SPREADSHEET_ID')

# Scopes define the level of access we are requesting from Google APIs
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]

def main(year_to_set, month_to_set, validate=True):
    os.makedirs("output", exist_ok=True)
    print("1. Authenticating Google Services...")
    # Authenticate Drive and Sheets using the new modules
    sheets_client = GoogleSheetsClient(SERVICE_ACCOUNT_FILE, SCOPES)
    client = WhatsAppClient()
    destination = None

    bills = sheets_client.get_all_records_for_bill(SPREADSHEET_ID)

    for bill in bills:          
        if validate:
            destination = bill['validation']
        else:
            destination = bill['phone_responsible']

        bill_type = bill['bill']
        view_sheet_name = bill['sheet']

        cell_year = bill['parameters']['year']
        cell_month = bill['parameters']['month']
        
        property_to_set = None
        prefix = "" 
        if 'property' in bill['fixed_parameters'].keys(): 
            property_to_set = bill['fixed_parameters']['property'] if bill['fixed_parameters']['property'] else None
            prefix = f"{bill['fixed_parameters']['property']} - " if bill['fixed_parameters']['property'] else ""

        cell_property = None
        if 'property' in bill['parameters'].keys():
            cell_property = bill['parameters']['property'] if bill['parameters']['property'] else None
        
        parameters = f"{'(year=' + year_to_set if year_to_set else ''} {', month=' + month_to_set if month_to_set else ''} {', property=' + property_to_set + ")" if property_to_set else ''}"
        parameters = "with parameters " + parameters if len(parameters.strip()) > 0 else ""
        
        print(f"\n")
        print(f"2. Starting for '{view_sheet_name}' {parameters}...")

        # Extract key and value list from restricted_parameter (e.g., {"property": ["101", "102"]})
        restricted_params_keys = bill.get('restricted_parameter').keys()
        skip_bill = False
        print(f"3. Checking restricted parameters for '{view_sheet_name}' {parameters}...")
        for restricted_params_key in restricted_params_keys:
            restricted_params_values = bill.get('restricted_parameter')[restricted_params_key]
            if month_to_set in restricted_params_values:
                print(f"3.1.    Found '{month_to_set}' in restricted parameter '{restricted_params_key}'. Skipping...")
                skip_bill = True
                break
            
        if skip_bill:
            continue

        print("4. {prefix}Extracting columns to text file...")

        sheets_client.update_dropdown_cell(view_sheet_name, cell_year, year_to_set)
        sheets_client.update_dropdown_cell(view_sheet_name, cell_month, month_to_set)
        if cell_property:
            sheets_client.update_dropdown_cell(view_sheet_name, cell_property, property_to_set)

        name_for_file_view = view_sheet_name.replace(" ", "_").lower()
        file_path_base = f"output/sheets/{name_for_file_view}/{year_to_set}_{month_to_set}"
        file_path = f"{file_path_base}/{name_for_file_view}"
        os.makedirs(file_path_base, exist_ok=True)
    
        title = ""
        if bill['title']:
            print("4. {prefix}Extracting title for text message...")
            for cell in bill['title']:
                if cell[0].startswith("'") and cell[0].endswith("'"):
                    title += cell[0].replace("'", "") + " "
                else:
                    title += sheets_client.get_cell_value(view_sheet_name, cell[0]) + " "
        else:
            print("4. {prefix}No title for text message...")


        resume_text = ""
        if bill['resume_text']:
            raw_data = []
            print(f"4. {prefix}Extracting resume text for text message...")
            
            # 1. First pass: Extract values and find the longest label
            for row in bill['resume_text']:
                label = sheets_client.get_cell_value(view_sheet_name, row[0]).strip().replace("\n", " ")
                value = sheets_client.get_cell_value(view_sheet_name, row[1]).strip().replace("\n", " ") if len(row) > 1 else ""
                raw_data.append((label, value))
            
            # Determine the padding based on the longest label
            if raw_data:
                max_label_len = max(len(item[0]) for item in raw_data) + 2
                
                # 2. Second pass: Create aligned lines using monospace-friendly padding
                lines = []
                for label, value in raw_data:
                    # .ljust(n, '.') adds dots until it reaches length 'n'
                    aligned_line = f"{label.ljust(max_label_len, '.')}: {value}"
                    lines.append(aligned_line)
                
                resume_text = "\n".join(lines)
        else:
            print(f"4. {prefix}No resume text for text message...")

        print(f"5. {prefix}Exporting '{view_sheet_name}' to PDF...")
        pdf_content = sheets_client.get_pdf_content(
            sheet_name=view_sheet_name
        )
            
        print(f"6. {prefix}Converting '{view_sheet_name}' PDF to Image Pixmap...")
        pix = sheets_client.convert_pdf_to_image(
            pdf_content=pdf_content,
            output_image_path=file_path + '.png'
        )
        print(f"7. {prefix}Converting '{view_sheet_name}' Image Pixmap to Base64...")
        base64_image = sheets_client.pix_to_base64(pix)

        print(f"8. {prefix}Sending to Whatsapp...")
        


        text_to_send = ""
        # 3. Final formatting logic for WhatsApp
        if title and resume_text:
            # Use triple backticks for the whole block to ensure the alignment works
            text_to_send = f"```{title}\n{'_' * len(title)}\n{resume_text}```"
        else:
            # If no resume, just send the title (or resume if title is missing)
            # Using triple backticks here is optional but keeps font consistency
            text_to_send = f"```{title or resume_text or ''}```"

        print(client.send_message_base64(destination_validation, text_to_send, base64_image)    )


if __name__ == '__main__':
    
    year_to_set = "2026"
    month_to_set = "Marzo"
    validate = True
    main(year_to_set, month_to_set, validate)