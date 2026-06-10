# Deployment Guide

AIRA is designed to be easily deployed via Docker on any system capable of running standard Linux containers.

## Production Preparation
1. **Environment Variables**:
   Create a `.env` file from `.env.example` and set:
   - `FLASK_ENV=production`
   - `SECRET_KEY=generate_a_secure_random_string`
   - `JWT_SECRET_KEY=generate_another_secure_string`
   - `CORS_ORIGINS=https://your-domain.com`

2. **Hardware Considerations**:
   - Ensure you have sufficient GPU VRAM or unified memory (minimum 8GB, 16GB+ recommended) to run `qwen3-coder` or similar models.
   - For NVIDIA hosts, install the `nvidia-container-toolkit` to allow Docker to access the GPU.

## Deploying the Stack
1. Ensure the docker service is running.
2. Run the deployment:
   ```bash
   docker-compose -f docker-compose.yml up -d --build
   ```

## Backups
The system stores persistent data in Docker volumes mapped to your local `data/` directory:
- `data/uploads`: Raw document uploads.
- `data/embeddings`: Persistent ChromaDB vector storage.
- `data/workspace`: User generated projects and repositories.

To backup your instance, simply archive the `data/` folder and perform a `mongodump` on the `mongodb` container.
