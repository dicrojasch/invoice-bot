import json
import google.generativeai as genai

def configure_gemini(api_key):
    """Configures the Gemini API client."""
    genai.configure(api_key=api_key)

def extract_data_with_gemini(image, model_name='models/gemini-2.5-flash'):
    """Sends the image to Gemini and asks for specific data formatted as JSON."""
    model = genai.GenerativeModel(model_name)
    
    # Strict prompt to ensure we get a clean JSON response that Python can parse easily
    prompt = """
    Analyze this water bill image. Extract the following 4 values:
    1. Fecha, Lectura y Tipo (Datos de medicion) (values from two rows) 
    2. Concepto and Subtotal (include valor facturas vencidas)
    3. Total a Pagar
    4. Fecha Pago oportuno
    
    Respond ONLY with a valid JSON object. Do not include markdown formatting or backticks.
    Use these exact keys: "fechas", "concepto", "costo", "fecha_pago_oportuno".
    Keep the monetary values as clean numbers (e.g., "245713.39") and consumption as just the number (e.g., "73").
    Concepto is a list of objects with keys: "CONSUMO GAS", "FIJO", "AJUSTE DECENA"
    Costo Total used to be with no decimals
    """
    
    response = model.generate_content([prompt, image])
    
    try:
        # Clean potential markdown formatting (like ```json ... ```) just in case
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        data = json.loads(clean_text)
        return data
    except json.JSONDecodeError:
        print("Error: Could not parse Gemini response as JSON.")
        print("Raw response:", response.text)
        return None
