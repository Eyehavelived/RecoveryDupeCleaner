"""
Helper for reading text files
"""
import typing
import extract_msg
import openpyxl
import xlrd

import pdfplumber
from docx import Document


class TextReaderHelper:
    """
    Helper for reading text Files
    """
    def read_file(self, path, extension) -> str:
        """
        Helper method for reading files and returns the stringified value of its contents
        """
        if (extension == "doc" or extension == "docx"):
            return self.read_doc(path)
        elif (extension == "xls" or extension == "xlsx"):
            return self.read_xls(path, extension)
        elif extension == "msg":
            return self.read_msg
        elif extension == "pdf": 
            return self.read_pdf
        elif extension == "txt":
            return self.read_txt
        else:
            raise RuntimeError(f"Unexpected extension received: {extension}")

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
        """
        Reads pdf files
        """
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    @staticmethod
    @error_handler
    def read_doc(path):
        """
        Reads legacy microsoft word documents
        """
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])

    @staticmethod
    @error_handler
    def read_msg(path):
        """
        Reads a msg file - likely a file export of Microsoft Outlook saved emails
        """
        msg = extract_msg.Message(path)
        return msg.body or ""

    @staticmethod
    @error_handler
    def read_xls(path, extension):
        """
        Reads an excel file as a text file to hash downstream
        """
        xls_loader = openpyxl.load_workbook if extension == "xlsx" else xlrd.open_workbook
        workbook = xls_loader(path, data_only=True)
        text = ""
        for sheet in workbook:
            for row in sheet.iter_rows(values_only=True):
                text += " ".join([str(cell) if cell is not None else "" for cell in row]) + "\n"
        return text

