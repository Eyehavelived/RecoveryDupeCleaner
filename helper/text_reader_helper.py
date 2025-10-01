"""
"""
import os

import pdfplumber
from docx import Document


class TextReaderHelper:
    """
    Helper for reading text Files
    """
    @staticmethod
    def error_handler(func):
        """
        Decorator to wrap file readers in a try/catch
        """
        def wrapper(*args, **kwargs):
            try:
                func(args, kwargs)
            except FileNotFoundError as e:
                raise FileNotFoundError(f'Failed to read file in given path: {e}')
            except Exception as e:
                raise RuntimeError(f'Unexpected Error occured: {e}')
        return wrapper

    @staticmethod
    @error_handler
    def read_txt(path):
        """
        Reads a txt file
        """
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    @error_handler
    def read_pdf(path):
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    @staticmethod
    @error_handler
    def read_doc(path):
        
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])

