import os
import uuid
from typing import List, Dict, Any

from rag.chunker import DocumentChunker
from rag.document_processor import DocumentProcessor
from rag.vector_store import VectorStore
from utils.logger import get_logger

logger = get_logger("rag.engine")

class RAGEngine:
    """
    Orchestrates the Retrieval-Augmented Generation pipeline.
    """
    
    def __init__(self):
        self.chunker = DocumentChunker()
        self.vector_store = VectorStore()
        
    def index_file(self, project_id: str, file_path: str, file_name: str = None) -> int:
        """
        Process, chunk, and embed a single file into the vector store.
        Returns the number of chunks added.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return 0
            
        name = file_name or os.path.basename(file_path)
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                
            text = DocumentProcessor.process_file(content, name)
            if not text.strip():
                return 0
                
            chunks = self.chunker.chunk_text(text, name)
            
            if not chunks:
                return 0
                
            ids = [f"{name}_{uuid.uuid4()}" for _ in range(len(chunks))]
            metadatas = [{"source": name, "project_id": str(project_id)} for _ in range(len(chunks))]
            
            self.vector_store.add_documents(
                project_id=str(project_id),
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )
            
            logger.info(f"Indexed {len(chunks)} chunks for {name}")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Failed to index {name}: {str(e)}")
            return 0

    def index_directory(self, project_id: str, directory_path: str) -> int:
        """
        Recursively index an entire directory.
        """
        total_chunks = 0
        
        # Files/dirs to ignore
        ignore_dirs = {".git", "node_modules", "venv", "__pycache__", ".next", "dist", "build"}
        ignore_exts = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".zip", ".tar", ".gz", ".mp3", ".mp4"}
        
        for root, dirs, files in os.walk(directory_path):
            # Prune ignored dirs
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ignore_exts:
                    continue
                    
                file_path = os.path.join(root, file)
                # Keep relative path for metadata
                rel_path = os.path.relpath(file_path, directory_path)
                
                chunks = self.index_file(project_id, file_path, rel_path)
                total_chunks += chunks
                
        return total_chunks

    def retrieve_context(self, project_id: str, query: str, top_k: int = 5) -> str:
        """
        Retrieve context for a query and format it for an LLM prompt.
        """
        results = self.vector_store.search(str(project_id), query, n_results=top_k)
        
        if not results:
            return ""
            
        context_parts = []
        for r in results:
            source = r["metadata"].get("source", "Unknown")
            # Distance might be used for relevance scoring or filtering if needed
            context_parts.append(f"--- File: {source} ---\n{r['document']}")
            
        return "\n\n".join(context_parts)
