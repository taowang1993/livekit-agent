import os
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import openai, deepgram, noise_cancellation, silero, groq, google
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        instructions = os.getenv("ASSISTANT_INSTRUCTIONS", "You are a helpful voice AI assistant.")
        super().__init__(instructions=instructions)

def get_stt():
    provider = os.getenv("STT_PROVIDER", "deepgram")
    if provider == "deepgram":
        kwargs = {
            "model": os.getenv("STT_MODEL", "nova-3"),
            "api_key": os.getenv("STT_API_KEY")
        }
        language = os.getenv("STT_LANGUAGE")
        if language:
            kwargs["language"] = language
        return deepgram.STT(**kwargs)
    elif provider == "openai":
        language = os.getenv("STT_LANGUAGE")
        if not language or language == "multi":
            language = "en"
        return openai.STT(
            model=os.getenv("STT_MODEL", "tts-1"),
            language=language,
            api_key=os.getenv("STT_API_KEY"),
            base_url=os.getenv("STT_BASE_URL"),
        )
    elif provider == "groq":
        language = os.getenv("STT_LANGUAGE")
        kwargs = {
            "model": os.getenv("STT_MODEL", "whisper-large-v3-turbo"),
            "api_key": os.getenv("STT_API_KEY"),
            "base_url": os.getenv("STT_BASE_URL", "https://api.groq.com/openai/v1"),
        }
        if language and language != "multi":
            kwargs["language"] = language
        return groq.STT(**kwargs)
    # Add more providers as needed
    raise NotImplementedError(f"STT provider {provider} not supported.")

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai")
    if provider == "openai":
        return openai.LLM(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL")
        )
    elif provider == "google":
        # Gemini Live API (beta)
        return google.beta.realtime.RealtimeModel(
            model=os.getenv("LLM_MODEL", "gemini-2.0-flash-exp"),
            api_key=os.getenv("GOOGLE_API_KEY"),
            voice=os.getenv("LLM_VOICE", "Puck"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.8")),
            instructions=os.getenv("ASSISTANT_INSTRUCTIONS", "You are a helpful voice AI assistant."),
            modalities=os.getenv("LLM_MODALITIES", "AUDIO").split(",") if os.getenv("LLM_MODALITIES") else ["AUDIO"],
            vertexai=os.getenv("LLM_VERTEXAI", "False").lower() == "true",
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )
    # Add more providers as needed
    raise NotImplementedError(f"LLM provider {provider} not supported.")

def get_tts():
    provider = os.getenv("TTS_PROVIDER", "openai")
    if provider == "openai":
        return openai.TTS(
            model=os.getenv("TTS_MODEL", "tts-1"),
            voice=os.getenv("TTS_VOICE", "en-US-AvaMultilingualNeural"),
            api_key=os.getenv("TTS_API_KEY"),
            base_url=os.getenv("TTS_BASE_URL"),
            speed=float(os.getenv("TTS_SPEED", "1.0")),
        )
    elif provider == "deepgram":
        return deepgram.TTS(
            model=os.getenv("TTS_MODEL", "sonic-2"),
            voice=os.getenv("TTS_VOICE"),
            api_key=os.getenv("TTS_API_KEY")
        )
    # Add more providers as needed
    raise NotImplementedError(f"TTS provider {provider} not supported.")

def get_gemini_modalities():
    valid = {"AUDIO", "TEXT"}
    env_val = os.getenv("LLM_MODALITIES")
    if env_val:
        vals = [v.strip().upper() for v in env_val.split(",") if v.strip()]
        filtered = [v for v in vals if v in valid]
        if filtered:
            return filtered
    return None

async def entrypoint(ctx: agents.JobContext):
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    if llm_provider == "google":
        # Use Gemini Live API as a realtime model (handles speech directly)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable is required for Gemini Live API integration.")
        gemini_kwargs = {
            'model': os.getenv("LLM_MODEL", "gemini-2.0-flash-exp"),
            'api_key': google_api_key,
            'voice': os.getenv("LLM_VOICE", "Puck"),
            'instructions': os.getenv("ASSISTANT_INSTRUCTIONS", "You are a helpful voice AI assistant."),
            'vertexai': os.getenv("LLM_VERTEXAI", "False").lower() == "true",
        }
        # Only add temperature if set and valid
        temp = os.getenv("LLM_TEMPERATURE")
        if temp:
            try:
                gemini_kwargs['temperature'] = float(temp)
            except Exception:
                pass
        # Only add modalities if set and valid
        modalities = get_gemini_modalities()
        if modalities:
            gemini_kwargs['modalities'] = modalities
        # Only add project/location if set
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if project:
            gemini_kwargs['project'] = project
        location = os.getenv("GOOGLE_CLOUD_LOCATION")
        if location:
            gemini_kwargs['location'] = location
        session = AgentSession(
            llm=google.beta.realtime.RealtimeModel(**gemini_kwargs)
        )
        await session.start(
            room=ctx.room,
            agent=Assistant(),
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )
    else:
        session = AgentSession(
            stt=get_stt(),
            llm=get_llm(),
            tts=get_tts(),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
        )
        await session.start(
            room=ctx.room,
            agent=Assistant(),
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )

    await ctx.connect()
    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )

import logging

def run_agent():
    # Configure logging for production
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    # Set load_threshold to 1.0 to avoid false 'at capacity' in constrained environments
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            load_threshold=1.0,  # Allow up to 100% load before marking unavailable
        )
    )

if __name__ == "__main__":
    run_agent()
