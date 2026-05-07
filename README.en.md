# Shenzhen Huidu Technology Co., Ltd. Device HTTP API Description


| Update Time| Modified by | illustrate                               | Remark                                            |
| ---------- | ------      | --------                                 | ----------------------------------------------- |
| 2025/08/05 | tanglin     |   3.2 Program General Interface   | Added blinking effect to effect node<br>Supplementary supported models:<br>Regular series (ARM/Linux platform): C16L, C08L, D16, D36, ...<br>Android series (Android platform): A3L, A4L, A5L, A6L, H4K, H8, B8L, A7, A8, ...<br>Android series needs to upgrade to the latest firmware |
| 2025/08/07 | tanglin     |   3.2.6 Text Program                          | Added a new voice broadcast attribute, PlayText|


# 1 Document Introduction

## 1.1 Reading Target
The development, maintenance and management personnel of your company's technical department should have the following basic knowledge：
1. Understand HTTPS/HTTP protocols and other content.
2. Understand the basic concepts of information security.
3. Understand at least one computer programming language.

## 1.2 Product Overview
This development manual describes the system's functional interfaces in detail. 
This guide provides a comprehensive understanding of the system, enabling technical personnel to quickly master the system's interfaces and develop on the system.
Huidu Technology's equipment secondary development, the flow chart is as follows

 **Access the gateway service (Ubuntu/Windows) through the SDK to control the device** 

