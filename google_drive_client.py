import io
import PIL.Image
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class GoogleDriveClient:
    def __init__(self, service_account_file, scopes):
        """Authenticates and initializes the Google Drive service client."""
        creds = Credentials.from_service_account_file(
            service_account_file, scopes=scopes)
        self.service = build('drive', 'v3', credentials=creds)

    def download_image_from_drive(self, file_id):
        """Downloads a file from Google Drive into memory and returns a PIL Image."""
        request = self.service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download Progress: {int(status.progress() * 100)}%.")
            
        # Reset the stream position to the beginning before reading
        file_stream.seek(0)
        return PIL.Image.open(file_stream)

    def get_file_metadata(self, file_id, fields='id, name, mimeType, createdTime, size'):
        """Retrieves metadata for a specific file."""
        return self.service.files().get(fileId=file_id, fields=fields).execute()

    def get_folder_id_by_name(self, parent_id, folder_name):
        # Query to find a specific folder within a parent folder
        # We include 'trashed = false' to ignore deleted folders
        query = (
            f"'{parent_id}' in parents and "
            f"name = '{folder_name}' and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"trashed = false"
        )
        
        response = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        
        files = response.get('files', [])
        if not files:
            return None
            
        return files[0].get('id')

    def list_files_by_relative_path(self, base_folder_id, relative_path):
        current_folder_id = base_folder_id
        
        # Traverse the relative path step by step
        if relative_path and relative_path.strip() != "":
            # Split the path by '/' and ignore empty strings
            path_parts = [part for part in relative_path.strip('/').split('/') if part]
            
            for part in path_parts:
                # Find the ID of the next subfolder in the path
                next_folder_id = self.get_folder_id_by_name(current_folder_id, part)
                
                if not next_folder_id:
                    print(f"Error: Subfolder '{part}' was not found in the current path.")
                    return []
                    
                # Move down the hierarchy
                current_folder_id = next_folder_id
                
        # At this point, current_folder_id is the ID of the target directory.
        # We can now list all its files.
        all_files = []
        page_token = None
        
        while True:
            # Query to get all files in the target folder, ignoring trashed items
            search_query = f"'{current_folder_id}' in parents and trashed = false"
            
            response = self.service.files().list(
                q=search_query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, createdTime, imageMediaMetadata)',
                pageToken=page_token
            ).execute()
            
            current_page_files = response.get('files', [])
            for file in current_page_files:
                # Try to get the EXIF original datetime first, fallback to drive creation time
                metadata = file.get('imageMediaMetadata', {})
                original_time = metadata.get('time')
                
                # If 'time' exists in EXIF, use it. Otherwise use Drive's createdTime
                if original_time:
                    # 'time' is usually formatted as 'YYYY:MM:DD HH:MM:SS'
                    # We can reformat it to match Google Drive's format or just use it raw
                    # Let's clean it up slightly to match ISO 8601 look so it's consistent
                    display_time = original_time.replace(':', '-', 2).replace(' ', 'T')
                else:
                    display_time = file.get('createdTime')
                    
                print(f"File Name: {file.get('name')} | File ID: {file.get('id')} | Type: {file.get('mimeType')} | Image DateTime: {display_time}")
                
                # We can also inject the chosen time back into the file dict so bot.py can use it
                file['originalTime'] = display_time
                # Remove the large metadata dictionary to keep the list clean
                file.pop('imageMediaMetadata', None)
                all_files.append(file)
                
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
                
        return all_files
