# config.py - 配置文件

# 1. WiFi 设置
WIFI_SSID = "Your_WIFI_SSID"
WIFI_PASSWORD = "Your_WIFI_PASSWORD"

# 2. 百度语音识别 API 设置
BAIDU_ASR_API_KEY = "your_baidu_asr_key"
BAIDU_ASR_SECRET_KEY = "your_baidu_asr_secret"

# === 2. 语音合成 (TTS) 配置 ===
BAIDU_TTS_API_KEY = "your_baidu_tts_key"
BAIDU_TTS_SECRET_KEY = "your_baidu_tts_secret" 

#deepseek调用api思考
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxx"

#天气
SENIVERSE_KEY = "your_seniverse_key" 

# 3. 硬件引脚定义
PIN_ASR_WAKE = 13 

# INMP441 麦克风 (I2S)
PIN_I2S_SCK = 14
PIN_I2S_WS = 15
PIN_I2S_SD = 32

# OLED 显示屏 (I2C)
PIN_OLED_SCL = 22
PIN_OLED_SDA = 21

# MAX98357
PIN_SPK_LRC = 26   
PIN_SPK_BCLK = 27  
PIN_SPK_DIN = 19   

#TM1637
PIN_TM_CLK = 17
PIN_TM_DIO = 5

# 4. 录音参数
SILENCE_THRESHOLD = 800  # 静音阈值，低于此数值判定为静音（根据环境噪音修改）
SILENCE_DURATION = 0.7   # 停顿超过多少秒视为说话结束
MAX_RECORD_TIME = 6      # 最大录音时长（秒），防内存溢出
