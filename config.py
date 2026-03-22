# ==========================================
# MicroZhi Project Configuration
# ==========================================

# 1. 网络配置
WIFI_SSID = "Your_WIFI_SSID"
WIFI_PASSWORD = "Your_WIFI_PASSWORD"

# 2. 云服务 API Keys
BAIDU_ASR_API_KEY = "your_baidu_asr_key"
BAIDU_ASR_SECRET_KEY = "your_baidu_asr_secret"
BAIDU_TTS_API_KEY = "your_baidu_tts_key"
BAIDU_TTS_SECRET_KEY = "your_baidu_tts_secret"
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxx"
SENIVERSE_KEY = "your_seniverse_key"

# 3. 硬件引脚映射 (Pin Mapping)
PIN_OLED_SCL = 22
PIN_OLED_SDA = 21
PIN_TM_CLK = 17
PIN_TM_DIO = 5
PIN_ASR_WAKE = 13
PIN_I2S_SCK = 32   # Mic SCK
PIN_I2S_WS = 25    # Mic WS
PIN_I2S_SD = 33    # Mic SD
PIN_SPK_BCLK = 27  # Speaker BCLK
PIN_SPK_LRC = 26   # Speaker LRC
PIN_SPK_DIN = 19   # Speaker DIN

# 4. 算法与系统参数
SILENCE_THRESHOLD_OFFSET = 800  # VAD 底噪灵敏度偏移
SILENCE_DURATION = 0.6          # 语音停顿切分时间(秒)
MAX_RECORD_TIME = 10            # 最大录音时长(秒)
