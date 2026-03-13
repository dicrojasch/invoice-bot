import google.generativeai as genai

# Remember to replace this with your actual API key
GEMINI_API_KEY = "AIzaSyAofRV4KzG45vWwJmK-eKeRFdKq4umuvao"
genai.configure(api_key=GEMINI_API_KEY)

def find_working_models():
    """
    Queries the Google API to list the exact model names 
    that are authorized for your specific API Key.
    """
    print("--- Searching for available models ---")
    
    found_any = False
    try:
        for m in genai.list_models():
            # Filter only models that support text/image generation
            if 'generateContent' in m.supported_generation_methods:
                print(f"Exact model name to use: {m.name}")
                found_any = True
                
        if not found_any:
            print("WARNING: Your API key is valid, but it doesn't have access to any generative models.")
            print("This can happen if your Google Cloud project has restrictions or due to regional blocks.")
            
    except Exception as e:
        print(f"Error connecting to the API: {e}")

if __name__ == "__main__":
    find_working_models()