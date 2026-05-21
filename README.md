# HW6 Car Plate Recognition System with Raspberry Pi and Node-RED

## 과제명

HW6 Car Plate Recognition System with Raspberry Pi and Node-RED

## 목표

Node-RED Dashboard에서 버튼을 누르면 Raspberry Pi Camera로 사진을 촬영하고, YOLO 모델로 촬영 이미지 안의 차량을 인식한 뒤 결과를 Dashboard에 표시한다.

## 변경된 과제 방식 설명

기존 OpenALPR 번호판 인식 방식 대신 Raspberry Pi Camera, Node-RED Dashboard, Python YOLO 스크립트를 연결한다. 실시간 스트리밍은 사용하지 않고, 사진 1장을 `/home/aiot/Pictures/photo1.jpg`로 저장한 뒤 YOLO가 해당 이미지를 분석한다.

## 사용한 하드웨어

- Raspberry Pi
- Raspberry Pi Camera
- SSH 접속용 PC
- 같은 네트워크에 연결된 브라우저 접속 기기

## 사용한 소프트웨어

- Raspberry Pi OS
- Node-RED
- Node-RED Dashboard
- libcamera-still
- Python 3
- ultralytics YOLO
- YOLO 모델: `yolov8n.pt`

## 시스템 흐름도

```text
Node-RED Dashboard Button
-> libcamera-still 또는 rpicam-still exec node
-> /home/aiot/Pictures/photo1.jpg 저장
-> Dashboard image template 표시
-> detect_car.py exec node
-> YOLO("yolov8n.pt")
-> car, truck, bus, motorcycle 필터링
-> JSON 출력
-> Node-RED json node
-> function node
-> Dashboard text 표시
```

## 설치 방법

### 1. 기본 패키지 설치

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv curl build-essential
```

### 2. Node-RED 설치

```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
```

설치 후 자동 실행을 켠다.

```bash
sudo systemctl enable nodered.service
sudo systemctl start nodered.service
```

### 3. Node-RED Dashboard 설치

Node-RED Editor에서 설치:

```text
Menu -> Manage palette -> Install -> node-red-dashboard
```

터미널에서 설치:

```bash
cd ~/.node-red
npm install node-red-dashboard
sudo systemctl restart nodered.service
```

### 4. libcamera 테스트

최신 Raspberry Pi OS에서는 `libcamera-still` 대신 `rpicam-still`만 있을 수 있다. 먼저 아래 명령을 확인한다.

```bash
command -v libcamera-still
command -v rpicam-still
```

`libcamera-still`이 있으면:

```bash
mkdir -p /home/aiot/Pictures
bash -lc 'if command -v libcamera-still >/dev/null 2>&1; then libcamera-still -o /home/aiot/Pictures/photo1.jpg --width 640 --height 480 --timeout 1000; else rpicam-still -o /home/aiot/Pictures/photo1.jpg --width 640 --height 480 --timeout 1000; fi'
```

`rpicam-still`만 있으면:

```bash
mkdir -p /home/aiot/Pictures
rpicam-still -o /home/aiot/Pictures/photo1.jpg --width 640 --height 480 --timeout 1000
```

### 5. Python venv 생성 및 ultralytics 설치

```bash
mkdir -p /home/aiot/IoT26-HW06
cd /home/aiot/IoT26-HW06
python3 -m venv /home/aiot/yolo-env
source /home/aiot/yolo-env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Raspberry Pi 5의 Python 3.13에서는 pip가 CUDA 포함 PyTorch 패키지를 받으려고 할 수 있다. 이 경우 아래처럼 Debian의 CPU PyTorch 패키지를 먼저 설치하고, venv가 system package를 볼 수 있게 만든 뒤 `ultralytics`를 `--no-deps`로 설치하는 방식이 안정적이다.

```bash
sudo apt install -y python3-torch python3-torchvision python3-opencv python3-matplotlib python3-scipy python3-pil python3-yaml python3-requests python3-psutil
rm -rf /home/aiot/yolo-env
python3 -m venv --system-site-packages /home/aiot/yolo-env
/home/aiot/yolo-env/bin/python -m pip install --upgrade pip
/home/aiot/yolo-env/bin/pip install --no-deps -r /home/aiot/IoT26-HW06/requirements.txt
```

## 실행 방법

