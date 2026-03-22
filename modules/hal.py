import time
from machine import Pin, SoftI2C
import config

class HAL:
    """Hardware Abstraction Layer: 统一管理硬件状态与显示"""
    def __init__(self):
        self.oled = None
        self.tm = None
        self.timer_running = False
        self.timer_start = 0
        self.last_tick = 0
        self._init_oled()
        self._init_tm1637()

    def _init_oled(self):
        try:
            import lib.ssd1306 as ssd1306
            i2c = SoftI2C(scl=Pin(config.PIN_OLED_SCL), sda=Pin(config.PIN_OLED_SDA), freq=100000)
            self.oled = ssd1306.SSD1306_I2C(128, 64, i2c)
            self.oled.fill(0); self.oled.text("System Booting...", 0, 0); self.oled.show()
        except: print("[HAL] OLED Init Failed")

    def _init_tm1637(self):
        try:
            import lib.tm1637 as tm1637
            self.tm = tm1637.TM1637(clk=Pin(config.PIN_TM_CLK), dio=Pin(config.PIN_TM_DIO))
            self.tm.show_number(8888); time.sleep(0.5); self.tm.clear()
        except: print("[HAL] TM1637 Init Failed")

    def tick(self):
        """维持硬件后台任务 (如数码管刷新)，需要在各种长循环中见缝插针调用"""
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_tick) > 500:
            if self.timer_running and self.tm:
                elapsed = int(time.time() - self.timer_start)
                self.tm.numbers(elapsed, colon=(elapsed % 2 == 0))
            self.last_tick = now

    # --- 计时器硬件控制 ---
    def start_timer(self):
        self.timer_start = time.time()
        self.timer_running = True
        if self.tm: self.tm.numbers(0, colon=True)
        
    def stop_timer(self):
        self.timer_running = False
        return int(time.time() - self.timer_start)
        
    def get_timer_value(self):
        if self.timer_running: return int(time.time() - self.timer_start)
        return -1

    # --- OLED 界面绘制 ---
    def log(self, msg, y=0, clear=True):
        print(f"[HAL] {msg}")
        if self.oled:
            try:
                if clear: self.oled.fill(0)
                safe = ''.join([c for c in str(msg) if ord(c) < 128])
                self.oled.text(safe[:16], 0, y); self.oled.show()
            except: pass

    def show_loading(self, text="Thinking"):
        if not self.oled: return
        for i in range(3):
            self.oled.fill(0)
            self.oled.text(text, 0, 20)
            self.oled.text("." * (i+1), 0, 35)
            self.oled.show()
            for _ in range(5): self.tick(); time.sleep_ms(50)

    def show_pinyin_paged(self, text):
        if self.oled is None or not text: return
        words = text.split(' ')
        lines, curr =[], ""
        for w in words:
            if len(curr + w) < 16: curr += w + " "
            else: lines.append(curr); curr = w + " "
        lines.append(curr)
        
        pages = (len(lines)+4)//5
        for p in range(pages):
            self.oled.fill(0)
            self.oled.text(f">> AI ({p+1}/{pages})", 0, 0)
            self.oled.hline(0, 10, 128, 1)
            for i, line in enumerate(lines[p*5:(p+1)*5]):
                self.oled.text(line, 0, 14+i*10)
            self.oled.show()
            if pages > 1:
                for _ in range(30): time.sleep_ms(100); self.tick()
