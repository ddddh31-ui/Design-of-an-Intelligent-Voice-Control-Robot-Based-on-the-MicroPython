import usocket
import ujson
from utils.helpers import get_current_date_str
import config

class Dispatcher:
    """调度器：处理硬件逻辑流转和指令分发"""
    def __init__(self, hal, ai_client):
        self.hal = hal
        self.ai = ai_client

    def handle_local_intent(self, text):
        """本地拦截：高优级的硬件动作 (如计时) 先行处理，构建上下文"""
        txt = text.replace("，","").replace("。","")
        
        # 1. 计时器调度
        if "开始计时" in txt or "帮我计时" in txt:
            self.hal.start_timer()
            return False, "Context: User STARTED the timer just now."
        elif "停止计时" in txt:
            t = self.hal.stop_timer()
            return False, f"Context: User STOPPED timer at {t}s."
        elif "多久" in txt or "几秒" in txt:
            t = self.hal.get_timer_value()
            if t >= 0: return False, f"Context: Current timer is {t}s."
            return False, "Context: Timer is NOT running."

        # 2. 天气调度 (借用 AI 识别城市)
        if "天气" in txt:
            loc = self.ai.analyze_intent(txt)
            w_data = self._fetch_weather(loc)
            return False, f"Context: {w_data}. Date: {get_current_date_str()}."

        return False, f"Context: Date: {get_current_date_str()}."

    def execute_action(self, action_dict):
        """未来扩展：执行 AI 产生的符合 Protocol 的 JSON 动作"""
        action_type = action_dict.get("action", "")
        print(f"[Dispatcher] Executing Action: {action_type}")
        
        if action_type == "LED_ON":
            print("-> Triggering external LED ON relay...")
            # e.g., external_relay.value(1)
        elif action_type == "LED_OFF":
            print("-> Triggering external LED OFF relay...")
        elif action_type == "ARM_WAVE":
            print("-> Triggering Servo Motor to wave...")

    def _fetch_weather(self, location):
        """获取外部天气数据服务"""
        self.hal.log("Fetching Weather...")
        try:
            url = f"https://api.seniverse.com/v3/weather/now.json?key={config.SENIVERSE_KEY}&location={location}&language=zh-Hans&unit=c"
            s = usocket.socket(); s.settimeout(5)
            s.connect(usocket.getaddrinfo("api.seniverse.com", 80)[0][-1])
            s.send(f"GET {url} HTTP/1.1\r\nHost: api.seniverse.com\r\nConnection: close\r\n\r\n".encode())
            
            resp = b""
            while True:
                c = s.recv(512)
                if not c: break
                resp += c; self.hal.tick()
            s.close()
            
            r_str = resp.decode()
            idx = r_str.find("{")
            if idx != -1:
                data = ujson.loads(r_str[idx:])
                if "results" in data:
                    now = data["results"][0]["now"]
                    city = data["results"][0]["location"]["name"]
                    return f"Loc:{city}, Weather:{now['text']}, Temp:{now['temperature']}C"
        except Exception as e: print(f"[Dispatcher] Wea Err: {e}")
        return "Weather API Failed"
