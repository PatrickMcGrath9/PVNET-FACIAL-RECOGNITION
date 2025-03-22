import json #for serializing objects
import pyttsx3 #for the TTS engine
import os #for finding files

class TTSManager:
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
        if os.path.exists(self.params.CATCHPHRASES_DB_PATH):
            with open("catchphrases.json", "rt") as f:
                catchphrases = json.load(f)
    
    def __del__(self): #TODO
        #write catch phrases to db file
        if os.path.exists(self.params.CATCHPHRASES_DB_PATH):
            with open(self.params.CATCHPHRASES_DB_PATH, "wt") as f:
                    json.dump(self.catchphrases, f)

    def request_speak(self, speech): #TODO
    #async with tts_lock:
        self.engine.say(speech)
        self.engine.runAndWait()

    async def add_catchphrase(self, name, catchphrase):
        self.catchphrases[name] = catchphrase