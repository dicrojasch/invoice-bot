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

    def extract_data_energy_measurement_202_203(self, image, file_name, file_date=None, model_name='gemini-2.5-flash'):
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
        
        response = self.client.models.generate_content(
            model=model_name,
            contents=[prompt, image]
        )
        
        return self._parse_json_response(response)

    def extract_data_energy_measurement_102(self, image, file_name, file_date=None, model_name='gemini-2.5-flash'):
        """Extracts energy measurement from a photo and returns a JSON."""
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
        prompt = f"""
            Analyze this energy meter reading photo.
            Filename context: {file_name}
            Technical Specifications for this Meter:
            Digit Configuration: The meter has 6 rolling drums. The first 5 digits represent whole kWh (integers). The 6th digit (on the far right, typically highlighted in red or with a decimal indicator) represents tenths of a kWh (decimal).
            Rolling Logic: This is an electromechanical display. If a digit is partially rotated between two numbers:
            Choose the number that is more than 50% visible.
            If it's exactly in the middle, use the lower number, unless the digit to its immediate right has just passed from '9' to '0'.
            Extraction Task: Combine these to form a single number with one decimal place.
            Contextual Data:
            Check for any visible date in the surroundings (e.g., calendars or markings). If no clear current date is found, return null.
            Response Requirements:
            Respond ONLY with a valid JSON object. Do not include markdown formatting or backticks.
            Exact JSON Keys:
            "fecha": (string in YYYY-MM-DD format based primarily on the provided metadata date: '{file_date}', or null if unavailable)
            "nombre_archivo": (string exactly '{file_name}')
            "medicion_kwh": (number, use dot '.' as decimal separator as per JSON standards)
        """
        
        response = self.client.models.generate_content(
            model=model_name,
            contents=[prompt, image]
        )
        
        return self._parse_json_response(response)

    def extract_data_energy_measurement_103(self, image, file_name, file_date=None, model_name='gemini-2.5-flash'):
        """Extracts energy measurement from a photo and returns a JSON."""
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
        prompt = f"""
            Analyze this digital energy meter reading photo.
            Filename context: {file_name}
            CRITICAL LCD READING INSTRUCTIONS:
            This segmented LCD screen can be difficult to read due to glare. You MUST read it mechanically, character by character from left to right.
            The meter is configured as '6ent+2dec', meaning EVERY measurement row contains EXACTLY 8 numerical digits (6 large integers followed by 2 smaller decimals).
            Step-by-Step Extraction:
            Top Row (kWh): Locate the top line of numbers. Carefully read all 8 digits from left to right. Pay very close attention to differentiate between '0', '1', '5', and '9'. Do not skip any digits.
            Bottom Row (kvarh): Locate the bottom line of numbers. Carefully read all 8 digits from left to right.
            Date: Check the environment for a date.
            Response Requirements:
            Respond ONLY with a valid JSON object. Do not include markdown formatting, code blocks, or backticks.
            Use these exact JSON keys in this order:
            "raw_kwh_string": (string, type exactly the 8 digits you see on the top line, ignoring spaces and decimal points. e.g., "00105124")
            "raw_kvarh_string": (string, type exactly the 8 digits you see on the bottom line, ignoring spaces and decimal points. e.g., "00101934")
            "fecha": (string in YYYY-MM-DD format based primarily on the provided metadata date: '{file_date}', or null if unavailable)
            "nombre_archivo": (string exactly '{file_name}')
            "medicion_kwh": (number, take your 'raw_kwh_string', place a dot '.' before the last two digits, and remove leading zeros. e.g., "00105124" becomes 1051.24)
            "medicion_kvarh": (number, take your 'raw_kvarh_string', place a dot '.' before the last two digits, and remove leading zeros. e.g., "00101934" becomes 1019.34)"
        """
        
        response = self.client.models.generate_content(
            model=model_name,
            contents=[prompt, image]
        )

    def extract_data_energy_measurement_301_302(self, image, file_name, file_date=None, model_name='gemini-2.5-flash'):
        """Extracts energy measurement from a photo and returns a JSON."""
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
        prompt = f"""
            Analyze this analog energy meter reading photo.
            Filename context: {file_name}
            CRITICAL ROLLING DRUM INSTRUCTIONS:
            This meter uses electromechanical rolling drums. In this image, the drums are caught mid-roll, showing two partial digits in each column (a top number rolling out, and a bottom number rolling in).
            Format: The meter has 6 drums in total: 5 integers (black background) and 1 decimal (red background).
            Mid-Roll Reading Rule: When drums are split horizontally, the correct current reading is formed by the numbers on the top half of the display window, because the bottom numbers have not yet fully locked into position.
            Extraction: Read the 6 digits visible on the top half of the rolling drums from left to right.
            Response Requirements:
            Respond ONLY with a valid JSON object. Do not include markdown formatting, code blocks, or backticks.
            Use these exact JSON keys in this order:
            "observaciones": (string, explicitly list the numbers you see on the top half of the window, and the numbers you see on the bottom half, to justify your reading)
            "fecha": (string in YYYY-MM-DD format based primarily on the provided metadata date: '{file_date}', or null if unavailable)
            "nombre_archivo": (string exactly '{file_name}')
            "medicion_kwh": (number, use the 6 top-half digits. The first 5 are integers, the 6th is the decimal. Use a dot '.' as the decimal separator. e.g., 17941.4)
        """
        
        response = self.client.models.generate_content(
            model=model_name,
            contents=[prompt, image]
        )
        
        return self._parse_json_response(response)

    def extract_data_energy_measurement_codensa_kwh(self, image, file_name, file_date=None, model_name='gemini-2.5-flash'):
        """Extracts energy measurement from a photo and returns a JSON."""
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
        prompt = f"""
            Analyze this digital energy meter reading photo.
            Filename context: {file_name}
            CRITICAL LCD 7-SEGMENT READING INSTRUCTIONS:
            This is a seven-segment LCD screen behind a protective glass. Glare, dirt, and reflections can distort the shapes of the digits, especially the leading digit.
            Step-by-Step Extraction:
            Locate Target: Focus on the main large numeric sequence displayed on the screen.
            Geometrical Verification (Crucial for '4' vs '9'): Read each digit from left to right very carefully.
            Pay extreme attention to the very first digit on the left. In seven-segment displays, a '4' is OPEN at the top (the top horizontal segment is completely unlit). A '9' is CLOSED at the top.
            Do not let light reflections on the glass trick you into seeing a closed top segment.
            Read Remaining Digits: Extract the rest of the numbers, explicitly locating the decimal point.
            Filter Noise: Ignore smaller text or indicators like '50 A' or '1 ->' below the main numbers.
            Response Requirements:
            Respond ONLY with a valid JSON object. Do not include markdown formatting, code blocks, or backticks.
            Use these exact JSON keys in this order:
            "observaciones": (string, explicitly describe the geometry of the first digit. Example: "The first digit has an unlit top segment, meaning it is an open 4, not a 9. The rest of the digits are...")
            "fecha": (string in YYYY-MM-DD format based primarily on the provided metadata date: '{file_date}', or null if unavailable)
            "nombre_archivo": (string exactly '{file_name}')
            "medicion_kwh": (number, the extracted active energy value using a dot '.' as the decimal separator. e.g., 45002.55)
        """
        
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
