import time
import gc
from machine import Pin
import config
from utils.network_mgr import NetworkManager
from utils.helpers import get_access_token
from modules.hal import HAL
from modules.audio import AudioEngine
from modules.ai_client import AIClient
from modules.dispatcher import Dispatcher

def main():
    while True: # 顶级容错循环
        try:
            gc.collect()
            
            # 1. 初始化模块
            hal = HAL()
            net = NetworkManager(hal)
            if not net.connect():
                print("WiFi Fail, Retrying..."); time.sleep(2); continue
                
            # 获取鉴权 Tokens
            hal.log("Get Tokens...")
            asr_tok = get_access_token(config.BAIDU_ASR_API_KEY, config.BAIDU_ASR_SECRET_KEY)
            tts_tok = get_access_token(config.BAIDU_TTS_API_KEY, config.BAIDU_TTS_SECRET_KEY)
            if not asr_tok: hal.log("Key Error"); time.sleep(2); continue

            # 实例化引擎
            audio = AudioEngine(hal, asr_tok, tts_tok)
            ai = AIClient(hal)
            dispatcher = Dispatcher(hal, ai)
            
            wake_pin = Pin(config.PIN_ASR_WAKE, Pin.IN, Pin.PULL_DOWN)
            hal.log("System Ready!", clear=True)
            print(">>> System Boot Completed. Waiting for wake word...")
            
            # 2. 核心交互循环
            while True:
                hal.tick() # 维持硬件状态 (如数码管计时)
                
                if wake_pin.value() == 1:
                    print("\n>>> Wake Up")
                    if audio.record_audio_vad("voice.pcm"):
                        gc.collect()
                        user_text = audio.recognize_speech("voice.pcm")
                        
                        if user_text:
                            print(f"\n[User]: {user_text}")
                            
                            # 调度器处理：本地拦截 or 硬件动作 or 上下文组装
                            skip_ai, context = dispatcher.handle_local_intent(user_text)
                            
                            if not skip_ai:
                                # AI 思考并返回结果与潜在的动作协议
                                pinyin, chinese, action_json = ai.ask(user_text, context)
                                
                                # 调度器执行 AI 产生的扩展硬件动作指令
                                if action_json: dispatcher.execute_action(action_json)
                                
                                # 播报与显示
                                if chinese and tts_tok:
                                    audio.play_tts(chinese, pinyin)
                                else:
                                    hal.show_pinyin_paged(pinyin)
                                    
                    hal.log("AI Ready", clear=True)
                    gc.collect()
                time.sleep_ms(50)
                
        except Exception as e:
            print(f"\n!!! CRITICAL ERROR: {e} !!!")
            time.sleep(3) # 遇到致命错误，等待后自动重启软件逻辑

if __name__ == "__main__":
    main()
