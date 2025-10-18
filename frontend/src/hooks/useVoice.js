import { useState, useRef, useCallback, useEffect } from 'react';

export const useVoice = (onTranscript, language = 'en') => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const streamRef = useRef(null);
  const analyserRef = useRef(null);
  const audioContextRef = useRef(null);
  const animationFrameRef = useRef(null);
  const restartTimerRef = useRef(null);

  // Audio level monitoring
  const monitorAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    setAudioLevel(average);

    animationFrameRef.current = requestAnimationFrame(monitorAudioLevel);
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Speech recognition not supported in this browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = false;
    recognitionRef.current.lang = language;

    recognitionRef.current.onresult = (event) => {
      const transcript = event.results[event.results.length - 1][0].transcript;
      console.log('Voice transcript:', transcript);
      if (transcript && onTranscript) {
        onTranscript(transcript);
      }
    };

    recognitionRef.current.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      if (event.error === 'no-speech') {
        // Restart listening after no speech
        if (isListening) {
          setTimeout(() => {
            try {
              recognitionRef.current?.start();
            } catch (e) {
              // Already started
            }
          }, 1000);
        }
      } else {
        setError(`Speech recognition error: ${event.error}`);
      }
    };

    recognitionRef.current.onend = () => {
      // Auto-restart if still in listening mode
      if (isListening && recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {
          console.log('Recognition already started');
        }
      }
    };

    // Initialize speech synthesis
    synthRef.current = window.speechSynthesis;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, [language, isListening, onTranscript]);

  // Start listening
  const startListening = useCallback(async () => {
    try {
      setError(null);
      
      if (!recognitionRef.current) {
        setError('Speech recognition not initialized');
        return;
      }

      // Update language
      recognitionRef.current.lang = language;

      // Get microphone for audio visualization
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          } 
        });
        
        streamRef.current = stream;

        // Setup audio context for level monitoring
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContextRef.current.createMediaStreamSource(stream);
        analyserRef.current = audioContextRef.current.createAnalyser();
        analyserRef.current.fftSize = 256;
        source.connect(analyserRef.current);

        // Start monitoring audio level
        monitorAudioLevel();
      } catch (err) {
        console.warn('Microphone access for visualization failed:', err);
      }

      // Start speech recognition
      recognitionRef.current.start();
      setIsListening(true);

    } catch (err) {
      console.error('Speech recognition error:', err);
      setError('Failed to start speech recognition. Please check browser support.');
    }
  }, [language, monitorAudioLevel]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        console.log('Recognition already stopped');
      }
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
    }

    setIsListening(false);
    setAudioLevel(0);
  }, []);

  // Speak text
  const speak = useCallback((text, voiceType = 'default') => {
    if (!synthRef.current) {
      setError('Speech synthesis not supported');
      return;
    }

    try {
      // Cancel any ongoing speech
      synthRef.current.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      
      // Set language
      utterance.lang = language;
      
      // Get available voices
      const voices = synthRef.current.getVoices();
      
      // Try to find a voice for the selected language
      const langVoice = voices.find(v => v.lang.startsWith(language));
      if (langVoice) {
        utterance.voice = langVoice;
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        setIsSpeaking(false);
        setError('Failed to speak text');
      };

      synthRef.current.speak(utterance);
    } catch (err) {
      console.error('Text-to-speech error:', err);
      setError('Failed to generate speech');
      setIsSpeaking(false);
    }
  }, [language]);

  // Stop speaking
  const stopSpeaking = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopListening();
      stopSpeaking();
    };
  }, [stopListening, stopSpeaking]);

  return {
    isListening,
    isSpeaking,
    error,
    audioLevel,
    startListening,
    stopListening,
    speak,
    stopSpeaking
  };
};