![image.png](https://img.cdn.apipost.cn/client/user/1172252/avatar/78805a221a988e79ef3f42d7c5bfd41867a5aabd619aa.png "image.png")

 **Directly access the device through the SDK** 

![image.png](https://img.cdn.apipost.cn/client/user/1172252/avatar/78805a221a988e79ef3f42d7c5bfd41867a5aac5460e3.png "image.png")

## 1.3 Directory structure
~~~
cn/huidu/device/sdk
├── doc                                              // interface debugging project files
├── java                                             // Java Development Kit
│       └── demo/src/main/java/cn/huidu/device/demo  // Sample Code
│           └── demo0_based                          // Get online equipment
│           └── demo1_deviceInfod                    // Device operations (get device information, modify device information, restart device)
│           └── demo2_task                           // Task interface (active push, scheduled tasks)
│           └── demo3_baseProgram                    // Programs (text, pictures, videos, digital clock, analog clock)
│           └── demo4_multiProgram                   // Multiple programs
│           └── demo5_dynamicContent                 // Dynamic updates (frequent updates)
│           └── demo6_multiAreaProgramSwitch         // Multi-region
│       └── sdk/src/main/java/cn/huidu/device/sdk    // Interface module                                           
│           └── common                               // Common modules
│               └── BaseClient.java                  // Core Module
│               └── Config.java                      // Launch Configuration
│               └── HttpApi.java                     // http interface (POST, GET, MD5, etc.)
│           └── data                                 // Data content
│               └── program                          // Program related
│               └── task                             // Task related
│           └── deviceTask                           // Device Tasks
│               └── PeriodicTask.java                // Scheduled tasks
│               └── PushStatusTask.java              // Active push
│               └── ScheduledTask.java               // Planned Tasks
│           └── Device.java                          // Device Interface
│           └── File.java                            // File Interface
│           └── Program.java                         // Program Interface
├── c                                                // C Development Kit
├── python                                           // Python development package
├── tools                                            // Support Tools
~~~

# 2 Preliminary preparation
## 2.1 Devices with a D in the middle of their ID are engineering cards. Non-engineering cards do not support secondary development.

例如：Standard Series C16L-D00-A000F

![输入图片说明](doc/images/id.png)

## 2.2 Verify HTTP SDK functionality [Just upgrade to the latest firmware for the Android series and skip this step.]


Using the SDK test tool, send the following command to query the status.

Note: Enabling the HTTP SDK will take over certain standard functions to ensure full HTTP control. 
After enabling it, some settings in other software (e.g., HDPlayer) may not take effect, such as scheduled power on/off.

![image.png](https://img.cdn.apipost.cn/client/user/1172252/avatar/78805a221a988e79ef3f42d7c5bfd41867a5ae332a291.png "image.png")

Retrieve HTTP SDK Status

Request:
```js
<?xml version='1.0' encoding='utf-8'?>
<sdk guid="##GUID">
    <in method="GetHttpApiEnable"/>
</sdk>
```
Response:
```js
<?xml version="1.0" encoding="utf-8"?>
<sdk guid="19aa000a54d79ce835655d855f109a97">
    <out result="kSuccess" method="GetHttpApiEnable">
        <func enable="true"/>
    </out>
</sdk>
```


Set HTTP SDK Status

Request:
```js
<?xml version='1.0' encoding='utf-8'?>
<sdk guid="##GUID">
    <in method="SetHttpApiEnable">
        <func enable="true"/>
    </in>
</sdk>
```
Response:
```js
<?xml version="1.0" encoding="utf-8"?>
<sdk guid="7b1b1e7dba5363fc651dc1dc72f949d5">
    <out method="SetHttpApiEnable" result="kSuccess"/>
</sdk>
```


## 2.3 Platform Registration

When customers need to operate the equipment, they must register through the GrayScale Technology Developer Platform to obtain the corresponding SDK Key and SDK Secret.

 **The platform is not yet open for early access. Please provide the following information to contact Huayu to obtain your SDK Key and SDK Secret.** 

![输入图片说明](doc/images/registered.png)


## 2.4 Signature Mechanism

1.During the initial setup of the device, the developer's SDKKey and corresponding SDKSecret must be initialized on the device via the “/api/sdkkey/” interface.

2.When developing using the SDK, the SDK version must be less than or equal to the device's API version number.

All API calls are signed using the SDKKey and SDKSecret (keys are not transmitted), ensuring data integrity and legitimacy while facilitating log tracing. Two signing rules apply as follows:

Rule 1 (General):

sign = HMACMD5(body+sdkKey+date, sdkSecret)

```js
Among them：
    body：All content within the requested data body;  
    date：Current client time, HTTP header field;  
    sdkKey：Developer SDK ID registered during development, HTTP header field;    
    sdkSecret： Key corresponding to the registered developer SDK ID, not transmitted (do not disclose to others);
    sign：Computed signature field added to the request header, HTTP header field;
```


Rule 2 (File Interface Only):

sign = HMACMD5(sdkKey+date, sdkSecret)

```js
Among them： 
     date： The client's current time, HTTP header field;
     sdkKey：The developer SDK ID registered during development, HTTP header field;
     sdkSecret：The key corresponding to the registered developer SDK ID, not transmitted (do not disclose to others);
     sign：The calculated signature field added to the request header, HTTP header field;
```

Signature example request header, such as:

```js
requestId: da7ddf89-c102-4fb4-95e7-a8f7a72e697e
sdkKey: xxxxxxxxxxxxxxxxxxxxx
date: Wed, 09 Aug 2023 07:27:44 GMT
sign: 371b45207ecc8ea993a1468caf7d8bec
Content-Type: application/json
Accept: */*
Host: sdk.huidu.cn
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
Content-Length: 72
```

When using for the first time, you must initialize the device's SDK key and corresponding SDK secret.

Method 1: Initialize via web interface (URL: Control card IP:30080/login/). If this page fails to display, it may be browser-related; try a different browser.

![输入图片说明](doc/images/webPageInit.png)

Method Two: Initialization via Interface

The following error indicates that **once initialized, it cannot be initialized again. Only one addition is permitted to prevent arbitrary additions**. 

![输入图片说明](doc/images/init.png)

## 2.5 Development Environment Configuration

### 2.5.1 Java Development Kit

1. Install the development environment. We recommend using[vscode](https://vscode.js.cn/Download)

2. Install the JDK; we recommend using[jdk21](https://www.oracle.com/cn/java/technologies/downloads/);

3. Install Maven. We recommend using[apache-maven-3.9.10](https://mirrors.aliyun.com/apache/maven/maven-3/)以上版本;

4. Configure Maven Path；

 **Note: Before running the demo, build the SDK library with “mvn clean install”."** 

### 2.5.2 C Development Kit

1. Official Website Download[CMake](https://cmake.org/download/)

### 2.5.3 Python Development Kit

1. Install the development environment. We recommend using[PyCharm](https://www.jetbrains.com.cn/pycharm/)

2. Install Python, recommended to use[Python 3.9.1](https://www.python.org/downloads/)

3. Install dependency packages/libraries[pip install requests; pip install requests-toolbelt]

# 3 API Interface Specification (JSON)

## 3.1 Universal Device Interface
Request：POST /api/device/

Different methods correspond to different parameters, where “method” is the method name and “data” corresponds to the parameter.

The device ID for the operation can be found in the URL or within the JSON data in the request body, following these rules:

1.No id specified： /api/device/ Indicates operating the local device

2.url： /api/device/C16-D23-A0001,C16-D23-A0002

3.url： /api/device/?id=C16-D23-A0001,C16-D23-A0002

### 3.1.1 Retrieve the list of online devices

Interface URL：127.0.0.1:30080/api/device/list/

Content-Type：application/json

Request Method: GET

Request Header Parameters:

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) Example：


```None
```


Return to Example：

```
{
    "total": "1",
    "message": "ok",
    "data": [
    "C16-D00-A000F"
    ]
}
```



### 3.1.2 Retrieve device properties

Interface URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request Method：POST

Request Header Parameter Description：

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) Example：


```
{
    "method": "getDeviceProperty",
    "data": []
}
```

Return to Example：

```
{
	"method": "getDeviceProperty",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": {
				"name": "BoxPlayer",
				"sync": "false",
				"screen.width": "128",
				"screen.height": "64",
				"screen.rotation": "0",
				"version.hardware": "HD-C16L-V1.X",
				"version.fpga": "16.12.0.0",
				"version.app": "7.10.78.1",
				"time": "2025-07-08 17:05:06",
				"time.timeZone": "Asia/Shanghai;UTC+08:00;Beijing,Chongqing,HongKong,Urumchi",
				"time.sync": "none",
				"volume": "100",
				"volume.mode": "default",
				"luminance": "100",
				"luminance.mode": "default",
				"eth.dhcp": "false",
				"eth.ip": "192.168.90.153",
				"gsm.apn": "3gnet",
				"wifi.enabled": "true",
				"wifi.mode": "ap",
				"wifi.ap.ssid": "C16L-D00-A000F",
				"wifi.ap.passwd": "hd12345678",
				"wifi.ap.channel": "5"
			}
		}
	]
}
```

```js
name                  // Device Name
screen.width          // Screen width
screen.height         // Screen height
version.hardware      // Hardware Version
version.fpga          // FPGA version
version.kernel        // Kernel Version
version.app           // Application Version (Firmware Version)
time                  // Time
time.timeZone         // Time zone
volume                // Volume
volume.mode           // Volume Mode
luminance             // Brightness
luminance.mode        // Brightness Mode
eth.dhcp                // dhcp
eth.ip                  // IP address
gsm.apn                 // Mobile network APN
wifi.valid              // Is there a Wi-Fi module for connectivity?
wifi.enabled            // Enable Wi-Fi
wifi.mode               // Wi-Fi Mode
wifi.ap.ssid            // Wi-Fi AP Mode Name
wifi.ap.passwd          // Wi-Fi AP Mode passwd
wifi.ap.channel         // Channel for Wi-Fi AP mode
…
```


### 3.1.3 Update device properties

Certain properties cannot be modified (read-only properties).

接口URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request Method: POST

Request Header Parameter Description：

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) Example：


```
{
    "method": "setDeviceProperty",
    "data": {
    "name": "BoxPlayer1",
    "screen.width": "512",
    "screen.height": "320",
    "volume": "60",
    "luminance": "80"
    }
}
```


Return to Example：

```
{
    "method": "setDeviceProperty",
    "message": "ok",
    "data": [
        {
            "id": "C16-D00-A000F",
            "message": "ok",
            "data": "kSuccess"
        }
    ]
}
```


### 3.1.4 Retrieve device status

Interface URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request Method: POST

Request Header Parameter Description:

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) Example:


```
{
    "method": "getDeviceStatus",
    "data": []
}
```


Return example:

```
{
	"method": "getDeviceStatus",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": {
				"screen.openStatus": "true",
				"eth.valid": "true",
				"eth.dhcp": "false",
				"eth.ip": "192.168.90.153",
				"gsm.valid": "true",
				"gsm.apn": "3gnet",
				"gsm.manufacturer": "Quectel",
				"gsm.version": "EC200TCNDAR02A15M16",
				"gsm.model": "EC200T",
				"gsm.imei": "862815031598210",
				"gsm.signal": "0",
				"gsm.dbm": "0",
				"gsm.insert": "false",
				"gsm.status": "init",
				"gsm.network": "init",
				"gsm.code": "128",
				"wifi.valid": "true",
				"wifi.enabled": "true",
				"wifi.mode": "ap"
			}
		}
	]
}
```

```js
screen.openStatus       // Screen open status: {“true”: Opened, “false”: Closed}
eth.valid               // Is the wired network connected? {“true”: Connected, “false”: Not connected}, no details provided when false
eth.dhcp                // “true” (DHCP-obtained IP address), “false” (static IP address)
eth.ip                  // IP address

gsm.valid               // Whether to use mobile network to connect to the Internet
gsm.apn                 // Mobile network APN
gsm.manufacturer        // Module manufacturer
gsm.version             // Module version
gsm.model               // Module model
gsm.imei                // Module IMEI
gsm.imsi                // SIM卡imsi
gsm.iccid               // SIM卡iccid
gsm.number              // SIM card phone number
gsm.operators           // Operator
gsm.signal              // Signal strength, value range [1, 5]; 1 means the worst signal strength; 5 means the best signal strength
gsm.dbm                 // Signal strength (in dBm)
gsm.insert              // Is the SIM card inserted?
gsm.status              // Network registration status
gsm.network             // Network standard value range {"init" (initialization state), "unknow" (unknown network), "2G" (2G), "2.5G" (2.5G), "3GPP" (3GPP family), "3G TD" (Mobile 3G), "3.5G HSDPA", "3.5G HSUPA", "3.5G HSPAPlus", "4G LTE", "4G TDD", "4G FDD"}
wifi.valid              // Is there a Wi-Fi module connected?
wifi.enabled            // Is Wi-Fi enabled?
wifi.mode               // Wi-Fi mode
wifi.ap.ssid            // Name of the Wi-Fi AP mode
wifi.ap.passwd          // Wi-Fi AP mode password
wifi.ap.channel         // Wi-Fi AP mode channel
wifi.ap.encryption      // Wi-Fi AP mode encryption method (fixed value "WPA-PSK")

…
```

### 3.1.5 Get scheduled tasks

Interface URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

1.screen: Switch screen

2.volume:volume

3.luminance:Brightness

4.relay : relay

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |


Request (Body) example:


```
{
	"method": "getScheduledTask",
	"id": "C16-D00-A000F",
	"data": [
		"screen",
		"volume",
		"luminance",
		"relay"
	]
}
```


Return example:

```
{
    "message": "ok",
    "data": {
        "luminance": [
            {
                "timeRange": "08:00:00~18:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "WeekFilter": "Mon,Tue,Wed",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "80"
            },
            {
                "timeRange": "18:00:00~08:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "WeekFilter": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "60"
            }
        ],
        "volume": [
            {
                "timeRange": "08:00:00~18:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "WeekFilter": "Mon,Tue,Wed",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "80"
            }
        ],
        "screen": [
            {
                "timeRange": "00:00:00~06:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "false"
            },
            {
                "timeRange": "06:00:00~00:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "true"
            }
        ],
        "relay": [
            {
                "timeRange": "08:00:00~18:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "true"
            }
        ]
    }
}
```


### 3.1.6 Update scheduled tasks

Interface URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

“setScheduledTask”,Replace all existing items

“updateScheduledTask”，Update transferred items

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) example:


```
{
    "method": "setScheduledTask",
    "data": {
        "luminance": [
            {
                "timeRange": "08:00:00~18:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "WeekFilter": "Mon,Tue,Wed",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "80"
            },
            {
                "timeRange": "18:00:00~08:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "WeekFilter": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "60"
            }
        ],
        "volume": [
            {
                "timeRange": "08:00:00~18:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "WeekFilter": "Mon,Tue,Wed",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "80"
            }
        ],
        "screen": [
            {
                "timeRange": "00:00:00~06:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "false"
            },
            {
                "timeRange": "06:00:00~00:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "true"
            }
        ],
        "relay": [
            {
                "timeRange": "08:00:00~18:00:00",
                "dateRange": "2023-10-01~2023-10-11",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "true"
            }
        ]
    }
}
```


Return example:

```
{
	"method": "setScheduledTask",
	"message": "ok",
	"data": [{
		"id": "C16-D00-A000F",
		"message": "ok",
		"data": "kSuccess"
	}]
}
```


### 3.1.7 Get scheduled tasks

Interface URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

Polling tasks are mainly used to obtain external data to update the relevant status of the device, switch programs and areas, update area data, etc.

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2 | String                |     yes | No description available  |

Request (Body) Description:
| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| url     | xxxxxxxxxxxx     | String                |     yes | The address of the data source |
| rege    |                  | String  Default value: none     |     no | Regular expression<br>Parse data into key-value pairs, with keys and values ​​separated by commas ","<br>Multiple sets of key values ​​are separated by line breaks "\n" |
| interval|                  | Int [3 – 3600 seconds] Default: 30 |  no | Polling interval, in seconds |

Request (Body) example:

```
{
    "method": "getPeriodicTask",
    "data": [
    ]
}
```


Return example:

```
{
    "method": "getPeriodicTask",
    "message": "ok",
    "data": [
        {
            "id": "C16-D21-015BD",
            "message": "ok",
            "data": [
                {
                    "url": "xxxxxxxxxxxx",
                    "rege": "",
                    "interval": "29"
                },
                {
                    "url": "xxxxxxxxxxxx",
                    "rege": "",
                    "interval": "29"
                }
            ]
        }
    ]
}
```


### 3.1.8 Update scheduled tasks

Interface URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description: Mainly used to set external data to update the relevant status of the device, used to switch programs and regions, update regional data, etc.

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) Description:
| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| url     | xxxxxxxxxxxx     | String                |   yes | The address of the data source |
| rege    |                  | String  Default value: none    |     no | Regular expression<br>Parse data into key-value pairs, with keys and values ​​separated by commas ","<br>Multiple sets of key values ​​are separated by line breaks "\n" |
| interval|                  | Int [3 – 3600 seconds] Default: 30 |  no | Polling interval, in seconds |

Request (Body) example:

```
{
    "method": "setPeriodicTask",
    "data": [
    		{
    			"url": "xxxxxxxxxxxx",
    			"rege": "",
    			"interval": "29"
    		},
    		{
    			"url": "xxxxxxxxxxxx",
    			"rege": "",
    			"interval": "29"
    		}
    	]
}
```


Return example:

```
{
	"method": "setPeriodicTask",
	"message": "ok",
	"data": {
		"id": "C16-D00-A000F",
		"message": "ok",
		"data": "kSuccess"
	}
}
```


### 3.1.9 Active push

Interface URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description: Actively push tasks, used to switch programs and regions, update regional data, etc.

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) example:


```
{
    "method": "pushStatus",
    "data": [
        {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
    ]
}
```


Return example:

```
{
	"method": "pushStatus",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```



### 3.1.10 Restart the device

Interface URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description: Restart after a few seconds

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) example:


```
{
    "method": "rebootDevice",
    "data": {
    	"delay": 5
    }
}
```


Return example:

```
{
	"method": "rebootDevice",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```


### 3.1.11 Turn on the screen

接口URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) example:


