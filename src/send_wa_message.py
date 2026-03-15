import requests
import os
from dotenv import load_dotenv

load_dotenv()

# WhatsApp API configuration
WA_API_URL = os.getenv('WA_API_URL')
API_WA_KEY = os.getenv('API_WA_KEY')
WHATSAPP_GROUP_ID = os.getenv('WHATSAPP_GROUP_ID')


def send_secure_whatsapp(phone, message, image_path=None):
    # Secure headers
    headers = {
        "x-api-key": API_WA_KEY
    }
    
    payload = {
        "phone": phone,
        "message": message,
        "imagePath": image_path
    }
    
    try:
        r = requests.post(WA_API_URL + "/send", json=payload, headers=headers)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

        

def send_secure_base64_whatsapp(phone, message, image_base64):
    # Secure headers
    headers = {
        "x-api-key": API_WA_KEY
    }
    
    if(image_base64 is None):
        send_secure_whatsapp(phone, message)

    payload = {
        "phone": phone,
        "message": message,
        "imageBase64": image_base64
    }
    
    try:
        r = requests.post(WA_API_URL + "/send-base64", json=payload, headers=headers)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# Usage examples:
if __name__ == "__main__":
    # print(send_secure_whatsapp(WHATSAPP_GROUP_ID, "Test from Python", "/home/diego/repos/wa-server/view_total.png"))
    file_path = '/home/diego/repos/invoice-bot/src/test_img_base64'

    try:
        with open(file_path, 'r') as file:
            # .read() gets the content, .strip() removes any hidden spaces or newlines
            image_base64 = file.read().strip()
        
        print(f"Success! Base64 string loaded. Length: {len(image_base64)} characters.")
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")


    print(send_secure_base64_whatsapp(WHATSAPP_GROUP_ID, "Test from Python", image_base64))