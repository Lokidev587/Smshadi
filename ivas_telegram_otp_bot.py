#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ========= PART 1: PERSONAL SETTINGS (EDIT THESE) =========
IVAS_USER_ID = "PASTE_YOUR_IVAS_USER_ID"          # <-- CHANGE
TELEGRAM_BOT_TOKEN = "PASTE_YOUR_TELEGRAM_BOT"    # <-- CHANGE
TELEGRAM_CHAT_ID   = -1001234567890               # <-- CHANGE (your group/channel id, negative for groups)

# ========= PART 2: CONSTANTS (NO NEED TO CHANGE) =========
IVAS_HOST = "ivasms.com:2087"
ORIGIN = "https://www.ivasms.com"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")

# ========= PART 3: IMPORTS =========
import json, re, time, html
from urllib.parse import quote
from datetime import datetime, timezone
import websocket, requests

# ========= PART 4: SMALL HELPERS =========
ISO_COUNTRY = {
    "id":"Indonesia","dz":"Algeria","ci":"Ivory Coast","pe":"Peru","ir":"Iran","de":"Germany",
    "bo":"Bolivia","us":"United States","gb":"United Kingdom","fr":"France","br":"Brazil",
    "in":"India","ru":"Russia","mx":"Mexico",
}
def flag_from_iso(iso:str)->str:
    if not iso or len(iso)!=2: return ""
    a,b=iso.upper()[0],iso.upper()[1]
    return chr(0x1F1E6+(ord(a)-65))+chr(0x1F1E6+(ord(b)-65))
def country_from_label(label:str)->str:
    if not label: return ""
    return re.sub(r"\s*\d+$","",label).strip().title()
def best_country_and_flag(country_iso,label):
    name=ISO_COUNTRY.get((country_iso or"").lower(),"") or country_from_label(label) or "Unknown"
    return name, (flag_from_iso(country_iso) if country_iso else "")
DIGIT_OTP  = re.compile(r"(?:^|[^0-9])(?:G-)?([0-9]{4,8})(?![0-9])")
MASKED_OTP = re.compile(r"\bX{3,6}(?:\sX{3,6})?\b", re.IGNORECASE)
def extract_otp(msg:str)->str:
    if not msg: return "N/A"
    m=DIGIT_OTP.search(msg);  m2=MASKED_OTP.search(msg)
    return m.group(1) if m else (m2.group(0) if m2 else "N/A")
def now_ts()->str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
def ui_html(ts_str,country,flag,service,number,otp,message)->str:
    esc=html.escape
    return (
        f"<b>🔥 {esc(service)} {esc(country)} RECEIVED! ✨</b>\n"
        f"<blockquote>⏰ Time: {esc(ts_str)}</blockquote>\n"
        f"<blockquote>🌍 Country: {esc(country)} {flag}</blockquote>\n"
        f"<blockquote>⚙️ Service: {esc(service)}</blockquote>\n"
        f"<blockquote>☎️ Number: {esc(number)}</blockquote>\n"
        f"<blockquote>🔑 OTP: <code>{esc(otp)}</code></blockquote>\n"
        f"<blockquote>📩 Full Message:</blockquote>\n"
        f"<blockquote>{esc(message)}</blockquote>"
    )
def tg_send(text_html:str):
    url=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r=requests.post(url,json={"chat_id":TELEGRAM_CHAT_ID,"text":text_html,"parse_mode":"HTML","disable_web_page_preview":True},timeout=15)
    if r.status_code!=200: print(f"[TG] {r.status_code} {r.text}")

# ========= PART 5: IVAS SOCKET URL (BUILT EACH RUN) =========
def ws_url(ivas_token:str)->str:
    qs=f"token={quote(ivas_token)}&user={quote(IVAS_USER_ID)}&EIO=4&transport=websocket"
    return f"wss://{IVAS_HOST}/socket.io/?{qs}"

# ========= PART 6: HANDLE ONLY 42/livesms =========
def handle_livesms(arr):
    payload = arr[1] if isinstance(arr,list) and len(arr)>1 else {}
    msg     = payload.get("message","") or ""
    service = payload.get("originator","") or "Unknown"
    number  = payload.get("recipient","") or ""
    ciso    = payload.get("country_iso","") or ""
    label   = payload.get("range","") or ""
    country,flag = best_country_and_flag(ciso,label)
    otp = extract_otp(msg)
    tg_send(ui_html(now_ts(),country,flag,service,number,otp,msg))

# ========= PART 7: MAIN (PROMPT FOR TOKEN, CONNECT, FORWARD) =========
def run_once(ivas_token:str):
    u=ws_url(ivas_token)
    sent_default=False; sent_livesms=False; printed_running=False
    def dec(m): 
        return m.decode("utf-8","replace") if isinstance(m,(bytes,bytearray)) else m
    def on_open(ws): print(f"{now_ts()} [RAW] Connecting ...")
    def on_close(ws,code,msg): print(f"{now_ts()} [RAW] CLOSE code={code} msg={msg}")
    def on_error(ws,err): print(f"{now_ts()} [RAW] ERROR: {err}")
    def on_message(ws,message):
        nonlocal sent_default,sent_livesms,printed_running
        message=dec(message)
        if message.startswith("0") and not sent_default:
            print(f"{now_ts()} [RAW] OPEN")
            print(f"{now_ts()} [RAW] Connected to: {u}")
            print(f"{now_ts()} [RAW] Waiting for Engine.IO open ('0{{...}}') ...")
            prev=message[:120]+("..." if len(message)>120 else "")
            print(f"{now_ts()} [RAW] Engine.IO OPEN: {prev}")
            ws.send("40"); print(f"{now_ts()} [RAW] TX: '40'  (default ns)")
            sent_default=True
            time.sleep(0.05)
            ws.send("40/livesms,"); print(f"{now_ts()} [RAW] TX: '40/livesms,'  (/livesms)")
            sent_livesms=True
            return
        if message=="2": ws.send("3"); return
        if message=="40": print(f"{now_ts()} [RAW] RX: '40'  (ack)"); return
        if message.startswith("40/livesms"):
            print(f"{now_ts()} [RAW] RX: {message}")
            if not printed_running:
                print("Code Running....."); printed_running=True
            return
        m=message.lstrip()
        if m.startswith("42/livesms"):
            try:
                rest=m.split(",",1)[1] if "," in m else "[]"
                arr=json.loads(rest)
                handle_livesms(arr)
            except Exception as e:
                print(f"{now_ts()} [PARSE ERROR] {e} → {message}")
            return
        if m.startswith("42[") or (m.startswith("42/") and not m.startswith("42/livesms")):
            return
    headers=[f"Origin: {ORIGIN}", f"User-Agent: {USER_AGENT}", "Cache-Control: no-cache","Pragma: no-cache"]
    wsapp=websocket.WebSocketApp(u,header=headers,on_open=on_open,on_message=on_message,on_error=on_error,on_close=on_close)
    wsapp.run_forever(origin=ORIGIN, skip_utf8_validation=True)

def main():
    try:
        ivas_token=input("Paste IVAS token: ").strip()
        if not ivas_token:
            print("No token provided."); return
        while True:
            run_once(ivas_token)
            time.sleep(3.0)  # reconnect delay
    except KeyboardInterrupt:
        pass

if __name__=="__main__":
    main()