```
{
    "method": "openDeviceScreen",
    "data": {}
}
```


Return example:

```
{
	"method": "openDeviceScreen",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```


### 3.1.12 Turn off the screen


Interface URL：127.0.0.1:30080/api/device/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) example:


```
{
    "method": "closeDeviceScreen",
    "data": {}
}
```


Return example:

```
{
	"method": "closeDeviceScreen",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```


## 3.2 Program Universal Interface

The program interface is mainly used to operate program-related content

All program operation related interfaces are based on this interface;

Request：POST /api/program/

Different methods correspond to different parameters, "method" is the method name, and "data" corresponds to the parameters;

The device ID of the operation can be in the URL or the body JSON data. The rules are as follows:

1.No id specified： /api/program/ Indicates operating the local device

2.url： /api/program/C16-D23-A0001,C16-D23-A0002

3.url： /api/program/?id=C16-D23-A0001,C16-D23-A0002

```js
{
    "method": "[append|remove|update|replace|getAll]",
    "data": {},
    "id": "C16-D23-A0001,C16-D23-A0001"
}
```

**Program Structure**

Program data is carried and represented in JSON format; program objects mainly consist of: program, area, image, video, text, digitalClock, etc. The relationship between objects is shown in the following request data;

1.Multiple programs are composed of multiple program object arrays;

