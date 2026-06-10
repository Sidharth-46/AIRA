import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentChunker:
    """
    Handles chunking of text documents for vector storage.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.default_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Specialized splitters can be added here (e.g., for code)
        self.code_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""]
        )

    def chunk_text(self, text: str, file_name: str = "") -> list[str]:
        """
        Splits text into chunks, using a specialized splitter if a code file is detected.
        """
        ext = os.path.splitext(file_name)[1].lower()
        code_extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".json", ".yaml", ".yml"]
        
        if ext in code_extensions:
            return self.code_splitter.split_text(text)
        
        return self.default_splitter.split_text(text)
