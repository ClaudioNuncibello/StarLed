import os
import sys

# Aggiungi il path corrente al sys.path
sys.path.insert(0, os.path.abspath('.'))

from app.api.huidu_client import HuiduClient
from app.api.device_api import DeviceApi
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_time():
    host = os.environ.get("HUIDU_GATEWAY_HOST", "127.0.0.1")
    port = int(os.environ.get("HUIDU_GATEWAY_PORT", "30080"))
    sdk_key = os.environ.get("HUIDU_SDK_KEY", "")
    sdk_secret = os.environ.get("HUIDU_SDK_SECRET", "")
    
    client = HuiduClient(host, port, sdk_key, sdk_secret)
    api = DeviceApi(client)
    
    devices = api.get_device_list()
    print("Devices:", devices)
    if not devices:
        return
    dev = devices[0]
    
    props = api.get_device_property(dev)
    print("Current time from props:", props.get("time"))
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Setting time to:", now_str)
    try:
        api.set_device_property(dev, time=now_str)
        print("Success setting time via set_device_property")
    except Exception as e:
        print("Error setting time via set_device_property:", e)
        
    props2 = api.get_device_property(dev)
    print("Time after setting:", props2.get("time"))
    
    # Test XML method SetTimeInfo if needed
    import uuid
    import requests
    import hashlib
    date_str = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    sign_str = sdk_key + date_str
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    
    xml_body = f"""<?xml version='1.0' encoding='utf-8'?>
<sdk guid="{uuid.uuid4()}">
    <in method="SetTimeInfo">
        <time>{now_str}</time>
        <timezone>+01:00</timezone>
    </in>
</sdk>"""
    
    headers = {
        "sdkKey": sdk_key,
        "date": date_str,
        "sign": sign,
        "requestId": str(uuid.uuid4()),
        "Content-Type": "application/xml"
    }
    
    url = f"http://{host}:{port}/raw/{dev}"
    print("Trying XML POST to:", url)
    print("Headers:", headers)
    print("Body:", xml_body)
    try:
        resp = requests.post(url, data=xml_body.encode('utf-8'), headers=headers, timeout=5)
        print("XML Response:", resp.status_code, resp.text)
    except Exception as e:
        print("XML Exception:", e)

if __name__ == "__main__":
    test_time()