2.A program object consists of one or more area objects. The program is used to control content switching, specify time, date, and other broadcast control information.

3.The area object consists of one or more content objects (currently supports image, text, video, digitalClock, dialClock, and dynamic). The function of area is to specify the display position and size.

4.The content object is the object that is ultimately displayed. Different objects have different functions, such as: text, which displays text content, image, which displays image content, and so on.

Effect Node Description
| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|
| type | Int <br>0 : Direct display.<br>1 : Shift left.<br>2 : Shift right.<br>3 : Shift up.<br>4 : Shift down.<br>5 : Overlay left.<br>6 : Overlay right.<br>7 : Overlay up.<br>8 : Overlay down.<br>9 : Overlay top left.<br>10 : Overlay bottom left.<br>11 : Overlay top right.<br>12 : Overlay bottom right.<br>13 : Horizontal opening.<br>14 : Vertical opening.<br>15 : Horizontal closing.<br>16 : Vertical closing.<br>17 : Fade in and out.<br>18 : Vertical blinds.<br>19 : Horizontal blinds.<br>20 : Do not clear the screen.<br>25: Random special effects.<br>// The following special effects are only supported by text plug-ins.<br>26: Continuous left movement with one end to the other.<br>27: Continuous right movement with one end to the other.<br>28: Continuous up movement with one end to the other.<br>29: Continuous down movement with one end to the other.<br>30: Flashing. | Yes | Special Effect Type |
| speed | Int[0-8] 0 is the fastest, 8 is the slowest | Yes | MD5 value of the file |
| hold | Int[0-9999999] Unit is milliseconds | Yes | Hold time |

