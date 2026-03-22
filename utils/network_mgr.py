import network
import time
import ntptime
import config

class NetworkManager:
    def __init__(self, hal):
        self.wlan = network.WLAN(network.STA_IF)
        self.hal = hal

    def connect(self):
        self.wlan.active(True)
        if not self.wlan.isconnected():
            self.hal.log("Connecting WiFi...")
            try:
                self.wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
                for _ in range(15):
                    if self.wlan.isconnected(): break
                    time.sleep(1)
            except: pass
        
        if self.wlan.isconnected():
            try:
                ntptime.host = 'ntp.aliyun.com'
                ntptime.settime()
                print("NTP Synced.")
            except: pass
            return True
        return False
