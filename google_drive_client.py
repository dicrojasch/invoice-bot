import io
import PIL.Image
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def authenticate_drive(service_account_file, scopes):
    """Authenticates and returns the Google Drive service client."""
    creds = Credentials.from_service_account_file(
        service_account_file, scopes=scopes)
    drive_service = build('drive', 'v3', credentials=creds)
    return drive_service

def download_image_from_drive(drive_service, file_id):
    """Downloads a file from Google Drive into memory and returns a PIL Image."""
    request = drive_service.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)
    
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download Progress: {int(status.progress() * 100)}%.")
        
    # Reset the stream position to the beginning before reading
    file_stream.seek(0)
    return PIL.Image.open(file_stream)