font node description
| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|
| bold | Bool | No | Bold |
| italic | Bool | No | Italic |
| underline | Bool | false | underline |
| size | Int | No | font size |
| color | Color #RRGGBB | No | Font color |
| name | String | No | Font name |

border node description
| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|
| index | String| Yes | Built-in border image index |
| effect | String| Yes| Border effects (rotate, twinkle, static)|
| speed | String| Yes | Border speed (1~10) |

### 3.2.1 Playback Controls

```
"playControl": {
    "duration": "00:00:30",
    "time": {
        "start": "00:00:00",
        "end": "06:00:00"
    },
    "week": {
        "enable": "Mon, Tue, Wed, Thur"
    },
    "date": [
        {
            "start": "2023-10-01",
            "end": "2024-10-01"
        }
    ],
    "time": [
        {
            "start": "00:00:00",
            "end": "16:27:00"
        },
        {
            "start": "16:28:00",
            "end": "18:00:00"
        }
    ]
}
```


### 3.2.2 Get the program

Interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) Example：


```
{
    "method": "getAll",
    "data": [],
    "id": "C16-D00-A000F"
}
```


Return to example：

```
{
    "method": "getAll",
    "message": "ok",
    "data": [
        {
            "id": "C16L-D00-A000F",
            "message": "ok",
            "data": {
                "item": [
                    {
                        "uuid": "2A7C2C2C-B2E3-475C-A501-0A3B7E6451E3",
                        "name": "节目2"
                    }
                ]
            }
        }
    ]
}
```

### 3.2.3 Update program

Interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) example:


```
{
    "method": "update",
    "data": [
        {
            "name": "节目2",
            "type": "normal",
            "uuid": "A4",
            "area": [
                {
                    "uuid": "B3",
                    "x": 0,
                    "y": 0,
                    "width": 128,
                    "height": 64,
                    "border": {
                        "type": 0,
                        "speed": 5,
                        "effect": "rotate"
                    },
                    "item": [
                        {
                            "uuid": "C2",
                            "type": "text",
                            "string": "LED",
                            "multiLine": false,
                            "font": {
                                "name": "宋体",
                                "size": 14,
                                "underline": false,
                                "bold": false,
                                "italic": false,
                                "color": "#ffff00"
                            },
                            "effect": {
                                "type": 0,
                                "speed": 5,
                                "hold": 5000
                            }
                        }
                    ]
                }
            ]
        }
    ]
}
```


Return example:

```
{
    "method": "update",
    "message": "ok",
    "data": [
        {
            "id": "C16L-D00-A000F",
            "message": "ok",
            "data": "kSuccess"
        }
    ]
}
```

### 3.2.4 Add Additional Programs

Interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) Example：


