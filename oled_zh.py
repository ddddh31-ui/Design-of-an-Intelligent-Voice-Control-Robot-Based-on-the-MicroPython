import framebuf
import os

class OLED_ZH:
    def __init__(self, oled, font_file='font.bin'):
        self.oled = oled
        self.font_file = font_file
        self.font_valid = False
        try:
            # 检查字库文件是否存在
            if font_file in os.listdir():
                self.font_valid = True
                print(f"[OLED] Font file '{font_file}' found.")
            else:
                print(f"[OLED] Warning: '{font_file}' not found. Chinese will be ignored.")
        except:
            pass

    def get_gb2312_offset(self, char):
        """简单的 UTF-8 转 GB2312 计算偏移量 (需要标准GB2312字库)"""
        # 注意：MicroPython 默认不支持 .encode('gb2312')
        # 这里使用一种简化的映射或直接报错降级。
        # 由于 MP 缺乏 GB2312 编码器，这里为了通用性，
        # 如果没有专门的转码库，只能建议显示英文或数字。
        # *** 也就是：真要在 OLED 显示任意中文，需要配合庞大的 unicode 映射表 ***
        return -1

    def text(self, string, x, y):
        """
        混合显示中文和英文
        注意：在没有 Unicode->GB2312 映射表的情况下，MicroPython 很难直接显示中文。
        如果必须显示中文，建议使用 PCtoLCD 取模工具生成特定汉字的字模。
        
        ** 这里为了稳定性，如果检测不到中文环境，将只过滤显示 ASCII **
        """
        current_x = x
        for char in string:
            # 判断是否为 ASCII
            if ord(char) < 128:
                self.oled.text(char, current_x, y)
                current_x += 8
            else:
                # 如果是中文，且有字库支持（这里极其复杂，通常建议看串口）
                # 为了不让程序崩溃，用一个方框或 ? 代替中文
                self.oled.text("?", current_x, y)
                current_x += 8
                
    def show_result(self, text):
        """智能显示识别结果"""
        self.oled.fill(0)
        
        # 1. 优先在 OLED 显示 "Done" 和截断的拼音/英文
        self.oled.text("Result:", 0, 0)
        
        # 尝试简单的过滤
        ascii_text = ""
        has_chinese = False
        for c in text:
            if ord(c) < 128:
                ascii_text += c
            else:
                has_chinese = True
        
        if has_chinese:
            # 如果有中文，屏幕提示看串口，并显示部分内容
            self.oled.text("See Serial...", 0, 16)
            self.oled.text(">> " + ascii_text[:10], 0, 32)
        else:
            # 纯英文直接显示
            self.oled.text(ascii_text[:16], 0, 16)
            if len(ascii_text) > 16:
                self.oled.text(ascii_text[16:32], 0, 28)
                
        self.oled.show()
