# tm1637.py - 标准驱动库
from machine import Pin
from time import sleep_us

TM1637_CMD1 = 64  # 0x40
TM1637_CMD2 = 192 # 0xC0
TM1637_CMD3 = 128 # 0x80
_SEGMENTS = bytearray(b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x77\x7C\x39\x5E\x79\x71')

class TM1637:
    def __init__(self, clk, dio, brightness=7):
        self.clk = clk
        self.dio = dio
        self.brightness = brightness
        self.clk.init(Pin.OUT, value=0)
        self.dio.init(Pin.OUT, value=0)
        sleep_us(10)
        self._write_data_cmd()
        self._write_dsp_ctrl()

    def _start(self):
        self.dio(0)
        sleep_us(50)
        self.clk(0)
        sleep_us(50)

    def _stop(self):
        self.dio(0)
        sleep_us(50)
        self.clk(1)
        sleep_us(50)
        self.dio(1)

    def _write_data_cmd(self):
        self._start()
        self._write_byte(TM1637_CMD1)
        self._stop()

    def _write_dsp_ctrl(self):
        self._start()
        self._write_byte(TM1637_CMD3 | 8 | self.brightness)
        self._stop()

    def _write_byte(self, b):
        for i in range(8):
            self.dio((b >> i) & 1)
            sleep_us(10)
            self.clk(1)
            sleep_us(10)
            self.clk(0)
            sleep_us(10)
        self.clk(0)
        sleep_us(10)
        self.clk(1)
        sleep_us(10)
        self.clk(0)

    def numbers(self, num, colon=False):
        # 自动转换成 分:秒 (MM:SS) 格式
        num = int(num)
        minutes = num // 60
        seconds = num % 60
        self.show_clock(minutes, seconds, colon)

    def show_clock(self, h, m, colon=False):
        seg_data = bytearray([
            _SEGMENTS[h // 10],
            _SEGMENTS[h % 10],
            _SEGMENTS[m // 10],
            _SEGMENTS[m % 10]
        ])
        if colon:
            seg_data[1] |= 128 # 点亮冒号
        self._start()
        self._write_byte(TM1637_CMD2)
        for seg in seg_data:
            self._write_byte(seg)
        self._stop()
        self._write_dsp_ctrl()

    def show_number(self, num):
        # 显示纯数字 0-9999
        num = int(num)
        if num > 9999: num = 9999
        seg_data = bytearray([
            _SEGMENTS[(num // 1000) % 10],
            _SEGMENTS[(num // 100) % 10],
            _SEGMENTS[(num // 10) % 10],
            _SEGMENTS[num % 10]
        ])
        self._start()
        self._write_byte(TM1637_CMD2)
        for seg in seg_data:
            self._write_byte(seg)
        self._stop()
        self._write_dsp_ctrl()

    def clear(self):
        self._start()
        self._write_byte(TM1637_CMD2)
        for i in range(4):
            self._write_byte(0)
        self._stop()
        self._write_dsp_ctrl()
