import os
import sys
from google.oauth2.service_account import Credentials
import requests

scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.readonly']
service_account_file = 'service_account.json'

creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)

import google.auth.transport.requests
request = google.auth.transport.requests.Request()
creds.refresh(request)

spreadsheet_id = "1BW64-NPp563ga3JlT4_oLKY8FAJ685Mx-llMLQLv0Y4"
sheet_name = "View Gas"
cell_label = "A1" # I'll just check what the API returns

url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?ranges={sheet_name}!{cell_label}&includeGridData=true"
headers = {'Authorization': f'Bearer {creds.token}'}
response = requests.get(url, headers=headers)
print(response.json())
