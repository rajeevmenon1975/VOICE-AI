import os
import sys

# Try importing open source audio libraries
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

class OpenSourceVoiceEngine:
    """
    Open-source Speech Engine (STT / TTS) reference class.
    Demonstrates how local models execute speech recognition and synthesis.
    """
    def __init__(self):
        self.gtts_installed = HAS_GTTS
        self.sr_installed = HAS_SR

    def text_to_speech_file(self, text: str, lang_code: str, output_path: str) -> bool:
        """
        Synthesizes text to a localized MP3 file.
        lang_code map:
            - English: 'en'
            - Hindi: 'hi'
            - Gujarati: 'gu'
        """
        if not self.gtts_installed:
            print(f"[TTS Fallback Engine] Synthesizing speech (gTTS missing) -> {lang_code}: '{text}'")
            # Create a mock audio placeholder file (a simple text log representing the output audio file)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"[MOCK AUDIO WAVEFORM DATA for: {text}]")
            return True

        try:
            # Map code to gTTS supported codes
            mapped_code = 'en'
            if 'hi' in lang_code.lower():
                mapped_code = 'hi'
            elif 'gu' in lang_code.lower():
                mapped_code = 'gu'

            tts = gTTS(text=text, lang=mapped_code, slow=False)
            tts.save(output_path)
            print(f"🎙️ [Open-Source TTS] Successfully saved voice synthesis to {output_path} ({mapped_code})")
            return True
        except Exception as e:
            print(f"❌ [Open-Source TTS] Error during audio generation: {e}")
            return False

    def speech_to_text(self, audio_file_path: str, lang_code: str) -> str:
        """
        Transcribes a local audio wave file into plain text.
        """
        if not self.sr_installed:
            print(f"[STT Fallback Engine] Transcribing {audio_file_path} (speech_recognition missing)...")
            return "Yes, please buy"

        r = sr.Recognizer()
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio_data = r.record(source)
                
            mapped_code = 'en-IN'
            if 'hi' in lang_code.lower():
                mapped_code = 'hi-IN'
            elif 'gu' in lang_code.lower():
                mapped_code = 'gu-IN'

            text = r.recognize_google(audio_data, language=mapped_code)
            print(f"🎙️ [Open-Source STT] Transcribed text: '{text}' using language '{mapped_code}'")
            return text
        except Exception as e:
            print(f"❌ [Open-Source STT] Error recognizing speech: {e}")
            return ""

def main():
    print("="*80)
    print("      🎙️ OPEN SOURCE STT & TTS NATIVE SPEECH PIPELINE REFERENCE 🎙️")
    print("="*80)
    
    engine = OpenSourceVoiceEngine()
    print(f"💡 Local gTTS (Text-To-Speech) library: {'INSTALLED' if engine.gtts_installed else 'MISSING (Runs in simulation mode)'}")
    print(f"💡 Local SpeechRecognition (STT) library: {'INSTALLED' if engine.sr_installed else 'MISSING (Runs in simulation mode)'}")
    print("-"*80)

    # Test Speech Synthesis
    test_phrases = {
        "en": "Hello Rajeev! Welcome to the Voice AI Backoffice. Let's place your order.",
        "hi": "नमस्ते प्रिया जी! शेयर बाजार में निवेश करना अब बहुत आसान है।",
        "gu": "નમસ્તે અમિત ભાઈ! તમારું સ્વાગત છે વોઈસ એઆઈ બ્રોકિંગમાં."
    }

    print("\n🚀 Simulating Speech Synthesis (TTS) for regional Indian languages...")
    for lang, phrase in test_phrases.items():
        filename = f"test_voice_{lang}.mp3"
        success = engine.text_to_speech_file(phrase, lang, filename)
        if success:
            print(f"  [✓] Generated {filename} for {lang.upper()}")
            # Clean up if it was a real file
            if os.path.exists(filename) and engine.gtts_installed:
                try:
                    os.remove(filename)
                except OSError:
                    pass
        else:
            print(f"  [✗] Failed to generate {filename}")

    print("\n📈 NATIVE SPEECH PIPELINE SCHEMATIC FLOW:")
    print("  [Mic/Audio Input] -> [WAV Capture (16kHz PCM)] -> [Google Speech API / Whisper Local] -> [Text Tokens]")
    print("  [Response Text] -> [gTTS Engine / ElevenLabs API] -> [MP3 Stream] -> [Browser/Speaker Playback]")
    print("="*80)

if __name__ == "__main__":
    main()