```
{
    "method": "append",
    "data": [
        {
            "name": "节目1",
            "type": "normal",
            "uuid": "A4",
            "area": [
                {
                    "x": 0,
                    "y": 0,
                    "width": 128,
                    "height": 64,
                    "item": [
                        {
                            "type": "text",
                            "string": "显示屏",
                            "multiLine": false,
                            "font": {
                                "name": "宋体",
                                "size": 14,
                                "underline": false,
                                "bold": false,
                                "italic": false,
                                "color": "#ffff00"
                            },
                            "effect": {
                                "type": 0,
                                "speed": 5,
                                "hold": 5000
                            }
                        }
                    ]
                }
            ]
        }
    ]
}
```


Return example:

```
{
    "method": "append",
    "message": "ok",
    "data": [
        {
            "id": "C16L-D00-A000F",
            "message": "ok",
            "data": "kSuccess"
        }
    ]
}
```

### 3.2.5 Remove program

Interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description:

| Parameter name | Example value  | Parameter Type  | Is this field required?  | Parameter Description  |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) example:


```
{
    "method": "remove",
    "data": [
        {
            "name": "节目2",
            "uuid": "A3"
        },
        {
            "name": "节目1",
            "uuid": "A4"
        }
    ]
}
```


Return example:

```
{
	"method": "remove",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```

### 3.2.6 Text Program

Interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) Description:
| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| type     |   text   | String                |     yes | Text Type |
| PlayText|   false   | Bool  |     No | Whether to play voice announcement |
| multiLine|   false   | Bool  |     No | Is it a multi-line text? |
| alignment|   left  | String <br>center: Center alignment <br>left: Left alignment <br>right: Right alignment | No | Horizontal alignment |
| valignment|  top  | String <br>middle: center alignment <br>top: top alignment <br>bottom: bottom alignment | No | Vertical alignment |

Request (Body) example:


```
{
    "method": "replace",
    "data": [{
	"name": "节目1",
	"type": "normal",
	"uuid": "A3",
	"area": [{
		"x": 0,
		"y": 0,
		"width": 128,
		"height": 80,
        "border": {
		"type": 0,
		"speed": 5,
		"effect":"rotate"
        },
		"item": [{
			"type": "text",
			"string": "LED",
			"multiLine": false,
			"PlayText": false,
			"font": {
				"name": "宋体",
				"size": 14,
				"underline": false,
				"bold": false,
				"italic": false,
				"color": "#ffff00"
			},
                    
			"effect": {
				"type": 0,
				"speed": 5,
				"hold": 5000
			}
		}]
	}]
}],
    "id": "C16-D00-A000F"
}
```


Return example:

```
{
	"method": "replace",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```


### 3.2.7 Picture Program

Interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | yes  |  No description available |

Request (Body) Description:
| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| type    |  image    | String | Yes | Image Type |
| fit     |  stretch | String fill: Fill: First, the image is proportionally enlarged to cover the entire area, and then the middle part is cut out for display. <br>center: Center: The image is proportionally reduced to the area size. If the proportions are inconsistent, black edges will be displayed. <br>stretch: Stretching may cause the image to be distorted. <br>tile: Tile | No | Image fill properties |
| file |     |  String   | Yes | The file name or valid URL of the file in the device |
| fileMd5  |     |  String   | Yes | MD5 value of the file |
| fileSize|     |  Int   | No | File size, if already exists on the device, no further download will be performed |

Request (Body) example:


```
{
    "method": "replace",
    "data": [
        {
            "name": "节目2",
            "type": "normal",
            "uuid": "A4",
            "area": [
                {
                    "x": 0,
                    "y": 0,
                    "width": 128,
                    "height": 64,
                    "item": [
                        {
                            "type": "image",
                            "file": "https://persuasion.yingkeiot.cn/attachment/violations/11/2024-06-03/80602000-58c6-43b5-adc9-b072ec04c792.jpg",
                            "fileSize": 337460,
                            "fileMd5": "498c7bbab17011a3d257cf0468bcff08",
                            "fit": "stretch",
                            "effect": {
                                "type": 0,
                                "speed": 5,
                                "hold": 5000
                            }
                        }
                    ]
                }
            ]
        }
    ]
}
```


Return example:

```
{
	"method": "replace",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```


### 3.2.8 Video Program

Interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | Yes | No description available |

Request (Body) Description:
| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| type    |  video            | String  | Yes | Video Type |
| aspectRatio |  false        | Bool    | No | Maintain aspect ratio |
| file |     |  String   | Yes | The filename on the device or a valid URL |
| fileMd5  |     |  String   | Yes | File's MD5 value |
| fileSize|     |  Int   | No | File size; if the file already exists on the device, it will not be downloaded again |

Request (Body) example:


```
{
	"data": [
		{
			"name": "节目1",
			"type": "normal",
			"uuid": "A4",
			"area": [
				{
					"height": 32,
					"item": [
						{
							"aspectRatio": false,
							"file": "https://persuasion.yingkeiot.cn/attachment/screen/2024-03-19/822091ba-f9e7-4096-8baa-318d785a60ef.mp4",
							"fileMd5": "46318c4df4968f716061e5fc2ad22401",
							"fileSize": 33417203,
							"type": "video"
						}
					],
					"width": 128,
					"x": 0,
					"y": 32
				}
			]
		}
	],
	"method": "replace"
}
```


Return example:

```
{
	"method": "replace",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```


### 3.2.9 Digital clock program

interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | Yes | No description available |

