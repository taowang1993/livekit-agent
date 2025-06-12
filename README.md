# LiveKit Agent

Voice AI Agent Built with the LiveKit Agent Python SDK

## Features
- LiveKit Agent is a production-ready voice AI agent that supports both the STT-LLM-TTS pipeline and the speech-to-speech pipeline.

- Health Check API: FastAPI server on port 7860 ensures Hugging Face Spaces and Docker health checks pass.

- Easy Deployment: Works on Hugging Face Spaces, Docker, or any container platform.


## Quick Start

### 1. Clone & Configure
```sh
git clone https://github.com/taowang1993/livekit-agent

cd livekit-agent

cp .env.example .env
```

### 2. Build & Run with Docker
```sh
docker buildx build --platform linux/amd64 -t {dockerhub_username}/livekit-agent:latest --push .
docker run --env-file .env -p 7860:7860 {dockerhub_username}/livekit-agent:latest
```

Or use the prebuilt docker image:
```sh
docker run --env-file .env -p 7860:7860 maxwang1993/livekit-agent:latest
```

### 3. Deploy on Hugging Face Spaces
- Set up as a Docker Space.
- Set your environment variables in the Space settings. (Select `New Secret` for keys!!!)
- Create a Dockerfile and fill in the following:

```Dockerfile
FROM {dockerhub_username}/livekit-agent:latest
```
OR

```Dockerfile
FROM maxwang1993/livekit-agent:latest
```

## Environment Variables
See `.env.example` for all required and optional settings:
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- `GOOGLE_API_KEY`, `OPENAI_API_KEY`, etc.
- `STT_PROVIDER`, `TTS_PROVIDER`, `LLM_PROVIDER`, ...

## Development
```sh
pip install -r requirements.txt
python app.py
```
- Visit [http://localhost:7860/](http://localhost:7860/) for the front page.
