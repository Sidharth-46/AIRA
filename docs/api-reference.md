# API Reference

The AIRA backend uses a RESTful JSON API structure protected by JWT tokens.

## Base URL
`http://localhost:5000/api`

## Authentication Routes

### `POST /auth/signup`
Creates a new user.
- **Body**: `{ "email": "user@example.com", "password": "password", "username": "dev" }`
- **Response**: `{ "user": {...}, "access_token": "...", "refresh_token": "..." }`

### `POST /auth/login`
Authenticates a user.
- **Body**: `{ "email": "user@example.com", "password": "password" }`

### `GET /auth/profile`
Returns current user profile. Requires Authorization header `Bearer <token>`.

## Chat Routes

### `POST /chat/message`
Send a message to the AI agent swarm.
- **Body**: `{ "chat_id": "optional-id", "message": "build a react app" }`
- **Response**: Returns Server-Sent Events (SSE) streaming the agent workflow and final response.

## RAG & Document Routes

### `POST /documents/upload/<project_id>`
Upload and index a file using ChromaDB.
- **Form Data**: `file` (the document to upload).

### `POST /documents/search/<project_id>`
Semantic search.
- **Body**: `{ "query": "database connection logic", "top_k": 5 }`
- **Response**: List of chunks and metadata.

## Ollama Control

### `GET /models/status`
Check Ollama connection and current loaded model.

### `GET /models/list`
List available Ollama models.
