import machine
import network
import time
import urequests
import ujson
import struct
import os
import gc
import usocket
import ntptime
from machine import I2S, Pin, SoftI2C
import config
import tm1637

# ================= 全局配置 =================
oled = None
tm = None 
asr_pin = Pin(config.PIN_ASR_WAKE, Pin.IN, Pin.PULL_DOWN)

# 计时器全局变量
timer_running = False
timer_start_time = 0

# ================= 1. 硬件初始化 =================
def init_hardware():
    global oled, tm
    # OLED
    try:
        import ssd1306
        i2c = SoftI2C(scl=Pin(config.PIN_OLED_SCL), sda=Pin(config.PIN_OLED_SDA), freq=100000)
        oled = ssd1306.SSD1306_I2C(128, 64, i2c)
        oled.fill(0); oled.text("System Booting...", 0, 0); oled.show()
    except: oled = None

    # TM1637
    try:
        tm = tm1637.TM1637(clk=Pin(config.PIN_TM_CLK), dio=Pin(config.PIN_TM_DIO))
        tm.show_number(8888)
        time.sleep(0.5)
        tm.clear()
        print("[Init] TM1637 Ready")
    except: tm = None

# ================= 2. 网络与工具 =================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        oled_log("Wifi Connect...")
        try:
            wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
            for _ in range(15):
                if wlan.isconnected(): break
                time.sleep(1)
        except: pass
    
    if wlan.isconnected():
        try:
            ntptime.host = 'ntp.aliyun.com'
            ntptime.settime()
        except: pass
        return True
    return False

def get_current_date_str():
    t = time.localtime(time.time() + 8 * 3600)
    # 格式优化：xx月xx日 周x
    w_day = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][t[6]]
    return "{}月{}日 {} {:02d}:{:02d}".format(t[1], t[2], w_day, t[3], t[4])

def url_encode(text):
    res = ""
    for char in text:
        if 'a'<=char<='z' or 'A'<=char<='Z' or '0'<=char<='9' or char in "-_.~": res+=char
        else:
            try: res+="".join(["%%%02X"%b for b in char.encode("utf-8")])
            except: pass
    return res

def get_access_token(ak, sk):
    try:
        res = urequests.post(f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={ak}&client_secret={sk}")
        token = res.json().get("access_token")
        res.close()
        return token
    except: return None

# ================= 3. 天气与意图识别 =================
def analyze_city_intent(user_text):
    """分析用户想查哪个城市"""
    print(f"Analyzing City: {user_text}")
    oled_log("Checking City...")
    
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config.DEEPSEEK_API_KEY.strip()}"}
    
    prompt = (
        "Analyze the user text. If they mention a specific city, return ONLY the City Name in Pinyin (lowercase). "
        "Example: '北京天气' -> 'beijing'. '查看上海' -> 'shanghai'. "
        "If NO city is mentioned, return ONLY 'ip'. "
        "Output NOTHING else."
    )
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": user_text}],
        "stream": False, "max_tokens": 10, "temperature": 0.1
    }
    
    try:
        res = urequests.post(url, headers=headers, data=ujson.dumps(payload).encode('utf-8'))
        if res.status_code == 200:
            data = res.json(); res.close()
            city = data["choices"][0]["message"]["content"].strip().lower().replace("'", "").replace(".", "")
            print(f"Target: {city}")
            return city
    except: pass
    return "ip"

def get_weather_data(location):
    """心知天气"""
    oled_log(f"Weather: {location}")
    try:
        url = f"https://api.seniverse.com/v3/weather/now.json?key={config.SENIVERSE_KEY}&location={location}&language=zh-Hans&unit=c"
        s = usocket.socket(); s.settimeout(5)
        s.connect(usocket.getaddrinfo("api.seniverse.com", 80)[0][-1])
        s.send(f"GET {url} HTTP/1.1\r\nHost: api.seniverse.com\r\nConnection: close\r\n\r\n".encode())
        resp = b""
        while True:
            c = s.recv(512)
            if not c: break
            resp += c
        s.close()
        
        r_str = resp.decode()
        idx = r_str.find("{")
        if idx != -1:
            data = ujson.loads(r_str[idx:])
            if "results" in data:
                now = data["results"][0]["now"]
                city = data["results"][0]["location"]["name"]
                return f"Loc:{city}, Wea:{now['text']}, Tmp:{now['temperature']}C"
    except Exception as e: print(f"Wea Err: {e}")
    return None

