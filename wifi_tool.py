import network
import time
import config

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('正在连接WiFi: %s...' % config.WIFI_SSID)
        wlan.connect(config.WIFI_SSID, config.WIFI_PASS)
        # 等待连接，超时处理
        start_time = time.time()
        while not wlan.isconnected():
            time.sleep(1)
            if time.time() - start_time > 15:
                print("WiFi连接超时")
                return False
    print('WiFi已连接, IP地址:', wlan.ifconfig()[0])
    return True
