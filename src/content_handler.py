import fitz  # PyMuPDF
import base64
import logging

logger = logging.getLogger(__name__)

class ContentHandler:
    """
    A utility class for handling content transformations, such as PDF to image conversion,
    string parsing, and file saving.
    """

    @staticmethod
    def parse_parameter_string(param_string):
        """Converts 'key1=val1;key2=val2' into a dictionary."""
        if not param_string or '=' not in str(param_string):
            return {}
        
        try:
            return {
                pair.split('=')[0].strip(): pair.split('=')[1].strip()
                for pair in str(param_string).split(';')
                if '=' in pair
            }
        except Exception:
            return {}

    @staticmethod
    def parse_parameter_list_string(param_string):
        """Converts 'key1=val1,val2;key2=val3' into a dictionary with lists."""
        if not param_string or '=' not in str(param_string):
            return {}
        
        try:
            return {
                pair.split('=')[0].strip(): [v.strip() for v in pair.split('=')[1].split(',')]
                for pair in str(param_string).split(';')
                if '=' in pair
            }
        except Exception:
            return {}

    @staticmethod
    def parse_nested_list(input_str):
        """Parses a nested list string like 'F3,F4;O3,O4' into [['F3', 'F4'], ['O3', 'O4']]."""
        if not input_str:
            return []
        return [item.split(',') for item in str(input_str).split(';')]

    @staticmethod
    def save_pdf_to_file(content, output_pdf_path):
        """Saves PDF content to a local file."""
        if content:
            with open(output_pdf_path, 'wb') as f:
                f.write(content)
            logger.debug(f"Success: PDF saved to {output_pdf_path}")
            return True
        return False

    @staticmethod
    def get_image_from_pdf_content(pdf_content):
        """Converts the first page of the PDF bytes to a pixmap, cropped to visible content."""
        try:
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            if len(doc) > 0:
                page = doc.load_page(0)
                content_rect = page.get_bboxlog()
                if content_rect:
                    full_bbox = fitz.Rect()
                    for item in content_rect:
                        full_bbox.include_rect(item[1])
                    padding = 0.5
                    full_bbox = full_bbox + (-padding, -padding, padding, padding)
                    page.set_cropbox(full_bbox)
                pix = page.get_pixmap(dpi=300)
                doc.close()
                return pix
            else:
                logger.debug("Error: Empty PDF")
                doc.close()
                return None
        except Exception as e:
            logger.debug(f"Error converting PDF to image: {e}")
            return None

    @staticmethod
    def pix_to_base64(pixmap):
        """Converts a fitz.Pixmap to a base64 encoded string."""
        if pixmap:
            img_bytes = pixmap.tobytes("png")
            base64_string = base64.b64encode(img_bytes).decode('utf-8')
            return base64_string
        return None

    @staticmethod
    def save_image_to_file(pixmap, output_image_path):
        """Saves a pixmap to a local image file."""
        if pixmap:
            pixmap.save(output_image_path)
            logger.debug(f"Success: Image saved at {output_image_path}")
            return True
        return False

    @staticmethod
    def convert_pdf_to_image(pdf_content, output_image_path=None):
        """Converts PDF bytes to an image pixmap."""
        pix = ContentHandler.get_image_from_pdf_content(pdf_content)
        if pix:
            if output_image_path:
                ContentHandler.save_image_to_file(pix, output_image_path)
            return pix
        return None

    @staticmethod
    def save_text_to_file(text, output_txt_path):
        """Saves a string to a local text file."""
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