### detect_car.py 단독 실행 테스트

```bash
mkdir -p /home/aiot/Pictures
libcamera-still -o /home/aiot/Pictures/photo1.jpg --width 640 --height 480 --timeout 1000
source /home/aiot/yolo-env/bin/activate
python /home/aiot/IoT26-HW06/detect_car.py
```

정상 예시:

```json
{"success": true, "image": "/home/aiot/Pictures/photo1.jpg", "vehicle_detected": true, "count": 1, "detections": [{"class": "car", "confidence": 0.842}]}
```

### Node-RED 실행 및 접속

```bash
sudo systemctl start nodered.service
```

- Node-RED Editor: `http://172.20.10.2:1880`
- Node-RED Dashboard: `http://172.20.10.2:1880/ui`
- Static image test: `http://172.20.10.2:1880/photo1.jpg`

## Node-RED static directory 설정

Dashboard에서 `/home/aiot/Pictures/photo1.jpg`를 `/photo1.jpg` 주소로 보여주기 위해 `~/.node-red/settings.js`에 static directory를 설정한다.

```bash
nano ~/.node-red/settings.js
```

아래 설정을 추가하거나 기존 `httpStatic` 값을 수정한다.

```javascript
httpStatic: '/home/aiot/Pictures/',
```

수정 후 재시작:

```bash
sudo systemctl restart nodered.service
```

브라우저에서 확인:

```text
http://172.20.10.2:1880/photo1.jpg
```

## Node-RED Flow 설명

`flows_example.json`을 Node-RED Editor에서 import한다.

```text
Menu -> Import -> Clipboard -> flows_example.json 내용 붙여넣기 -> Import
```

Flow 구조:

```text
[ui_button: Take Photo]
-> [exec: libcamera-still 또는 rpicam-still로 /home/aiot/Pictures/photo1.jpg 저장]
-> [function: Refresh image]
-> [ui_template: image display]
-> [exec: /home/aiot/yolo-env/bin/python /home/aiot/IoT26-HW06/detect_car.py]
-> [json]
-> [function: Format YOLO result]
-> [ui_text: result output]
```

`flows_example.json`의 카메라 exec 노드는 아래 명령을 사용한다. `libcamera-still`이 있으면 먼저 사용하고, 없으면 최신 Raspberry Pi OS의 `rpicam-still`로 자동 대체한다.

```bash
bash -lc 'if command -v libcamera-still >/dev/null 2>&1; then libcamera-still -o /home/aiot/Pictures/photo1.jpg --width 640 --height 480 --timeout 1000; else rpicam-still -o /home/aiot/Pictures/photo1.jpg --width 640 --height 480 --timeout 1000; fi'
```

## Dashboard 이미지 표시 ui_template 예시

```html
<div style="text-align:center;">
  <h3>Raspberry Pi Camera Image</h3>
  <img src="/photo1.jpg" style="width:100%; max-width:640px;">
</div>
```

`flows_example.json`에서는 버튼을 누를 때마다 새 이미지를 불러오도록 cache busting 값을 추가한 아래 방식을 사용한다.

```html
<div style="text-align:center;">
  <h3>Raspberry Pi Camera Image</h3>
  <img src="/photo1.jpg?ts={{msg.payload}}" style="width:100%; max-width:640px;">
</div>
```

## function 노드 코드

```javascript
const result = msg.payload;

if (!result || result.success === false) {
    const error = result && result.error ? result.error : "Unknown error";
    msg.payload = "YOLO error: " + error;
    return msg;
}

if (!result.vehicle_detected || result.count === 0) {
    msg.payload = "No vehicle detected";
    return msg;
}

const lines = result.detections.map((item, index) => {
    const confidence = Math.round(item.confidence * 1000) / 1000;
    return `${index + 1}. ${item.class} (${confidence})`;
});

msg.payload = `Vehicle detected: ${result.count}\n` + lines.join("\n");
return msg;
```

## YOLO 차량 인식 코드 설명

`detect_car.py`는 `/home/aiot/Pictures/photo1.jpg`를 입력 이미지로 사용한다. `YOLO("yolov8n.pt")` 모델을 실행하고, 감지 결과 중 `car`, `truck`, `bus`, `motorcycle` 클래스만 남긴다. 결과는 stdout과 `/home/aiot/IoT26-HW06/yolo_result.json`에 JSON으로 저장한다. 오류가 발생해도 stdout에 JSON을 출력하므로 Node-RED의 json 노드에서 처리하기 쉽다.