Request (Body) Description:
| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| type    |  digitalClock     | String  | Yes | Digital Clock |
| timezone |  In the format of "+8:00"     | String    | No | Time Zone |
| timeOffset |"+00:05:00" moves the time forward or "-00:05:00" moves the time backward <br>Default value: 0 | String | No | Time fine-tuning |
| multiLine|       | Bool   | No | Multi-line display |
| title.string|    | String | No | Title Content |
| title.color|     | String | No | Title Color |
| title.display|   | String | No | Title Display|
| date.format |    | Int has the following fixed values: <br>0, YYYY/MM/DD <br>1, MM/DD/YYYY <br>2, DD/MM/YYYY <br>3, Jan DD, YYYY <br>4, DD Jan, YYYY <br>5, YYYY-MM-DD-dd <br>6, MM-DD-dd | No | Date format |
| date.color|     | String | No | Date Color |
| date.display|   | String | No | Date Display|
| week.format |    | Int has the following fixed values: <br>0, Monday <br>1, Monday <br>2, Mon | No | Week format |
| week.color|      | String | No | Week Color |
| week.display|    | String | No | Week Display|
| time.format |    | Int has the following fixed values: <br>0, hh:mm:ss <br>1, hh:ss <br>2, hh hour, mm minute, ss second <br>3, hh hour, mm minute | No | Time format |
| time.color|      | String | No | Time Color |
| time.display|    | String | No | Time Display|
| lunarCalendar.color|      | String | No | lunarCalendar Color |
| lunarCalendar.display|    | String | No | lunarCalendar Display|

Request (Body) example:


```
{
	"method": "replace",
	"data": [
		{
			"name": "节目1",
			"type": "normal",
			"uuid": "A4",
			"area": [
				{
					"x": 0,
					"y": 0,
					"width": 128,
					"height": 64,
					"item": [
						{
							"type": "digitalClock",
							"timezone": "",
							"timeOffset": "",
                                                        "multiLine": "true",
							"font": {
								"name": "宋体",
								"size": 8,
								"underline": false,
								"bold": false,
								"italic": false,
								"color": "#ff0000"
							},
							"title": {
								"string": "0",
								"color": "#ff0000"
							},
							"date": {
								"format": "6",
								"color": "#ff0000"
							},
							"week": {
								"format": "0",
								"color": "#ff0000"
							},
							"time": {
								"format": "0",
								"color": "#ff0000"
							}
                                                        "lunarCalendar": {
                                                                "display": "true",
                                                                "color": "#ff00ff"
                                                        }
						}
					]
				}
			]
		}
	]
}
```


Return example:

```
{
	"method": "replace",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```


### 3.2.10 Analog clock program

Interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2    | String  | Yes | No description available |

Request (Body) Description:
| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| type    |  dialClock          | String  | Yes | Analog Clock |
| timezone | In the format of "+8:00" | String | No | Time zone |
| timeOffset | "+00:05:00" to adjust the time forward or "-00:05:00" to adjust the time backward <br>Default: 0 | String | No | Time fine-tuning |
| title.string | | String | No | Title content |
| date.format | | Int fixed values: <br>0, YYYY/MM/DD <br>1, MM/DD/YYYY <br>2, DD/MM/YYYY <br>3, Jan DD, YYYY <br>4, DD Jan, YYYY <br>5, YYYY-MM-DD-DD <br>6, MM-DD-DD-DD | No | Date format |
| week.format | | Int fixed values: <br>0, Monday <br>1, Monday <br>2, Mon | No | Week format |
| time.format | | Int fixed value: <br>0, hh:mm:ss <br>1, hh:ss <br>2, hh hours, mm minutes, ss seconds <br>3, hh hours, mm minutes | No | Time format |
| style.hourHandColor | #ffffff | String | No | Time format |
| style.minuteHandColor | #ffffff | String | No | Minute hand color |
| style.secondHandColor | #ffffff | String | No | Second hand color |
| style.hourScaleColor | #ffffff | String | No | Clock scale color |
| style.minuteScaleColor | #ffffff | String | No | Minute scale color |

Request (Body) example:


```
{
	"method": "replace",
	"data": [
		{
			"name": "节目1",
			"type": "normal",
			"uuid": "A4",
			"area": [
				{
					"x": 0,
					"y": 0,
					"width": 128,
					"height": 64,
					"item": [
						{
							"type": "dialClock",
							"timezone": "",
							"timeOffset": "",
							"font": {
								"name": "宋体",
								"size": 8,
								"underline": false,
								"bold": false,
								"italic": false,
								"color": "#ff0000"
							},
							"title": {
								"string": "0",
								"color": "#ff0000"
							},
							"date": {
								"format": "6",
								"color": "#ff0000"
							},
							"week": {
								"format": "0",
								"color": "#ff0000"
							},
							"time": {
								"format": "0",
								"color": "#ff0000"
							}
						}
					]
				}
			]
		}
	]
}
```


Return example:

```
{
	"method": "replace",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```


### 3.2.11 Dynamic Area

Interface URL：127.0.0.1:30080/api/program/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description：

| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | Yes | No description available |

Request (Body) example:


