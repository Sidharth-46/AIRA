import os
from io import BytesIO

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

class DocumentProcessor:
    """
    Extracts text from various document formats (PDF, DOCX, TXT, MD, Code).
    """

    @staticmethod
    def process_file(file_content: bytes, filename: str) -> str:
        """
        Process a file's bytes and return its text content.
        """
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == ".pdf":
            return DocumentProcessor._process_pdf(file_content)
        elif ext in [".docx", ".doc"]:
            return DocumentProcessor._process_docx(file_content)
        elif ext in [".txt", ".md", ".json", ".yaml", ".yml", ".csv"] or ext in DocumentProcessor._get_code_extensions():
            return DocumentProcessor._process_text(file_content)
        else:
            # Fallback to try reading as utf-8 text
            try:
                return DocumentProcessor._process_text(file_content)
            except Exception as e:
                raise ValueError(f"Unsupported or unreadable file type: {ext}")

    @staticmethod
    def _process_pdf(file_content: bytes) -> str:
        if not PdfReader:
            raise ImportError("pypdf is required for PDF processing")
        
        reader = PdfReader(BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def _process_docx(file_content: bytes) -> str:
        if not docx:
            raise ImportError("python-docx is required for DOCX processing")
        
        doc = docx.Document(BytesIO(file_content))
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    @staticmethod
    def _process_text(file_content: bytes) -> str:
        # Try utf-8 first, fallback to others if needed
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for enc in encodings:
            try:
                return file_content.decode(enc)
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("Could not decode text file using known encodings.")

    @staticmethod
    def _get_code_extensions() -> list[str]:
        return [
            ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".h", 
            ".hpp", ".go", ".rs", ".php", ".rb", ".html", ".css", ".sh"
        ]
