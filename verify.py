from google.oauth2 import service_account

# Path to your downloaded JSON key
KEY_PATH = 'service_account.json'

def verify_identity():
    try:
        # Load credentials from the JSON file
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
        
        # Extract the client email from the credentials object
        bot_email = credentials.service_account_email
        project_id = credentials.project_id
        
        print("--- Authentication Successful ---")
        print(f"Service Account Email: {bot_email}")
        print(f"Project ID: {project_id}")
        print("Now, make sure to share your Google Sheet with this email!")
        
    except Exception as e:
        print(f"Authentication Failed: {e}")

if __name__ == "__main__":
    verify_identity()