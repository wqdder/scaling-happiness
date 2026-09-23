import requests
import pyttsx3
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext
import threading

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    winsound = None
    HAS_WINSOUND = False

# ============ 配置区 ============
city_name = "淮安"
# ================================


def get_date_text():
    now = datetime.now()
    return now.strftime("今天是%m月%d日")


def get_time_text():
    now = datetime.now()
    return now.strftime("现在是%H点%M分")


def get_weather(lat=33.55, lon=119.02):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code",
        "daily": "sunrise,sunset,temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": "Asia/Shanghai",
        "forecast_days": 2,
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    weather_map = {
        0: "晴", 1: "多云", 2: "多云", 3: "阴",
        45: "雾", 48: "雾", 51: "毛毛雨", 53: "毛毛雨",
        61: "雨", 63: "雨", 65: "大雨", 80: "阵雨", 95: "雷雨"
    }

    cur = data["current"]
    temp = cur["temperature_2m"]
    feels = cur["apparent_temperature"]
    humidity = cur["relative_humidity_2m"]
    code = cur["weather_code"]
    desc = weather_map.get(code, "未知")

    daily = data["daily"]
    sunrise = daily["sunrise"][0][11:16]
    sunset = daily["sunset"][0][11:16]

    t_max = daily["temperature_2m_max"][1]
    t_min = daily["temperature_2m_min"][1]
    code2 = daily["weather_code"][1]
    desc2 = weather_map.get(code2, "未知")

    return (
        f"{city_name}当前温度{temp}摄氏度，体感{feels}摄氏度，\n"
        f"湿度{humidity}%，{desc}。\n"
        f"日出{sunrise}，日落{sunset}。\n"
        f"明天{desc2}，气温{t_min}到{t_max}摄氏度。"
    )


def speak(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 1800)
    engine.say(text)
    engine.runAndWait()


def beep():
    if HAS_WINSOUND:
        winsound.Beep(1000, 300)


# ============ 全局 ============
text_area = None
busy = False   # 防止连点


def log(msg):
    root.after(0, lambda: _write(msg))


def _write(msg):
    assert text_area is not None
    text_area.config(state=tk.NORMAL)
    text_area.insert(tk.END, msg + "\n")
    text_area.see(tk.END)
    text_area.config(state=tk.DISABLED)


def do_broadcast():
    """真正的播报逻辑，放在后台线程里跑，避免卡界面"""
    global busy
    try:
        date_text = get_date_text()
        time_text = get_time_text()
        try:
            weather_text = get_weather()
        except Exception as e:
            weather_text = "天气获取失败"
            log(f"错误：{e}")

        full_text = f"{date_text}，{time_text}。\n{weather_text}"
        log(full_text)

        try:
            beep()
            speak(full_text)
        except Exception as e:
            log(f"语音播报出错：{e}")
    finally:
        busy = False
        root.after(0, lambda: btn_broadcast.config(state=tk.NORMAL, text="播报一次"))


def on_broadcast():
    global busy
    if busy:
        return
    busy = True
    btn_broadcast.config(state=tk.DISABLED, text="播报中…")
    threading.Thread(target=do_broadcast, daemon=True).start()


def clear_text():
    assert text_area is not None
    text_area.config(state=tk.NORMAL)
    text_area.delete("1.0", tk.END)
    text_area.config(state=tk.DISABLED)


# ============ 界面 ============
root = tk.Tk()
root.title("天气播报")
root.geometry("460x420")
root.minsize(400, 320)

tk.Label(root, text="点一下按钮，播报一次", font=("微软雅黑", 12)).pack(pady=8)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=8)

btn_broadcast = tk.Button(btn_frame, text="播报一次", width=12,
                          font=("微软雅黑", 11), command=on_broadcast)
btn_broadcast.pack(side=tk.LEFT, padx=8)

tk.Button(btn_frame, text="清空", width=10,
          command=clear_text).pack(side=tk.LEFT, padx=8)

tk.Button(root, text="退出", width=10, command=root.destroy).pack(pady=5)

text_area = scrolledtext.ScrolledText(
    root, wrap=tk.WORD, font=("微软雅黑", 10), state=tk.DISABLED
)
text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

root.mainloop()