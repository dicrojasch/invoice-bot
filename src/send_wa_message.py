import requests
import os
from dotenv import load_dotenv

load_dotenv()

class WhatsAppClient:
    def __init__(self, api_url=None, api_key=None, group_id=None):
        """
        Initializes the WhatsAppClient with API configuration.
        Defaults to environment variables if not provided.
        """
        self.api_url = api_url or os.getenv('WA_API_URL')
        self.api_key = api_key or os.getenv('API_WA_KEY')
        self.group_id = group_id or os.getenv('WHATSAPP_GROUP_ID')

    def send_message(self, phone, message, image_path=None):
        """Sends a text message and optionally an image via file path."""
        headers = {
            "x-api-key": self.api_key
        }
        
        payload = {
            "phone": phone,
            "message": message,
            "imagePath": image_path
        }
        
        try:
            r = requests.post(f"{self.api_url}/send", json=payload, headers=headers)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def send_message_base64(self, phone, message, image_base64):
        """Sends a text message and an image via base64 encoded string."""
        if image_base64 is None:
            return self.send_message(phone, message)

        headers = {
            "x-api-key": self.api_key
        }
        
        payload = {
            "phone": phone,
            "message": message,
            "imageBase64": image_base64
        }
        
        try:
            r = requests.post(f"{self.api_url}/send-base64", json=payload, headers=headers)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

# Usage examples:
if __name__ == "__main__":
    client = WhatsAppClient()
    
    # Example: Send message from file (commented out)
    # print(client.send_message(client.group_id, "Test from Python", "/path/to/image.png"))

    file_path = '/home/diego/repos/invoice-bot/src/test_img_base64'

    try:
        with open(file_path, 'r') as file:
            # .read() gets the content, .strip() removes any hidden spaces or newlines
            image_base64 = file.read().strip()
        
        print(f"Success! Base64 string loaded. Length: {len(image_base64)} characters.")
        
        print(client.send_message_base64(client.group_id, "Test from Python Class", image_base64))
        
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except Exception as e:
        print(f"Error: {e}")