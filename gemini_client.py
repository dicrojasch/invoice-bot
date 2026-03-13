import json
from google import genai

class GeminiClient:
    def __init__(self, api_key):
        """Configures and initializes the Gemini API client."""
        self.client = genai.Client(api_key=api_key)

    def extract_data_gas_bill_with_gemini(self, image, model_name='gemini-2.5-flash'):
        """Sends the image to Gemini and asks for specific data formatted as JSON."""
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
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
        
        response = self.client.models.generate_content(
            model=model_name,
            contents=[prompt, image]
        )
        
        return self._parse_json_response(response)

    def extract_data_energy_measurement_203(self, image, file_name, file_date=None, model_name='gemini-2.5-flash'):
        """Extracts energy measurement from a photo and returns a JSON."""
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
        prompt = f"""
            Analyze this energy meter reading photo.
            Filename context: {file_name}
            Instructions for Measurement Extraction:
            The meter has 6 visible digits in total: 5 integers (black background) and 1 decimal digit (red background).
            Since this is an analog-style rolling display, numbers may appear partially scrolled or between positions.
            If a digit is between two numbers, choose the one that is most fully visible or consistent with the rolling direction 
            (the lower number unless the next digit to the right has passed '0').
            Extract the total energy measurement in kWh.
            Response Requirements:
            Respond ONLY with a valid JSON object. Do not include markdown formatting, code blocks, or backticks.
            Exact JSON Keys:
            "fecha": (string in YYYY-MM-DD format based primarily on the provided metadata date: '{file_date}', or null if unavailable)
            "nombre_archivo": (string exactly '{file_name}')
            "medicion_kwh": (number, use a dot as decimal separator)
        """
        
        # prompt = f"""
        # Analyze this energy meter reading photo. 
        # Filename context: {file_name}
        # Extract the energy measurement shown in the image in kWh.
        # Also determine the date of the reading (if visible, otherwise use current date or say 'null').
        
        # Respond ONLY with a valid JSON object. Do not include markdown formatting or backticks.
        # Use these exact keys:
        # "fecha": (string or null)
        # "nombre_archivo": (string exactly '{file_name}')
        # "medicion_kwh": (number, just the digits and decimals if any)
        # """
        
        response = self.client.models.generate_content(
            model=model_name,
            contents=[prompt, image]
        )
        
        return self._parse_json_response(response)

    def _parse_json_response(self, response):
        try:
            # Clean potential markdown formatting (like ```json ... ```) just in case
            clean_text = response.text.strip().replace('```json', '').replace('```', '')
            data = json.loads(clean_text)
            return data
        except json.JSONDecodeError:
            print("Error: Could not parse Gemini response as JSON.")
            print("Raw response:", response.text)
            return None
