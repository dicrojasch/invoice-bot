import gspread
from google.oauth2.service_account import Credentials
import requests
import fitz  # PyMuPDF

class GoogleSheetsClient:
    def __init__(self, service_account_file, scopes):
        """Authenticates and initializes the Google Sheets client."""
        self.creds = Credentials.from_service_account_file(
            service_account_file, scopes=scopes)
        self.gc = gspread.authorize(self.creds)

    def upload_to_sheets(self, spreadsheet_id, sheet_name, data):
        """Appends the extracted data as a new row in the specified Google Sheet."""
        # Open the target spreadsheet and select the specific tab
        sh = self.gc.open_by_key(spreadsheet_id)
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

    def get_pdf_content(self, spreadsheet_id, sheet_name):
        """Retrieves PDF content for a specific tab from Google Sheets."""
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=pdf&gid={worksheet.id}"
        
        import google.auth.transport.requests
        request = google.auth.transport.requests.Request()
        self.creds.refresh(request)
        headers = {'Authorization': f'Bearer {self.creds.token}'}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Error downloading PDF: {response.status_code} - {response.text}")
            return None

    def save_pdf_to_file(self, content, output_pdf_path):
        """Saves PDF content to a local file."""
        if content:
            with open(output_pdf_path, 'wb') as f:
                f.write(content)
            print(f"Success: PDF saved to {output_pdf_path}")
            return True
        return False

    def export_sheet_to_pdf(self, spreadsheet_id, sheet_name, output_pdf_path):
        """Exports a specific tab to a PDF file and downloads it locally."""
        content = self.get_pdf_content(spreadsheet_id, sheet_name)
        if content:
            return self.save_pdf_to_file(content, output_pdf_path)
        return False

    def get_image_from_pdf_content(self, pdf_content):
        """Converts the first page of the PDF bytes to a pixmap, cropped to visible content."""
        try:
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            if len(doc) > 0:
                page = doc.load_page(0)
                content_rect = page.get_bboxlog()
                if content_rect:
                    full_bbox = fitz.Rect()
                    for item in content_rect:
                        full_bbox.include_rect(item[1])
                    padding = 0.1
                    full_bbox = full_bbox + (-padding, -padding, padding, padding)
                    page.set_cropbox(full_bbox)
                pix = page.get_pixmap(dpi=300)
                doc.close()
                return pix
            else:
                print("Error: Empty PDF")
                doc.close()
                return None
        except Exception as e:
            print(f"Error converting PDF to image: {e}")
            return None

    def save_image_to_file(self, pixmap, output_image_path):
        """Saves a pixmap to a local image file."""
        if pixmap:
            pixmap.save(output_image_path)
            print(f"Success: Image saved at {output_image_path}")
            return True
        return False

    def convert_pdf_to_image(self, pdf_content, output_image_path):
        """Converts PDF bytes to an image and saves it locally."""
        pix = self.get_image_from_pdf_content(pdf_content)
        if pix:
            return self.save_image_to_file(pix, output_image_path)
        return False

    def get_formatted_text_from_columns(self, spreadsheet_id, sheet_name, column1_index, column2_index):
        """
        Extracts content from two columns and returns it as a formatted string.
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        all_values = worksheet.get_all_values()
        
        lines = []
        for i, row in enumerate(all_values):
            val1 = row[column1_index - 1] if column1_index - 1 < len(row) else ""
            val2 = row[column2_index - 1] if column2_index - 1 < len(row) else ""
            if val1.strip() == "" and val2.strip() == "":
                continue
            
            separator = "\t\t"
            if i == 2:
                separator = "\t\t\t"
            
            lines.append(f"{val1.strip()}{separator}{val2.strip()}")
        
        return "\n".join(lines) + "\n"

    def save_text_to_file(self, text, output_txt_path):
        """Saves a string to a local text file."""
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(text)

    def extract_columns_to_text(self, spreadsheet_id, sheet_name, column1_index, column2_index, output_txt_path):
        """
        Extracts text from two columns (1-based index) and saves it to a local text file.
        column1_index and column2_index should be integers (e.g., 1 for A, 2 for B).
        """
        text = self.get_formatted_text_from_columns(spreadsheet_id, sheet_name, column1_index, column2_index)
        self.save_text_to_file(text, output_txt_path)
        print(f"Success: Columns {column1_index} and {column2_index} extracted to {output_txt_path}")

    def update_dropdown_cell(self, spreadsheet_id, sheet_name, cell_label, new_value):
        """
        Updates a cell in the specified Google Sheet.
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        
        worksheet.update_acell(cell_label, new_value)
        print(f"Success: Updated cell {cell_label} to '{new_value}'")
        return True

    def get_dropdown_options(self, spreadsheet_id, sheet_name, cell_label):
        """
        Retrieves the allowed values for a dropdown cell.
        Returns a list of strings if ONE_OF_LIST, otherwise returns an empty list or None.
        """
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?ranges={sheet_name}!{cell_label}&includeGridData=true"
        
        import google.auth.transport.requests
        request = google.auth.transport.requests.Request()
        self.creds.refresh(request)
        headers = {'Authorization': f'Bearer {self.creds.token}'}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching cell data: {response.status_code} - {response.text}")
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
                            print(f"Error fetching range values: {values_response.status_code} - {values_response.text}")
                            return []
                    return []
                else:
                    print(f"Note: Unhandled validation type {condition_type} for cell {cell_label}.")
                    return []
            else:
                 print(f"Note: No data validation found for {cell_label}.")
                 return []
                
        except (KeyError, IndexError):
            print(f"Note: Cell {cell_label} data not found in response.")
            return []

    def get_all_sheet_names(self, spreadsheet_id):
        """
        Returns a list of titles for all worksheets in the spreadsheet.
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheets = sh.worksheets()
        return [ws.title for ws in worksheets]
