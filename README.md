# AIRA - Autonomous Intelligent Reasoning Agent

![AIRA Logo](public/aira-logo.png)

**Think. Reason. Build.**

AIRA is a self-hosted, multi-agent AI coding assistant and software engineering platform. It runs entirely on locally hosted open-source language models through **Ollama**, ensuring complete data privacy with **zero external AI API calls** (No OpenAI, Claude, etc.).

## 🚀 Features

- **Multi-Agent Architecture**: Planner, Research, Coder, and Reviewer agents working in tandem.
- **100% Local Inference**: Powered by Ollama (supports Apple Silicon and NVIDIA CUDA).
- **In-Browser IDE**: Monaco-based workspace with file explorer, terminal, tab management, and command palette.
- **RAG & Context Memory**: ChromaDB powered semantic codebase search and long-term user preference memory.
- **Dockerized**: Zero-config deployment via `docker-compose`.

## 🛠️ Installation

See [docs/installation.md](docs/installation.md) for full setup instructions.

### Quick Start
1. Ensure Docker Desktop is running.
2. Run the setup script for your platform:
   - Windows: `.\scripts\setup.ps1`
   - Mac/Linux: `./scripts/setup.sh`
3. Start the stack:
   ```bash
   docker-compose up --build -d
   ```
4. Open [http://localhost:3000](http://localhost:3000)

## 📚 Documentation
- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)

## 💻 Tech Stack
- **Frontend**: React, Vite, Tailwind CSS, Zustand, Monaco Editor
- **Backend**: Flask, PyMongo, JWT Extended
- **AI / DB**: Ollama, MongoDB, ChromaDB, LangChain Splitters