```
{
    "data": [
        {
            "name": "节目1",
            "type": "normal",
            "uuid": "A4",
            "area": [
                {
                    "x": 0,
                    "y": 32,
                    "width": 128,
                    "height": 32,
                    "item": [
                        {
                            "type": "dynamic",
                            "string": "停车场信息<br>温度:{{Temperature}} ℃<br>车位:{{ParkingSpace}} 个",
                            "keys": "Temperature,ParkingSpace",
                            "alignment": "center",
                            "font": {
                                "name": "宋体",
                                "size": 14,
                                "underline": false,
                                "bold": false,
                                "italic": false,
                                "color": "#ffff00"
                            },
                            "effect": {
                                "type": 0,
                                "speed": 5,
                                "hold": 5000
                            }
                        }
                    ]
                },
                {
                    "x": 0,
                    "y": 0,
                    "width": 128,
                    "height": 32,
                    "item": [
                        {
                            "type": "text",
                            "string": "剩余车位：",
                            "alignment": "left",
                            "multiLine": false,
                            "font": {
                                "name": "FZLanTingHeiS-R-GB",
                                "size": 14,
                                "underline": false,
                                "bold": false,
                                "italic": false,
                                "color": "#ffff00"
                            },
                            "effect": {
                                "type": 0,
                                "speed": 5,
                                "hold": 5000
                            }
                        }
                    ]
                }
            ]
        }
    ],
    "method": "replace"
}
```


Return example:

```
{
	"method": "replace",
	"message": "ok",
	"data": [
		{
			"id": "C16L-D00-A000F",
			"message": "ok",
			"data": "kSuccess"
		}
	]
}
```

## 3.3 File Common Interface

Interface URL：127.0.0.1:30080/api/file/{{Id}}

Content-Type：application/json

Request method：POST

Request header parameter description: Upload files, mainly used to operate resource file related content

| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | Yes | No description available |

Request **(form-data)** Example:


```
none
```


Return example:

```
{
	"data": [{
		"message": "ok",
		"name": "R-C.png",
		"md5": "9295dc4594e9fd82466c9c008a989e8e",
		"size": "21186",
		"data": "http://127.0.0.1:30080/api/file/R-C.png?_hdsdk_expired=1730865038&date=1714967438&sdkKey=a7fa6795aaa891e2&sign=ed39a32f10d1b349f9ab2ae4c3acb97a&zzzzz=R-C.png"
	}],
	"message": "ok"
}
```

## 3.4 Screenshot interface

Interface URL：127.0.0.1:30080/api/screenshot/{{Id}}

Content-Type：application/json

Request method：GET

Request header parameter description：

| Parameter Name | Example Value | Parameter Type | Required | Parameter Description |
|---|---|---|---|---|
| sdkKey  | a7fa6795aaa891e2  | String  | Yes | No description available |

Request (Body) example:


```
{
	"method": "screenshot",
	"data": {}
}
```


Return example:

```
**When taking a screenshot using the device universal interface, the base64 data of the image is returned**
```

# 4 Interface simulation debugging

Interface Example：https://console-docs.apipost.cn/preview/07ce80dbc607d40d/7b80fbbde771e7ba

## 4.1 Configure the Apipost environment

Download URL：https://www.apipost.cn/

## 4.2 Importing Project Files

Select the json file【HD_HttpApi1.0_Apipost_Collection.json】

![输入图片说明](doc/images/import1.png)

![输入图片说明](doc/images/import2.png)

## 4.3 Configure environment variables

![输入图片说明](doc/images/Apipost1.png)

## 4.4 Configure server ip, port and key

![输入图片说明](doc/images/Apipost2.png)

## 4.5 Edit Pre-Action

![输入图片说明](doc/images/Apipost3.png)


```
pm.request.headers.upsert({
    key: "requestId",
    value: pm.variables.get("requestId")
});

if (pm.request.headers.has("sdkKey")) {

    pm.request.headers.upsert({
        key: "sdkKey",
        value: pm.environment.get("sdkKey")
    });

    var dateData = new Date()
    pm.request.headers.upsert({
        key: "date",
        value: dateData.toUTCString()
    });

    var signText = pm.environment.get("sdkKey") + dateData.toUTCString()
    if (pm.request.body != undefined && pm.request.body.raw != undefined) {
        signText = pm.request.body.raw + signText
    }
    var sign = CryptoJS.HmacMD5(signText, pm.environment.get("sdkSecret")).toString();

    pm.request.headers.upsert({
        key: "sign",
        value: sign
    });
} else if (pm.request.url.query.has("sdkKey")) {

    pm.request.url.query.upsert({
        key: "sdkKey",
        value: pm.environment.get("sdkKey")
    });

    var dateData = new Date()
    pm.request.url.query.upsert({
        key: "date",
        value: dateData.toUTCString()
    });

    var signText = pm.environment.get("sdkKey") + dateData.toUTCString()
    if (pm.request.body != undefined && pm.request.body.raw != undefined) {
        signText = pm.request.body.raw + signText
    }
    var sign = CryptoJS.HmacMD5(signText, pm.environment.get("sdkSecret")).toString();

    pm.request.url.query.upsert({
        key: "sign",
        value: sign
    });
}
// Get the Header parameter object
var headers = pm.request.headers;
// Traverse the entire header
headers.each((item) => {
    console.log(item.key + ":" + item.value);
});
```

