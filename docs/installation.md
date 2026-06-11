# Installation Guide

## Prerequisites
- **Docker Desktop**: Required to orchestrate the MongoDB, Ollama, Backend, and Frontend containers.
- **Git**: To clone the repository.

## Hardware Requirements
- **Development System (Mac)**: Apple Silicon (M-series), 16GB Unified Memory recommended.
- **Secondary Testing (Windows)**: NVIDIA GPU with CUDA support (e.g., GTX 1650 4GB VRAM).

## Local Setup (Docker)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sidharth-46/AIRA
   cd AIRA
   ```

2. **Run Initialization Scripts**
   This will create your `.env` file and generate necessary `data/` and `logs/` folders.
   - **Windows**: `.\scripts\setup.ps1`
   - **macOS/Linux**: `./scripts/setup.sh`

3. **Start the Stack**
   ```bash
   docker-compose up -d --build
   ```

4. **Verify Ollama Models**
   The system defaults to `qwen3-coder` and `nomic-embed-text`. Ensure they are pulled:
   ```bash
   docker exec -it aira-ollama-1 ollama run qwen3-coder
   docker exec -it aira-ollama-1 ollama pull nomic-embed-text
   ```

5. **Access Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000/api/health
