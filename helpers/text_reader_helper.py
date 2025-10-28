"""
Helper for reading text files
"""
import typing
import extract_msg
import openpyxl
import xlrd

import html2text
import pdfplumber
from docx import Document

def error_handler(func):
    """
    Decorator to wrap file readers in a try/catch
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            raise FileNotFoundError(f'Failed to read file in given path: {e}')
        except Exception as e:
            raise RuntimeError(f'Unexpected Error occured: {e}')
    return wrapper

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
            return self.read_msg(path)
        elif extension == "pdf":
            return self.read_pdf(path)
        elif extension == "txt":
            return self.read_txt(path)
        elif extension == "html":
            return self.read_html(path)
        else:
            raise RuntimeError(f"Unexpected extension received: {extension}")

    @error_handler
    def read_html(self, path):
        """
        Reads a html file
        """
        with open(path, "r", encoding="utf-8") as f:
            html_content = f.read()

        return html2text.html2text(html_content)

    @error_handler
    def read_txt(self, path):
        """
        Reads a txt file
        """
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @error_handler
    def read_pdf(self, path):
        """
        Reads pdf files
        """
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    @error_handler
    def read_doc(self, path):
        """
        Reads legacy microsoft word documents
        """
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])

    @error_handler
    def read_msg(self, path):
        """
        Reads a msg file - likely a file export of Microsoft Outlook saved emails
        """
        msg = extract_msg.Message(path)
        return msg.body or ""

    @error_handler
    def read_xls(self, path, extension):
        """
        Reads an excel file as a text file to hash downstream
        """
        text = []
        if extension == "xlsx":
            workbook = openpyxl.load_workbook(path, data_only=True)
            sheets = workbook.worksheets
            for sheet in sheets:
                for row in sheet.iter_rows(values_only=True):
                    text.append(" ".join([str(cell) if cell is not None else "" for cell in row]))
        else:
            workbook = xlrd.open_workbook(path)
            for sheet in workbook.sheets():
                for row_idx in range(sheet.nrows):
                    text.append(" ".join([str(cell) for cell in sheet.row_values(row_idx)]))
        return "\n".join(text)
