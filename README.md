# 고속도로 CCTV 영상 녹화 및 분석 시스템

## 목적

1. CCTV 스트리밍 영상을 연구 목적으로 녹화하기 위함
2. 녹화된 영상에 대한 분석을 연구원이 진행할 수 있도록 제공

## 유스케이스

1. 연구원은 원하는 CCTV 구간을 선택하여 정해진 기간(녹화 시작/종료 시각)동안 녹화할 수 있다.
2. 연구원은 녹화된 CCTV 영상에서 ROI를 설정하여 필요한 부분만 추출할 수 있다.
3. 연구원은 녹화된 CCTV 영상에서 Perspective Transform Matrix 생성 및 특징점을 선택하여 픽셀 단위의 거리를 실제 거리로 변환할 수 있다.

## 구조

- CCTV 목록 관리 시스템: CCTV 목록을 관리하는 시스템
- 녹화 시스템: CCTV 영상을 녹화하는 시스템
- 분석 시스템: 녹화된 영상을 분석하는 시스템
- UI: CCTV 영상 녹화 및 분석을 위한 유저 인터페이스

### CCTV 목록 관리 시스템

- CCTV 목록은 아래의 스키마를 따른다.
  - cctvid: string, CCTV ID
  - cctvname: string, CCTV 이름
  - cctvhls: string, CCTV HLS URL
  - coordx: float, CCTV 좌표 X
  - coordy: float, CCTV 좌표 Y

- 실제 구현에서는 ITS CCTV HLS이 동적으로 변하므로 이에 대응한다.
- ITS 시스템에서는 CCTV 별 ID 정보가 따로 존재하지 않는다. 또한 해당 OpenAPI 시스템에 종속되면 안되므로, 우리만의 CCTV DB를 구축하여 이를 관리한다.

- CCTV 목록은 아래와 같은 형식의 문자열을 매개변수로 받아 관리한다.

  ```bash
  --add <CCTV_ID> <CCTV_NAME> <CCTV_HLS> <COORD_X> <COORD_Y>
  --remove <CCTV_ID>
  --list
  ```

- 또는 위와 상응하는 HTTP API를 제공할 수 있다.

### 녹화 시스템

- 녹화 시스템은 아래와 같은 형식의 문자열을 매개변수로 받아 녹화를 시작한다.

  ```bash
  --cctvid <CCTV_ID> --start <START_TIME> --end <END_TIME>
  --cctvid <CCTV_ID> --start <START_TIME> --duration <DURATION>
  --cctvid <CCTV_ID> --start <START_TIME> --end <END_TIME> --roi <ROI>
  ```

- 녹화가 되는 중에 그 상태 정보를 다른 애플리케이션에서 받아볼 수 있어야 한다.
- HLS 녹화를 위한 애플리케이션: [ffmpeg](https://ffmpeg.org/)
  - ffmpeg으로 HLS 녹화를 진행할 때, `ffmpeg -i <HLS_URL> -c copy <OUTPUT_PATH>` 명령어를 사용한다.

