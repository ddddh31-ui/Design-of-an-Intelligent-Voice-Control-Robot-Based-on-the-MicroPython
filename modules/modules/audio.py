import os
import time
import struct
import usocket
from machine import I2S, Pin
import config
from utils.helpers import url_encode

class AudioEngine:
    def __init__(self, hal, asr_token, tts_token):
        self.hal = hal
        self.asr_tok = asr_token
        self.tts_tok = tts_token

    def record_audio_vad(self, fn="voice.pcm"):
        self.hal.log("Listening...")
        i2s = None
        try:
            i2s = I2S(0, sck=Pin(config.PIN_I2S_SCK), ws=Pin(config.PIN_I2S_WS), sd=Pin(config.PIN_I2S_SD), mode=I2S.RX, bits=16, format=I2S.MONO, rate=16000, ibuf=4096)
            buf = bytearray(2048)
            
            # 校准底噪
            ns = 0
            for _ in range(5): 
                i2s.readinto(buf); s = struct.unpack(f"<{len(buf)//2}h", buf)
                ns += sum(abs(x) for x in s)//len(s); time.sleep_ms(20)
            thr = max((ns//10) + config.SILENCE_THRESHOLD_OFFSET, 500)
            
            self.hal.log("Speak Now!")
            with open(fn, "wb") as f:
                speaking = False; silent_t = None; start_t = time.time()
                while True:
                    if i2s.readinto(buf):
                        f.write(buf)
                        s = struct.unpack(f"<{num//2}h", buf)
                        eng = sum(abs(x) for x in s)//len(s)
                        if eng > thr: speaking = True; silent_t = None
                        elif speaking:
                            if not silent_t: silent_t = time.time()
                            if time.time() - silent_t > config.SILENCE_DURATION: break
                        self.hal.tick() # 防卡死
                    if time.time() - start_t > config.MAX_RECORD_TIME: break
            return (time.time() - start_t) > 0.4
        except Exception as e: print(f"[Audio] Rec Err: {e}")
        finally: 
            if i2s: i2s.deinit()
        return False

    def recognize_speech(self, fn):
        try:
            fl = os.stat(fn)[6]
            s = usocket.socket(); s.settimeout(5)
            s.connect(usocket.getaddrinfo("vop.baidu.com", 80)[0][-1])
            s.send(f"POST /server_api?cuid=esp32&token={self.asr_tok}&dev_pid=1537 HTTP/1.1\r\nHost: vop.baidu.com\r\nContent-Type: audio/pcm;rate=16000\r\nContent-Length: {fl}\r\nConnection: close\r\n\r\n".encode())
            with open(fn, "rb") as f:
                while True:
                    d = f.read(1024)
                    if not d: break
                    s.send(d); self.hal.tick()
            res = b""
            while True:
                try: 
                    d = s.recv(512); 
                    if not d: break
                    res += d; self.hal.tick()
                except: break
            s.close()
            r_str = res.decode()
            if "result" in r_str: return r_str.split('["')[1].split('"]')[0]
        except: pass
        return None

    def play_tts(self, text, pinyin_for_display=""):
        if not text: return
        self.hal.log("Speaking...")
        i2s = None; s = None
        try:
            i2s = I2S(1, sck=Pin(config.PIN_SPK_BCLK), ws=Pin(config.PIN_SPK_LRC), sd=Pin(config.PIN_SPK_DIN), mode=I2S.TX, bits=16, format=I2S.MONO, rate=16000, ibuf=4096)
            path = f"/text2audio?tex={url_encode(text)}&lan=zh&cuid=esp32&ctp=1&tok={self.tts_tok}&aue=4&spd=5&per=4"
            s = usocket.socket(); s.settimeout(5)
            s.connect(usocket.getaddrinfo("tsn.baidu.com", 80)[0][-1])
            s.send(f"GET {path} HTTP/1.1\r\nHost: tsn.baidu.com\r\nConnection: close\r\n\r\n".encode())
            
            while b"\r\n\r\n" not in s.recv(16): pass
            
            while True:
                try:
                    d = s.recv(512)
                    if not d: break
                    i2s.write(d)
                    self.hal.tick() # 一边播声音，一边刷新数码管
                except: break
            i2s.write(b'\x00'*3000)
        except Exception as e: print(f"[Audio] TTS Err: {e}")
        finally:
            if s: s.close()
            if i2s: i2s.deinit()
            if pinyin_for_display: self.hal.show_pinyin_paged(pinyin_for_display)
