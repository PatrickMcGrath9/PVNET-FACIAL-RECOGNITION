import asyncio
import json
import pyttsx3 #for the TTS engine

class TTSManager:
    file_lock = asyncio.Lock()
    tts_lock = asyncio.Lock()
    catchphrases = { #TODO load from file instead
        "Tiffany" : "borbnation will flourish.",
        "Patrick" : "slayer of bugnation.",
        "Tyler" : "ruler of the monkeys."
    }

    class params:
        SPEAK_INTERVAL = 300 # TODO ?
        UNKNOWN_SPEAK_INTERVAL = 60 # TODO ?
        DETECTION_TIME_REQUIRED = 0.3 # Time required for known faces, stops random objects being recognized as faces TODO necessary?
        UNKNOWN_DETECTION_TIME_REQUIRED = 0.75 # Time required for unknown faces, stops random objects being recongized as faces TODO necessary?
        CATCHPHRASES_DB_PATH = ""

    def __init__(self):  
        self.engine = pyttsx3.init() #intialize TTS engine
        with open("catchphrases.json", "rt") as f:
            catchphrases = json.load(f)
    
    def __del__(self): #TODO

        #write catch phrases to db file
        async with file_lock:
            with open(self.params.CATCHPHRASES_DB_PATH, "wt") as f:
                    json.dump(self.catchphrases, f)

    async def request_speak(self, speech): #TODO
        async with tts_lock:
            self.engine.say(speech)
            self.engine.runAndWait()

    async def add_catchphrase(self, name, catchphrase):
            self.catchphrases[name] = catchphrase
