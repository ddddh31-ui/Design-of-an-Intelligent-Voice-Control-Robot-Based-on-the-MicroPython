import time
import urequests

def get_current_date_str():
    t = time.localtime(time.time() + 8 * 3600)
    w_day =["周一", "周二", "周三", "周四", "周五", "周六", "周日"][t[6]]
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
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={ak}&client_secret={sk}"
        res = urequests.post(url)
        token = res.json().get("access_token")
        res.close()
        return token
    except: return None
