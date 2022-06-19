import sys
import os
import logging
import time
from flask import Flask, request, send_file
import urllib.parse
import shutil
import glados

sys.path.insert(0, os.getcwd()+'/glados_tts')
logging.basicConfig(filename='glados_engine_service.log',
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s]\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',level=logging.DEBUG)

def printedLog(message):
    logging.info(message)
    print(message)

def printTimelapse(processName,old_time):
    printedLog(f"{processName} took {str((time.time() - old_time) * 1000)} ms")

def filenameParse(input_text):
    filename = "GLaDOS-tts-"+input_text.replace(" ", "-")
    filename = filename.replace("!", "")
    filename = filename.replace("°c", "degrees celcius")
    filename = filename.replace(",", "")+".wav"
    return filename

def checkCache(file):
    # Update access time. This will allow for routine cleanups
    os.utime(file, None)
    printedLog("The audio sample sent from cache.")
    return send_file(file)

# If the script is run directly, assume remote engine
if __name__ == "__main__":
    printedLog("Initializing TTS Remote Engine...")
    glados.loadModels()
    PORT = 8124
    CACHE = True

    printedLog("Initializing TTS Server...")
    app = Flask(__name__)
    @app.route('/synthesize/', defaults={'text': ''},methods=["POST","GET"])
    @app.route('/synthesize/<path:text>',methods=["POST","GET"])
    def synthesize(text):
        if(request.method=="GET"):
            if(text == ''): return 'No input'
            input_text = urllib.parse.unquote(request.url[request.url.find('synthesize/')+11:])
        elif(request.method=="POST"):
            input_text = request.data.decode('ascii')
        printedLog(f"Input text: {input_text}")

        output_key = filenameParse(input_text)

        if not os.path.exists('audio'):
            os.makedirs('audio')
        file = os.getcwd()+'/audio/'+output_key

        # Check for Local Cache
        #if(os.path.isfile(file)): return checkCache(file)

        # Generate New Sample
        audio = glados.glados_tts(input_text)
        output_file = glados.saveAudioFile(audio,output_key)
        send_file(file)
		# If the input_text isn't too long, store in cache
        if(len(input_text) < 200 and CACHE):
            shutil.move(output_file, file)
        else:
            print("Sending else")
            return send_file(file)
        print("No else")
        return send_file(file)

    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    printedLog(f"Listening in http://localhost:{PORT}/synthesize/{'{PRHASE}'}")
    app.run(host="0.0.0.0", port=PORT)
