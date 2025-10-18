from openai import OpenAI
import os
import logging
from pathlib import Path
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

class VoiceService:
    """
    Service for handling speech-to-text and text-to-speech using OpenAI APIs.
    Supports multiple languages for global accessibility.
    """
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'ru': 'Russian',
        'ko': 'Korean',
        'nl': 'Dutch',
        'tr': 'Turkish',
        'pl': 'Polish'
    }
    
    AVAILABLE_VOICES = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    
    def __init__(self):
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
        
        self.client = OpenAI(api_key=api_key)
        logger.info("VoiceService initialized with OpenAI client")
    
    async def speech_to_text(
        self, 
        audio_file, 
        language: Optional[str] = None,
        response_format: str = "text"
    ) -> str:
        """
        Convert speech to text using OpenAI Whisper.
        
        Args:
            audio_file: Audio file object (supports webm, mp3, mp4, mpeg, mpga, m4a, wav, webm)
            language: Optional language code (e.g., 'en', 'es'). Auto-detects if not provided.
            response_format: Response format ('text', 'json', 'verbose_json', 'srt', 'vtt')
        
        Returns:
            Transcribed text
        """
        try:
            logger.info(f"Transcribing audio, language: {language or 'auto-detect'}")
            
            # Create transcription
            params = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": response_format
            }
            
            # Add language if specified
            if language and language in self.SUPPORTED_LANGUAGES:
                params["language"] = language
            
            transcript = self.client.audio.transcriptions.create(**params)
            
            # Handle different response formats
            if response_format == "text":
                result = transcript
            else:
                result = transcript.text
            
            logger.info(f"Transcription successful: {result[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"Speech-to-text error: {str(e)}")
            raise
    
    async def text_to_speech(
        self,
        text: str,
        voice: str = "nova",
        model: str = "tts-1",
        speed: float = 1.0
    ) -> bytes:
        """
        Convert text to speech using OpenAI TTS.
        
        Args:
            text: Text to convert to speech (auto-detects language)
            voice: Voice to use ('alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer')
            model: TTS model ('tts-1' for standard, 'tts-1-hd' for higher quality)
            speed: Speech speed (0.25 to 4.0)
        
        Returns:
            Audio bytes (MP3 format)
        """
        try:
            if voice not in self.AVAILABLE_VOICES:
                logger.warning(f"Invalid voice {voice}, using 'nova'")
                voice = "nova"
            
            logger.info(f"Converting text to speech, voice: {voice}")
            
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed
            )
            
            audio_data = response.content
            logger.info(f"Text-to-speech successful, audio size: {len(audio_data)} bytes")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {str(e)}")
            raise
    
    async def translate_speech(
        self,
        audio_file,
        target_language: str = "en"
    ) -> str:
        """
        Translate speech in any language to English.
        
        Args:
            audio_file: Audio file object
            target_language: Currently only supports 'en' (English)
        
        Returns:
            Translated text in English
        """
        try:
            logger.info("Translating audio to English")
            
            translation = self.client.audio.translations.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            
            logger.info(f"Translation successful: {translation[:100]}...")
            return translation
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise
