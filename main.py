import pvporcupine
import pyaudio
from pvrecorder import PvRecorder
from dotenv import load_dotenv
import logging, verboselogs
from time import sleep
import websockets
import json
import asyncio

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)


from mycroft_plugin_tts_mimic3 import Mimic3TTSPlugin
import simpleaudio as sa

load_dotenv()

last_message = ""
ACCESS_KEY = 'jsoYHt2GJ3T+6zAvfSgtzBRekNzQioEhisl97z2xQ/TuSRTJfNvphQ=='
KEYWORD_FILE_PATH = '/home/raymond/OpenHome/Hey-Open-Home_en_mac_v3_0_0.ppn'
porcupine = pvporcupine.create(
  access_key='jsoYHt2GJ3T+6zAvfSgtzBRekNzQioEhisl97z2xQ/TuSRTJfNvphQ==',
  keyword_paths=['/home/raymond/OpenHome/Hey-Open-Home_en_raspberry-pi_v3_0_0.ppn']
)

def Wake_Word_Detection():
   
   recorder = PvRecorder(device_index=-1, frame_length=512)

   try:
     recorder.start()

     while True:
        frame = recorder.read()
        keyword_index = porcupine.process(frame)
        if keyword_index == 0:
            print('Wake word detected!')
            greeting = input("Hi, how would you like me to address you? ")
            TTS("Hello " + greeting + ", you are entering a speech to text program now. Press enter to exit.")
            # TTS("Hello Raymond, you are entering a speech to text program now. Press enter to exit.")
            porcupine.delete()
            break
   except KeyboardInterrupt:
        recorder.stop()
   finally:
        recorder.delete()
        STT()


def STT():
    try:
        # example of setting up a client config. logging values: WARNING, VERBOSE, DEBUG, SPAM
        # config = DeepgramClientOptions(
        #     verbose=logging.DEBUG,
        #     options={"keepalive": "true"}
        # )
        # deepgram: DeepgramClient = DeepgramClient("", config)
        # otherwise, use default config
        deepgram = DeepgramClient()

        dg_connection = deepgram.listen.live.v("1")

        def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            print(f"speaker: {sentence}")
            
            

        def on_metadata(self, metadata, **kwargs):
            print(f"\n\n{metadata}\n\n")

        def on_utterance_end(self, utterance_end, **kwargs):
            print(f"\n\n{utterance_end}\n\n")

        def on_error(self, error, **kwargs):
            print(f"\n\n{error}\n\n")

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        options = LiveOptions(
            model="nova-2",
            # punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            # To get UtteranceEnd, the following must be set:
            # interim_results=True,
            # utterance_end_ms="3000",
            smart_format=True,
        )
        dg_connection.start(options, addons=dict(myattr="hello"), test="hello")

        # Open a microphone stream
        microphone = Microphone(dg_connection.send)

        # start microphone
        microphone.start()

        # wait until finished
        input("Press Enter to stop recording...\n\n")

        # Wait for the microphone to close
        microphone.finish()
        TTS("Have a nice day!")

        # Indicate that we've finished
        dg_connection.finish()
        print("Finished")
        # sleep(30)  # wait 30 seconds to see if there is any additional socket activity
        # print("Really done!")

    except Exception as e:
        print(f"Could not open socket: {e}")
        return

def TTS(text): 
    cfg = {"voice": "en_US/cmu-arctic_low"}  # select voice etc here

    mimic = Mimic3TTSPlugin(lang="en_US", config=cfg)
    input_text = text
    mimic.get_tts(input_text, "output_file_path.wav")
    wave_obj = sa.WaveObject.from_wave_file("output_file_path.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()  # Wait until sound has finished playing


def main():
    Wake_Word_Detection()
    # STT()
    
# For testing connection purposes
# async def main():
#     try:
#         async with websockets.connect('wss://api.deepgram.com/v1/listen',
#         # Remember to replace the YOUR_DEEPGRAM_API_KEY placeholder with your Deepgram API Key
#         extra_headers = { 'Authorization': f'token 2a1434f3fde551de795df913574f0b844c72db50' }) as ws:
#         # If the request is successful, print the request ID from the HTTP header
#             print('🟢 Successfully opened connection')
#             print(f'Request ID: {ws.response_headers["dg-request-id"]}')
#             await ws.send(json.dumps({
#                 'type': 'CloseStream'
#             }))
#     except websockets.exceptions.InvalidStatusCode as e:
#         # If the request fails, print both the error message and the request ID from the HTTP headers
#         print(f'🔴 ERROR: Could not connect to Deepgram! {e.headers.get("dg-error")}')
#         print(f'🔴 Please contact Deepgram Support with request ID {e.headers.get("dg-request-id")}')

# asyncio.run(main())

if __name__ == "__main__":
    main()
