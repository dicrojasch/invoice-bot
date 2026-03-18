import os
from dotenv import load_dotenv
import json
import sys
import time
import logging

# Import our new modules
from utils import check_env_permissions
from google_drive_client import GoogleDriveClient
from gemini_client import GeminiClient
from google_sheets_client import GoogleSheetsClient
from send_wa_message import WhatsAppClient
from content_handler import ContentHandler

# Logging Configuration
def setup_logging(level=logging.INFO):
    # Clear any existing handlers to allow reconfiguration
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    logging.basicConfig(
        level=level,
        format='[%(levelname)s][%(name)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class BillLoggerAdapter(logging.LoggerAdapter):
    """Adapter to add bill ID context to log messages."""
    def process(self, msg, kwargs):
        bill_id = self.extra.get('bill_id')
        prefix = f"[id={bill_id}] " if bill_id else ""
        return f"{prefix}{msg}", kwargs

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

def main(year_to_set, month_to_set, validate=True, execution_ids=None, list_only=False):
    """
    Main execution loop for generating and sending invoices.
    
    Args:
        year_to_set (str): The year to set in the spreadsheet dropdown.
        month_to_set (str): The month to set in the spreadsheet dropdown.
        validate (bool): If True, sends to validation phone; else to responsible phone.
        execution_ids (list): Optional list of id_execution to filter bills.
        list_only (bool): If True, prints available bills and exits.
    """
    os.makedirs("output", exist_ok=True)
    logger.info("Authenticating Google Services...")
    # Authenticate Drive and Sheets using the new modules
    sheets_client = GoogleSheetsClient(SERVICE_ACCOUNT_FILE, SCOPES)
    client = WhatsAppClient()
    destination = None

    bills = sheets_client.get_all_records_for_bill(SPREADSHEET_ID)

    if list_only:
        # Display a summary of all bills retrieved from the 'bills' tab
        logger.info("--- Available Bills ---")
        header = f"{'ID':<5} | {'Sheet':<20} | {'Responsible':<15} | {'Parameters'}"
        logger.info(header)
        logger.info("-" * len(header))
        for bill in bills:
            if execution_ids and str(bill.get('id_execution')) not in execution_ids:
                continue
            
            id_exec = bill.get('id_execution', 'N/A')
            sheet = bill.get('sheet', 'N/A')
            resp = bill.get('phone_responsible', 'N/A')
            params = json.dumps(bill.get('parameters', {}))
            fixed = json.dumps(bill.get('fixed_parameters', {}))
            
            logger.info(f"{id_exec:<5} | {sheet:<20} | {resp:<15} | {params} (Fixed: {fixed})")
        logger.info("-" * len(header))
        return

    for bill in bills: 
        bill_id = bill.get('id_execution')
        b_logger = BillLoggerAdapter(logger, {'bill_id': bill_id})
        
        b_logger.info(f"Starting for bill {bill_id}...")
        
        if execution_ids and str(bill_id) not in execution_ids:
            b_logger.info(f"Skipping bill {bill_id}...")
            continue

        if validate:
            destination = str(bill['validation'])
        else:
            destination = str(bill['phone_responsible'])

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
        
        b_logger.info(f"Starting for '{view_sheet_name}' {parameters}...")

        # Extract key and value list from restricted_parameter (e.g., {"property": ["101", "102"]})
        restricted_params_keys = bill.get('restricted_parameter').keys()
        skip_bill = False
        b_logger.info(f"Checking restricted parameters for '{view_sheet_name}' {parameters}...")
        for restricted_params_key in restricted_params_keys:
            restricted_params_values = bill.get('restricted_parameter')[restricted_params_key]
            if month_to_set in restricted_params_values:
                b_logger.info(f"Found '{month_to_set}' in restricted parameter '{restricted_params_key}'. Skipping...")
                skip_bill = True
                break
            
        if skip_bill:
            continue

        b_logger.info(f"{prefix}Extracting columns to text file...")

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
            b_logger.info(f"{prefix}Extracting title for text message...")
            for cell in bill['title']:
                if cell[0].startswith("'") and cell[0].endswith("'"):
                    title += cell[0].replace("'", "") + " "
                else:
                    title += sheets_client.get_cell_value(view_sheet_name, cell[0]) + " "
        else:
            b_logger.info(f"{prefix}No title for text message...")

        title = title.strip().replace("\n", " ")

        resume_text = ""
        if bill['resume_text']:
            raw_data = []
            b_logger.info(f"{prefix}Extracting resume text for text message...")
            
            # 1. First pass: Extract values and find the longest label
            for row in bill['resume_text']:
                label = sheets_client.get_cell_value(view_sheet_name, row[0]).strip().replace("\n", " ")
                value = sheets_client.get_cell_value(view_sheet_name, row[1]).strip().replace("\n", " ") if len(row) > 1 else ""
                # Format: Label in bold, then value on the next line
                # Using * for bold works in standard WhatsApp font
                raw_data.append(f"\t*{label}:*\n\t\t{value}")
            
            resume_text = "\n".join(raw_data)
        else:
            b_logger.info(f"{prefix}No resume text for text message...")
            
        text_to_send = ""
        # 3. Final formatting for WhatsApp
        if title and resume_text:
            # Since we are not using monospace anymore, a fixed-length underline works best
            underline = "—" * 15 
            text_to_send = f"*{title}*\n{underline}\n{resume_text}"
        else:
            # If no resume, just send the bold title
            text_to_send = f"*{title or resume_text or ''}*"

        b_logger.info(f"{prefix}Exporting '{view_sheet_name}' to PDF...")
        pdf_content = sheets_client.get_pdf_content(
            sheet_name=view_sheet_name
        )
            
        b_logger.info(f"{prefix}Converting '{view_sheet_name}' PDF to Image Pixmap...")
        pix = ContentHandler.convert_pdf_to_image(
            pdf_content=pdf_content
        )
        b_logger.info(f"{prefix}Converting '{view_sheet_name}' Image Pixmap to Base64...")
        base64_image = ContentHandler.pix_to_base64(pix)

        b_logger.info(f"{prefix}Sending to Whatsapp...")

        b_logger.info(f"{prefix}Sent to Whatsapp: {client.send_message_base64(destination, text_to_send, base64_image)}")
        time.sleep(5)


if __name__ == '__main__':
    import argparse
    
    # Setup command line arguments
    parser = argparse.ArgumentParser(description="Generate and send invoices via WhatsApp.")
    parser.add_argument('--year', type=str, default="2026", help="Year to set for the bills (default: 2026)")
    parser.add_argument('--month', type=str, default="Marzo", help="Month to set for the bills (default: Marzo)")
    parser.add_argument('--no-validate', action='store_false', dest='validate', help="Send bills directly to responsible phones instead of validation number")
    parser.add_argument('--ids', type=str, default="", help="Comma-separated list of id_execution to process")
    parser.add_argument('--list', action='store_true', help="Only list available bills without processing them")
    parser.add_argument('--log', type=str, default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help="Logging level (default: INFO)")
    parser.set_defaults(validate=True)
    
    args = parser.parse_args()
    
    # Reconfigure logging with the specified level
    log_level = getattr(logging, args.log.upper(), logging.INFO)
    logger = setup_logging(log_level)
    
    execution_ids = [i.strip() for i in args.ids.split(",")] if args.ids else []

    # Execution examples:
    # Default execution: +
    #   python src/generate_bills.py 
    # Custom year and month: 
    #   python src/generate_bills.py --year 2025 --month Diciembre
    # Send directly to responsible (skip validation): 
    #   python src/generate_bills.py --no-validate
    
    main(args.year, args.month, args.validate, execution_ids, args.list)