# ================= 4. 显示与动画 =================
def oled_log(msg, y=0, clear=True):
    print(f"[LOG] {msg}")
    if oled:
        try:
            if clear: oled.fill(0)
            safe = ''.join([c for c in str(msg) if ord(c) < 128])
            oled.text(safe[:16], 0, y)
            oled.show()
        except: pass

def show_loading_animation(text="Thinking"):
    if not oled: return
    for i in range(3):
        oled.fill(0)
        oled.text(text, 0, 20)
        oled.text("." * (i+1), 0, 35)
        oled.show()
        for _ in range(5):
            update_led_logic(); time.sleep_ms(50)

def show_pinyin_paged(text):
    if oled is None or not text: return
    words = text.split(' ')
    lines = []
    curr = ""
    for w in words:
        if len(curr + w) < 16: curr += w + " "
        else: lines.append(curr); curr = w + " "
    lines.append(curr)
    
    pages = (len(lines)+4)//5
    for p in range(pages):
        oled.fill(0)
        oled.text(f">> AI ({p+1}/{pages})", 0, 0)
        oled.hline(0, 10, 128, 1)
        for i, line in enumerate(lines[p*5:(p+1)*5]):
            oled.text(line, 0, 14+i*10)
        oled.show()
        if pages > 1:
            for _ in range(30): # 3秒翻页
                time.sleep_ms(100); update_led_logic()

# ================= 5. 逻辑核心 =================
def update_led_logic():
    if timer_running and tm:
        elapsed = int(time.time() - timer_start_time)
        tm.numbers(elapsed, colon=(elapsed % 2 == 0))

def handle_local_commands(text):
    global timer_running, timer_start_time
    txt = text.replace("，","").replace("。","")
    
    if "开始计时" in txt or "帮我计时" in txt:
        timer_start_time = time.time(); timer_running = True
        if tm: tm.numbers(0, colon=True)
        return False, "Context: Timer STARTED."
    elif "停止计时" in txt:
        timer_running = False
        t = int(time.time() - timer_start_time)
        return False, f"Context: Timer STOPPED at {t}s."
    elif "多久" in txt or "几秒" in txt:
        if timer_running:
            t = int(time.time() - timer_start_time)
            return False, f"Context: Current timer is {t}s."
        return False, "Context: Timer NOT running."

    if "天气" in txt:
        loc = analyze_city_intent(txt)
        w_data = get_weather_data(loc)
        if w_data: return False, f"Context: {w_data}. Date: {get_current_date_str()}."
        return False, f"Context: Weather check failed. Date: {get_current_date_str()}."

    return False, f"Context: Date: {get_current_date_str()}."

# ================= 6. DeepSeek (有趣的灵魂核心) =================
def ask_deepseek(question, context=""):
    show_loading_animation("Thinking")
    gc.collect()
    
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config.DEEPSEEK_API_KEY.strip()}"}
    
    # === 注入灵魂的 Prompt (高情商、有趣、好听) ===
    base_prompt = (
        "You are a high-EQ, witty, and knowledgeable robot companion living in an ESP32 chip. "
        "You are NOT a boring machine. "
        "Strict Format: 'PINYIN # CHINESE'. "
        "Pinyin: ASCII only. Chinese < 80 chars. "
        "Style: "
        "1. Be warm, humorous, or slightly sarcastic depending on the topic. "
        "2. Use metaphors or interesting facts. "
        "3. Use [Context] (Time, Weather) naturally. "
        "Example: 'Tian qi bu cuo # 天气不错，适合出去晒晒你发霉的心情。'"
    )
    
    final_q = f"[{context}] {question}" if context else question
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": base_prompt}, {"role": "user", "content": final_q}],
        "stream": False, "max_tokens": 150, "temperature": 1.4 # 温度高一点，更活泼
    }
    
    try:
        res = urequests.post(url, headers=headers, data=ujson.dumps(payload).encode('utf-8'))
        if res.status_code == 200:
            data = res.json(); res.close()
            content = data["choices"][0]["message"]["content"].strip()
            print(f"[DeepSeek] {content}")
            if "#" in content: return content.split("#")[0].strip(), content.split("#")[1].strip()
            return content, ""
    except Exception as e: print(f"AI Err: {e}")
    return "Error", ""

