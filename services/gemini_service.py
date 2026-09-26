"""Centralized Google Gemini Client and LLM Factory for CrewAI."""

import os
import json
from typing import Dict, Any, Optional, List
import config

try:
    from crewai import LLM
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False


class GeminiService:
    _native_client = None

    @classmethod
    def get_api_key(cls) -> str:
        api_key = config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        return api_key

    @classmethod
    def _candidate_models(cls) -> List[str]:
        """Returns ordered list of candidate models with automatic resilient fallbacks."""
        primary = config.GEMINI_MODEL or "gemini-3.7-flash"
        fallbacks = [
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.1-flash-lite",
            "gemini-3-flash-preview",
            "gemini-3.8-flash",
        ]
        seen = set()
        models = []
        for m in [primary] + fallbacks:
            if m and m not in seen:
                seen.add(m)
                models.append(m)
        return models

    @classmethod
    def get_crewai_llm(cls, temperature: float = 0.2) -> Any:
        """Returns a configured CrewAI LLM instance backed by Gemini 3.8 Flash."""
        api_key = cls.get_api_key()
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please add GEMINI_API_KEY to your .env file."
            )
        
        # Set environment variable so CrewAI's provider detects it
        os.environ["GEMINI_API_KEY"] = api_key

        if CREWAI_AVAILABLE:
            return LLM(
                model=f"gemini/{config.GEMINI_MODEL}",
                api_key=api_key,
                temperature=temperature,
            )
        return None

    @classmethod
    def get_native_client(cls) -> Optional[Any]:
        """Returns native Google GenAI client for direct fast calls or fallback."""
        if not GENAI_SDK_AVAILABLE:
            return None
        
        api_key = cls.get_api_key()
        if not api_key:
            return None
        
        if cls._native_client is None:
            cls._native_client = genai.Client(api_key=api_key)
        return cls._native_client

    @classmethod
    def generate_text(cls, prompt: str, system_instruction: str = "") -> str:
        """Direct text generation via Gemini 3.8 Flash with automatic multi-model fallback.

        Raises RuntimeError if the API key is not configured or all candidates fail.
        Always returns a str (never None).
        """
        api_key = cls.get_api_key()
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set.\n"
                "Please open the app window, click ⚙️ API Key, and paste your key."
            )

        client = cls.get_native_client()
        if not client:
            raise RuntimeError(
                "Could not initialise Gemini client. Check your GEMINI_API_KEY is valid."
            )

        last_error = None
        for model_name in cls._candidate_models():
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction or None,
                        temperature=0.2,
                    ),
                )
                if response and response.text:
                    return response.text
                return response.text or ""
            except Exception as e:
                last_error = e
                print(f"[GeminiService] Model '{model_name}' encountered error: {e}. Trying next candidate...")
                continue
        
        raise RuntimeError(f"Gemini API call failed: {last_error}")

    @classmethod
    def transcribe_audio_native(cls, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe and diarize meeting audio natively using Gemini 3.8 Flash with fallback."""
        client = cls.get_native_client()
        if not client:
            raise RuntimeError("Gemini client is not initialized or API key is missing.")

        prompt = (
            "You are a professional meeting transcription and speaker diarization engine. "
            "Please transcribe the following audio recording completely and accurately. "
            "Separate different speakers clearly, identify speaker names if spoken or label them "
            "Speaker 1, Speaker 2, etc., and include timestamps if discernible.\n"
            "Format each segment as:\n"
            "Speaker Name (or Speaker 1) [MM:SS]: Transcribed speech\n\n"
            "Ensure technical terms, names, and commitments are preserved accurately."
        )

        last_error = None
        for model_name in cls._candidate_models():
            try:
                audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
                response = client.models.generate_content(
                    model=model_name,
                    contents=[audio_part, prompt],
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                last_error = e
                print(f"[GeminiService Audio] Model '{model_name}' failed: {e}. Trying next candidate...")
                continue

        raise RuntimeError(f"Gemini Native Audio Transcription failed: {last_error}")
