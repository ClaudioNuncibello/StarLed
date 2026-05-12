import os, sys, uuid, requests, hashlib, hmac, time
sys.path.insert(0, os.path.abspath('.'))
try:
    from dotenv import load_dotenv
    load_dotenv()
except: pass
from datetime import datetime
host = os.environ.get('HUIDU_GATEWAY_HOST', '192.168.1.33')
port = int(os.environ.get('HUIDU_GATEWAY_PORT', '30080'))
sdk_key = os.environ.get('HUIDU_SDK_KEY', '')
sdk_secret = os.environ.get('HUIDU_SDK_SECRET', '')
dev = 'C16L-D25-00724'
date_str = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
for m in ['SetTimeInfo', 'SetRTC', 'SyncTime', 'SetClock', 'SetTime', 'setDeviceProperty']:
    xml_body = f"<?xml version='1.0' encoding='utf-8'?><sdk guid='{uuid.uuid4()}'><in method='{m}'><time>2026-05-12 15:00:00</time></in></sdk>"
    sign_str = xml_body + sdk_key + date_str
    sign = hmac.new(sdk_secret.encode(), sign_str.encode(), hashlib.md5).hexdigest()
    headers = {'sdkKey': sdk_key, 'date': date_str, 'sign': sign, 'requestId': str(uuid.uuid4()), 'Content-Type': 'application/xml'}
    try:
        r = requests.post(f'http://{host}:{port}/raw/{dev}', data=xml_body.encode('utf-8'), headers=headers, timeout=5)
        print(f'{m} -> {r.text}')
    except Exception as e:
        print(f'{m} -> Error: {e}')