## 결과 화면 첨부 위치

보고서 또는 GitHub README에 아래 화면을 첨부한다.

- 카메라 촬영 결과 이미지
- Node-RED Flow 화면
- Dashboard 버튼 화면
- Dashboard 이미지 표시 화면
- YOLO 차량 인식 결과 화면

## 제출용 캡처 목록

1. Raspberry Pi Camera가 사진 촬영한 화면
2. Node-RED Flow 화면
3. Node-RED Dashboard 버튼 화면
4. Dashboard에 촬영 이미지가 표시된 화면
5. YOLO 차량 인식 결과가 표시된 화면
6. `detect_car.py` 단독 실행 결과 터미널 화면
7. Raspberry Pi가 실제로 실행 중인 사진 또는 영상

## 문제 발생 시 해결 방법

### `libcamera-still: command not found`

최신 Raspberry Pi OS에서는 명령어 이름이 `rpicam-still`일 수 있다.

```bash
command -v rpicam-still
rpicam-still -o /home/aiot/Pictures/photo1.jpg --width 640 --height 480 --timeout 1000
```

Node-RED exec 노드의 카메라 명령어도 `rpicam-still`로 수정한다.

### Dashboard에서 이미지가 안 보임

`~/.node-red/settings.js`에 아래 설정이 있는지 확인한다.

```javascript
httpStatic: '/home/aiot/Pictures/',
```

수정 후 재시작한다.

```bash
sudo systemctl restart nodered.service
```

### YOLO 설치 실패

`ultralytics`는 PyTorch에 의존한다. Raspberry Pi OS와 Python 버전에 따라 pip가 CUDA 포함 PyTorch를 받으려고 할 수 있다. Raspberry Pi 5와 Python 3.13에서는 아래 방식을 우선 사용한다.

```bash
sudo apt install -y python3-torch python3-torchvision python3-opencv python3-matplotlib python3-scipy python3-pil python3-yaml python3-requests python3-psutil
rm -rf /home/aiot/yolo-env
python3 -m venv --system-site-packages /home/aiot/yolo-env
/home/aiot/yolo-env/bin/python -m pip install --upgrade pip
/home/aiot/yolo-env/bin/pip install --no-deps -r /home/aiot/IoT26-HW06/requirements.txt
```

그래도 실패하면 Python 3.11 또는 3.12 venv를 사용하고, venv 경로는 `/home/aiot/yolo-env`로 유지한다.

### Node-RED exec 노드에서 YOLO 결과가 안 나옴

아래 명령이 SSH에서 먼저 성공해야 한다.

```bash
/home/aiot/yolo-env/bin/python /home/aiot/IoT26-HW06/detect_car.py
```

성공하면 stdout에 JSON이 출력된다.

## GitHub 제출용 파일 구조

```text
IoT26-HW06/
├── README.md
├── detect_car.py
├── flows_example.json
└── requirements.txt
```

실행 중 생성되는 파일:

```text
/home/aiot/Pictures/photo1.jpg
/home/aiot/IoT26-HW06/yolo_result.json
```

## 전체 실행 순서

1. `/home/aiot/IoT26-HW06` 프로젝트 폴더를 준비한다.
2. `/home/aiot/Pictures` 폴더를 만든다.
3. Node-RED와 Node-RED Dashboard를 설치한다.
4. `~/.node-red/settings.js`에 `httpStatic: '/home/aiot/Pictures/'`를 설정한다.
5. `libcamera-still` 또는 `rpicam-still`로 사진 촬영을 테스트한다.
6. `/home/aiot/yolo-env` Python venv를 만들고 `pip install -r requirements.txt`를 실행한다.
7. `python /home/aiot/IoT26-HW06/detect_car.py`로 YOLO 단독 실행을 확인한다.
8. Node-RED Editor `http://172.20.10.2:1880`에 접속한다.
9. `flows_example.json`을 import하고 Deploy한다.
10. Dashboard `http://172.20.10.2:1880/ui`에서 Take Photo 버튼을 누른다.
11. 이미지와 YOLO 차량 인식 결과가 표시되는지 확인한다.
