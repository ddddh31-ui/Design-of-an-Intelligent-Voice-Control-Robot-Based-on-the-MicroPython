import urequests
import ujson
import gc
import config

class AIClient:
    def __init__(self, hal):
        self.hal = hal
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config.DEEPSEEK_API_KEY.strip()}"}

    def analyze_intent(self, user_text):
        """专门用来让 AI 提取实体 (如查天气的城市)"""
        self.hal.log("Thinking Intent...")
        prompt = "Analyze user text for weather query. Return ONLY City Name in Pinyin (e.g. 'beijing'). If no city mentioned, return 'ip'. Output NOTHING else."
        payload = {"model": "deepseek-chat", "messages":[{"role": "system", "content": prompt}, {"role": "user", "content": user_text}], "stream": False, "max_tokens": 10, "temperature": 0.1}
        try:
            res = urequests.post(self.api_url, headers=self.headers, data=ujson.dumps(payload).encode('utf-8'))
            if res.status_code == 200:
                data = res.json(); res.close()
                return data["choices"][0]["message"]["content"].strip().lower().replace("'", "").replace(".", "")
        except: pass
        return "ip"

    def ask(self, question, context=""):
        self.hal.show_loading("Thinking")
        gc.collect()
        
        # 【进阶优化】：在 Prompt 中预留扩展动作指令的 JSON 接口
        base_prompt = (
            "You are a witty, smart ESP32 robot. "
            "Format Requirement: Reply MUST be exactly 'PINYIN # CHINESE'. "
            "Pinyin: ASCII only. Chinese < 80 chars. "
            "If the user asks to control hardware (like turning on a light), append a JSON block at the very end like this: "
            "```json\n{\"action\": \"LED_ON\"}\n``` "
            "Use [Context] accurately but humorously."
        )
        final_q = f"[{context}] {question}" if context else question
        payload = {"model": "deepseek-chat", "messages":[{"role": "system", "content": base_prompt}, {"role": "user", "content": final_q}], "stream": False, "max_tokens": 200, "temperature": 1.3}
        
        try:
            res = urequests.post(self.api_url, headers=self.headers, data=ujson.dumps(payload).encode('utf-8'))
            if res.status_code == 200:
                data = res.json(); res.close()
                content = data["choices"][0]["message"]["content"].strip()
                print(f"[AI] {content}")
                
                # 简单解析 Action JSON (支持未来扩展)
                action_json = None
                if "```json" in content:
                    try:
                        j_str = content.split("```json")[1].split("```")[0].strip()
                        action_json = ujson.loads(j_str)
                        content = content.split("```json")[0].strip() # 剔除 JSON 留作语音
                    except: pass

                if "#" in content:
                    return content.split("#")[0].strip(), content.split("#")[1].strip(), action_json
                return content, "", action_json
        except Exception as e: print(f"[AI] Network Err: {e}")
        return "Error", "", None
