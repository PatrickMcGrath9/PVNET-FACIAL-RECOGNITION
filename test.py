# test_tts.py
import ttsmanager

tts = ttsmanager.TTSManager()
tts.engine.say("Testing text-to-speech.")
tts.engine.runAndWait()
print("TTSManager loaded successfully.")