# ================= 7. TTS (声音优化版) =================
def play_baidu_tts(text, token):
    if not text: return
    oled_log("Speaking...")
    i2s = None; s = None
    try:
        i2s = I2S(1, sck=Pin(config.PIN_SPK_BCLK), ws=Pin(config.PIN_SPK_LRC), sd=Pin(config.PIN_SPK_DIN), mode=I2S.TX, bits=16, format=I2S.MONO, rate=16000, ibuf=4096)
        
        # === 声音参数优化 ===
        # per=4: 度丫丫 (情感女声，温暖、可爱)
        # per=3: 度逍遥 (情感男声，有磁性)
        # per=1: 度小宇 (标准男声，比较普通)
        # spd=5: 语速 (5是标准，想快点可以改6)
        # pit=5: 音调 (5是标准)
        voice_per = 4 
        
        host = "tsn.baidu.com"
        path = f"/text2audio?tex={url_encode(text)}&lan=zh&cuid=esp32&ctp=1&tok={token}&aue=4&spd=5&pit=5&per={voice_per}"
        
        s = usocket.socket(); s.settimeout(5)
        s.connect(usocket.getaddrinfo(host, 80)[0][-1])
        s.send(f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
        
        head = b""
        while b"\r\n\r\n" not in head:
            c = s.recv(1); 
            if not c: break
            head += c
            
        last_refresh = 0
        while True:
            try:
                d = s.recv(512)
                if not d: break
                i2s.write(d)
                # 边说话边刷新LED
                now = time.ticks_ms()
                if time.ticks_diff(now, last_refresh) > 200:
                    update_led_logic(); last_refresh = now
            except: break
        i2s.write(b'\x00'*3000)
    except Exception as e: print(f"TTS Err: {e}")
    finally:
        if s: s.close()
        if i2s: i2s.deinit()

# ================= 8. 录音/识别 (保持不变) =================
def record_audio_vad(fn):
    oled_log("Listening...")
    i2s = None
    try:
        # 初始化麦克风
        i2s = I2S(0, sck=Pin(config.PIN_I2S_SCK), ws=Pin(config.PIN_I2S_WS), sd=Pin(config.PIN_I2S_SD), mode=I2S.RX, bits=16, format=I2S.MONO, rate=16000, ibuf=4096)
        
        buf = bytearray(2048)
        
        # === 极速校准底噪 (0.1秒) ===
        # 优化：不需要校准太久，取5次样本即可
        print("Calibrating...", end="")
        noise_sum = 0
        for i in range(5): 
            i2s.readinto(buf)
            s = struct.unpack(f"<{len(buf)//2}h", buf)
            noise_sum += sum(abs(x) for x in s) // len(s)
            time.sleep_ms(20)
        
        # 动态阈值：底噪 + 灵敏度
        # 如果环境很吵，可以把 800 调大到 1500
        threshold = max((noise_sum // 10) + 800, 800)
        print(f" Thr:{threshold}")
        
        oled_log("Speak Now!")
        
        f = open(fn, "wb")
        
        is_speaking = False      # 是否检测到了人声
        silent_start_time = 0    # 静音开始的时间点
        start_record_time = time.time() # 录音总开始时间
        
        # 循环读取音频
        while True:
            num = i2s.readinto(buf)
            if num:
                # 写入文件
                f.write(buf)
                
                # 计算能量
                samples = struct.unpack(f"<{num//2}h", buf)
                energy = sum(abs(x) for x in s) // len(s)
                
                # === VAD 核心逻辑 ===
                if energy > threshold:
                    # 正在说话
                    is_speaking = True
                    silent_start_time = 0 # 重置静音计时器
                else:
                    # 能量低 (静音)
                    if is_speaking:
                        # 如果之前在说话，现在停了，开始计时
                        if silent_start_time == 0:
                            silent_start_time = time.time()
                        
                        # 如果静音持续超过设定值 (比如 0.6秒)
                        if time.time() - silent_start_time > config.SILENCE_DURATION:
                            print(">> End of speech detected!")
                            break # 【立刻跳出，不再录音】
            
            # 刷新数码管 (防止录音时LED卡住)
            update_led_logic()
            
            # 超时强制停止 (比如 10秒)
            if time.time() - start_record_time > config.MAX_RECORD_TIME:
                print(">> Timeout")
                break
                
        f.close()
        i2s.deinit()
        
        # 如果录音时间太短 (比如小于0.3秒)，可能是误触，返回失败
        if time.time() - start_record_time < 0.3:
            print("Too short, ignored.")
            return False
            
        return True
        
    except Exception as e:
        print(f"Rec Err: {e}")
        if i2s: i2s.deinit()
        return False

def recognize_speech(fn, token):
    try:
        fl = os.stat(fn)[6]
        host = "vop.baidu.com"
        s = usocket.socket(); s.settimeout(5)
        s.connect(usocket.getaddrinfo(host, 80)[0][-1])
        s.send(f"POST /server_api?cuid=esp32&token={token}&dev_pid=1537 HTTP/1.1\r\nHost: {host}\r\nContent-Type: audio/pcm;rate=16000\r\nContent-Length: {fl}\r\nConnection: close\r\n\r\n".encode())
        with open(fn, "rb") as f:
            while True:
                d = f.read(1024); 
                if not d: break
                s.send(d); update_led_logic()
        res = b""; 
        while True:
            try: 
                d = s.recv(512); 
                if not d: break
                res += d; update_led_logic()
            except: break
        s.close()
        r_str = res.decode()
        if "result" in r_str: return r_str.split('["')[1].split('"]')[0]
    except: pass
    return None

# ================= 主程序 (超级防崩版) =================
def main():
    while True:
        try:
            gc.collect()
            init_hardware()
            if not connect_wifi(): 
                print("Wifi Fail"); time.sleep(1); continue
            
            print("Getting Tokens...")
            asr_tok = get_access_token(config.BAIDU_ASR_API_KEY, config.BAIDU_ASR_SECRET_KEY)
            tts_tok = get_access_token(config.BAIDU_TTS_API_KEY, config.BAIDU_TTS_SECRET_KEY)
            
            if not asr_tok: 
                oled_log("Key Err"); time.sleep(2); continue
            
            oled_log("AI Ready", clear=True)
            print(">>> System Ready.")
            
            last_led_update = 0
            
            while True:
                now = time.ticks_ms()
                if time.ticks_diff(now, last_led_update) > 500:
                    update_led_logic(); last_led_update = now
                    
                if asr_pin.value() == 1:
                    print("\n>>> Wake Up")
                    if not record_audio_vad("voice.pcm"):
                        oled_log("Rec Fail"); time.sleep(1); continue
                        
                    gc.collect()
                    text = recognize_speech("voice.pcm", asr_tok)
                    
                    if text:
                        print(f"\n[User]: {text}")
                        skip_ai, context = handle_local_commands(text)
                        
                        if not skip_ai:
                            pinyin, chinese = ask_deepseek(text, context)
                            if chinese and tts_tok:
                                play_baidu_tts(chinese, tts_tok)
                                show_pinyin_paged(pinyin)
                            else:
                                show_pinyin_paged(pinyin)
                    
                    oled_log("AI Ready", clear=True)
                    gc.collect()
                    
                time.sleep_ms(50)
                
        except Exception as e:
            print(f"\n!!! CRITICAL ERROR: {e} !!!")
            oled_log("Error! Resetting...")
            if tm: tm.clear()
            time.sleep(3)

if __name__ == "__main__":
    main()
