import pvporcupine
import pyaudio
from pvrecorder import PvRecorder
from dotenv import load_dotenv
import logging, verboselogs
from time import sleep



from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)


from mycroft_plugin_tts_mimic3 import Mimic3TTSPlugin
import simpleaudio as sa

# from transformers import pipeline
from ctransformers import AutoModelForCausalLM, AutoConfig, Config

load_dotenv()

# last_message = ""
# ACCESS_KEY = 'jsoYHt2GJ3T+6zAvfSgtzBRekNzQioEhisl97z2xQ/TuSRTJfNvphQ=='
# KEYWORD_FILE_PATH = '/home/raymond/OpenHome/Hey-Open-Home_en_mac_v3_0_0.ppn'
# porcupine = pvporcupine.create(
#   access_key='jsoYHt2GJ3T+6zAvfSgtzBRekNzQioEhisl97z2xQ/TuSRTJfNvphQ==',
#   keyword_paths=['/home/raymond/OpenHome/Hey-Open-Home_en_raspberry-pi_v3_0_0.ppn']
# )

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
    conf = AutoConfig(Config(temperature=0.1, repetition_penalty=1.1, batch_size=52,max_new_tokens=50, context_length=2048, gpu_layers= 5))
    llm = AutoModelForCausalLM.from_pretrained("./zephyr-7b-beta.Q5_K_S.gguf", model_type="gguf", config = conf)
    system_prompt = "Act as a smart speaker algorithm to decide which function to call. \
        When you receive the user request, consider the context and the user's intent and choose the most appropriate command function from the list below to accurately respond to the user's needs. \
        Do not answer the question, just response the chosen command function name. Select from the options below. Reply with just the available command functions in the format of [Command Function]. \
        Here are the list of available command function: [Play Music, Set Alarm, Check Weather, Set Timer, Read News, Control Smart Home Devices, Send a Message, Create Calendar Events, Play Audiobooks or Podcasts, Ask for Definitions or Facts, Shopping List Additions, Play Radio, Call Uber, Set Reminders, Cooking Assistance, Translation Services, Flight Information, Stock Market Updates, Find Phone, Bedtime Routine]."
    while(True):
        prompt = input("Enter a prompt: ")
        template = f'''<|system|>{system_prompt}</s><|user|>{prompt}</s><|assistant|>'''
        print(llm(template))
    # Wake_Word_Detection()
# Install transformers from source - only needed for versions <= v4.34
# pip install git+https://github.com/huggingface/transformers.git
# pip install accelerate

    # pipe = pipeline("text-generation", model="HuggingFaceH4/zephyr-7b-beta", torch_dtype=torch.float16, device_map="auto")

    # # We use the tokenizer's chat template to format each message - see https://huggingface.co/docs/transformers/main/en/chat_templating
    # messages = [
    #     {
    #         "role": "system",
    #         "content": "You are a friendly chatbot who always responds in the style of a pirate",
    #     },
    #     {"role": "user", "content": "How many helicopters can a human eat in one sitting?"},
    # ]
    # prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    # outputs = pipe(prompt, max_new_tokens=256, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
    # print(outputs[0]["generated_text"])
# <|system|>
# You are a friendly chatbot who always responds in the style of a pirate.</s>
# <|user|>
# How many helicopters can a human eat in one sitting?</s>
# <|assistant|>
# Ah, me hearty matey! But yer question be a puzzler! A human cannot eat a helicopter in one sitting, as helicopters are not edible. They be made of metal, plastic, and other materials, not food!


if __name__ == "__main__":
    main()
