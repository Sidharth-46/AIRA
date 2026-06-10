# Architecture

AIRA uses a clean, microservices-inspired monolithic architecture managed via Docker.

## 1. Multi-Agent Workflow
AIRA utilizes four distinct agents coordinated by the `Orchestrator`:
1. **Planner Agent**: Decomposes user intents into actionable steps.
2. **Research Agent**: Uses RAG to search the vector database and retrieve relevant context.
3. **Coder Agent**: Generates, refactors, and edits code based on the plan and context.
4. **Reviewer Agent**: Evaluates the generated code for security, style, and optimization.

## 2. Service Layer Pattern
The backend enforces a strict `Routes → Services → Agents → Ollama` pattern.
- **Routes**: Flask blueprints (`auth.py`, `workspace.py`, etc.) handling HTTP requests.
- **Services**: Business logic encapsulation (`chat_service.py`, `ollama_service.py`).
- **Models**: MongoDB schemas.

## 3. RAG Pipeline
- **Ingestion**: Documents are parsed by `document_processor.py`, chunked by `chunker.py` (using `langchain`), and embedded.
- **Storage**: Vector embeddings are stored in a persistent local `ChromaDB` instance.
- **Retrieval**: Agents query `vector_store.py` to inject relevant code snippets directly into the LLM context.

## 4. Memory Pipeline
- Short-term conversation history is maintained via ContextManager.
- Long-term memory uses `preference_extractor.py` to identify user traits and saves them to MongoDB via `memory_manager.py`.

## 5. Ollama Integration
Everything is locally hosted. `OllamaProvider` acts as the standard interface for LLM completions, streaming, and embeddings.
