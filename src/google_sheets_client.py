import gspread
from google.oauth2.service_account import Credentials
import requests
import os
import logging
from content_handler import ContentHandler

logger = logging.getLogger(__name__)

class GoogleSheetsClient:
    """
    A client for interacting with Google Sheets, providing caching,
    PDF export, and structured data extraction capabilities.
    
    Internal operations are logged at DEBUG level to maintain a clean 
    main execution output.
    """
    def __init__(self, service_account_file, scopes, spreadsheet_id=None):
        """Authenticates and initializes the Google Sheets client."""
        self.creds = Credentials.from_service_account_file(
            service_account_file, scopes=scopes)
        self.gc = gspread.authorize(self.creds)
        self.spreadsheet_id = spreadsheet_id or os.getenv('TARGET_SPREADSHEET_ID')
        self.sh = self.gc.open_by_key(self.spreadsheet_id)
        self._worksheet_cache = {}
        self._sheet_data_cache = {}

    def get_cached_worksheet(self, sheet_name, spreadsheet_id=None):
        """Retrieves a worksheet, using an internal cache to minimize API calls."""
        # Only use cache for the default spreadsheet
        if not spreadsheet_id or spreadsheet_id == self.spreadsheet_id:
            if sheet_name not in self._worksheet_cache:
                self._worksheet_cache[sheet_name] = self.sh.worksheet(sheet_name)
            return self._worksheet_cache[sheet_name]
        
        # If a different spreadsheet_id is provided, fetch it without caching
        sh = self.gc.open_by_key(spreadsheet_id)
        return sh.worksheet(sheet_name)

    def get_all_values_cached(self, sheet_name, spreadsheet_id=None):
        """Fetches all values from the sheet and caches them. Re-fetches if not cached."""
        if not spreadsheet_id or spreadsheet_id == self.spreadsheet_id:
            if sheet_name not in self._sheet_data_cache:
                worksheet = self.get_cached_worksheet(sheet_name, spreadsheet_id)
                self._sheet_data_cache[sheet_name] = worksheet.get_all_values()
            return self._sheet_data_cache[sheet_name]
        
        # For non-default spreadsheets, avoid caching to prevent memory leaks over time
        worksheet = self.get_cached_worksheet(sheet_name, spreadsheet_id)
        return worksheet.get_all_values()

    def upload_to_sheets(self, sheet_name, data, spreadsheet_id=None):
        """Appends the extracted data as a new row in the specified Google Sheet."""
        worksheet = self.get_cached_worksheet(sheet_name, spreadsheet_id=spreadsheet_id)
        
        # Prepare the list of values matching your columns (assuming A, B, C, D)
        row = [
            data.get('fechas', ''),
            data.get('concepto', ''),
            data.get('costo', ''),
            data.get('fecha_pago_oportuno', '')
        ]
        
        # Append the row to the first available empty row
        worksheet.append_row(row)
        logger.debug("Success: Data uploaded to Google Sheets!")

    def get_all_records_for_bill(self, spreadsheet_id=None):
        sheet_name = "bills"
        worksheet = self.get_cached_worksheet(sheet_name, spreadsheet_id=spreadsheet_id)
        data_records = worksheet.get_all_records()

        # 2. Process the records to expand columns I and J
        for row in data_records:
            # Expand 'parameters' column (Column I)
            row['parameters'] = ContentHandler.parse_parameter_string(row.get('parameters', ''))
            # Expand 'fixed_parameters' column (Column J)
            row['fixed_parameters'] = ContentHandler.parse_parameter_string(row.get('fixed_parameters', ''))
            # Expand 'title' column into nested lists (Column K)
            row['title'] = ContentHandler.parse_nested_list(row.get('title', ''))
            # Expand 'resume_text' column into nested lists (Column L)
            row['resume_text'] = ContentHandler.parse_nested_list(row.get('resume_text', ''))
            # Expand 'restricted_parameter' column into nested lists (Column M)
            row['restricted_parameter'] = ContentHandler.parse_parameter_list_string(row.get('restricted_parameter', ''))

        return data_records
            
    def get_pdf_content(self, sheet_name, spreadsheet_id=None):
        """Retrieves PDF content for a specific tab from Google Sheets."""
        actual_id = spreadsheet_id or self.spreadsheet_id
        worksheet = self.get_cached_worksheet(sheet_name, spreadsheet_id=spreadsheet_id)
        
        url = f"https://docs.google.com/spreadsheets/d/{actual_id}/export?format=pdf&gid={worksheet.id}"
        
        import google.auth.transport.requests
        request = google.auth.transport.requests.Request()
        self.creds.refresh(request)
        headers = {'Authorization': f'Bearer {self.creds.token}'}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            logger.debug(f"Error downloading PDF: {response.status_code} - {response.text}")
            return None

    def export_sheet_to_pdf(self, sheet_name, output_pdf_path, spreadsheet_id=None):
        """Exports a specific tab to a PDF file and downloads it locally."""
        content = self.get_pdf_content(sheet_name, spreadsheet_id=spreadsheet_id)
        if content:
            return ContentHandler.save_pdf_to_file(content, output_pdf_path)
        return False


    def update_dropdown_cell(self, sheet_name, cell_label, new_value, spreadsheet_id=None):
        """
        Updates a cell in the specified Google Sheet and invalidates the data cache.
        """
        worksheet = self.get_cached_worksheet(sheet_name, spreadsheet_id=spreadsheet_id)
        
        worksheet.update_acell(cell_label, new_value)
        # Clear the data cache because formulas in the sheet might recalculate based on this change
        if (not spreadsheet_id or spreadsheet_id == self.spreadsheet_id) and sheet_name in self._sheet_data_cache:
            del self._sheet_data_cache[sheet_name]
            
        logger.debug(f"Success: Updated cell {cell_label} to '{new_value}'. Formatted data cache invalidated.")
        return True

    def get_cell_value(self, sheet_name, cell_label, spreadsheet_id=None):
        """
        Retrieves the value of a specific cell from the locally cached data grid.
        This prevents massive API read quotas from single-cell lookups.
        """
        all_values = self.get_all_values_cached(sheet_name, spreadsheet_id=spreadsheet_id)
        
        try:
            row_idx, col_idx = gspread.utils.a1_to_rowcol(cell_label)
            # a1_to_rowcol returns 1-based indexes, adjust to 0-based for python lists
            r, c = row_idx - 1, col_idx - 1
            
            # Check boundaries just in case
            if r < len(all_values) and c < len(all_values[r]):
                value = all_values[r][c]
            else:
                value = ""
                
        except Exception as e:
            logger.debug(f"Error parsing cell label {cell_label}: {e}")
            value = ""
            
        logger.debug(f"Success: Retrieved value from cell {cell_label}: '{value}'")
        return value

    def get_dropdown_options(self, sheet_name, cell_label, spreadsheet_id=None):
        """
        Retrieves the allowed values for a dropdown cell.
        Returns a list of strings if ONE_OF_LIST, otherwise returns an empty list or None.
        """
        spreadsheet_id = spreadsheet_id or self.spreadsheet_id
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?ranges={sheet_name}!{cell_label}&includeGridData=true"
        
        import google.auth.transport.requests
        request = google.auth.transport.requests.Request()
        self.creds.refresh(request)
        headers = {'Authorization': f'Bearer {self.creds.token}'}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.debug(f"Error fetching cell data: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        
        try:
            cell_data = data['sheets'][0]['data'][0]['rowData'][0]['values'][0]
            if 'dataValidation' in cell_data:
                validation_rule = cell_data['dataValidation']
                condition = validation_rule.get('condition', {})
                condition_type = condition.get('type')
                
                if condition_type == 'ONE_OF_LIST':
                    return [v.get('userEnteredValue') for v in condition.get('values', [])]
                elif condition_type == 'ONE_OF_RANGE':
                    # Extract the range formula from the condition (e.g., "='View Gas'!$A$6:$A$1502")
                    range_formula = condition.get('values', [])[0].get('userEnteredValue', '')
                    if range_formula.startswith('='):
                        # Strip the '=' to get the raw range reference for the API
                        target_range = range_formula[1:] 
                        # Make a secondary API call to fetch the actual values from that range
                        values_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{target_range}"
                        values_response = requests.get(values_url, headers=headers)
                        if values_response.status_code == 200:
                            values_data = values_response.json()
                            raw_values = values_data.get('values', [])
                            # Flatten the resulting list of lists and filter out any empty string values
                            dropdown_options = [item for sublist in raw_values for item in sublist if str(item).strip()]
                            return dropdown_options
                        else:
                            logger.debug(f"Error fetching range values: {values_response.status_code} - {values_response.text}")
                            return []
                    return []
                else:
                    logger.debug(f"Note: Unhandled validation type {condition_type} for cell {cell_label}.")
                    return []
            else:
                 logger.debug(f"Note: No data validation found for {cell_label}.")
                 return []
                
        except (KeyError, IndexError):
            logger.debug(f"Note: Cell {cell_label} data not found in response.")
            return []

    def get_all_sheet_names(self, spreadsheet_id=None):
        """
        Returns a list of titles for all worksheets in the spreadsheet.
        """
        sh = self.sh if not spreadsheet_id or spreadsheet_id == self.spreadsheet_id else self.gc.open_by_key(spreadsheet_id)
        worksheets = sh.worksheets()
        return [ws.title for ws in worksheets]

