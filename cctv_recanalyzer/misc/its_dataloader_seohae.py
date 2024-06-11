import uuid
import requests
import cctv_recanalyzer.main as di
from cctv_recanalyzer.core.model import CCTVStream

# 서해대교 주변 좌표
MIN_X = 126.0
MIN_Y = 36.9
MAX_X = 127.0
MAX_Y = 37.0

# CCTV 정보 요청
url = f"https://openapi.its.go.kr:9443/cctvInfo?apiKey={di.ITS_API_KEY}&type=ex&cctvType=1&minX={MIN_X}&maxX={MAX_X}&minY={MIN_Y}&maxY={MAX_Y}&getType=json"
print("Requesting CCTV information...")
print(url)
response = requests.get(url)

"""
API 응답 예시:
{
    "response": {
        "coordtype": 1,
        "data": [
            {
                "roadsectionid": "",
                "coordx": 126.8689758,
                "coordy": 36.99797346,
                "cctvresolution": "",
                "filecreatetime": "",
                "cctvtype": 1,
                "cctvformat": "HLS",
                "cctvname": "[서해안선] 서평택",
                "cctvurl": ...
            },
            ...
"""

# CCTV 정보 파싱
data = response.json()['response']['data']
data = [
    CCTVStream(
        id=str(uuid.uuid4()),
        name=cctv['cctvname'],
        coord=(float(cctv['coordx']), float(cctv['coordy'])),
        avail=True,
    ) for cctv in data
]
print("CCTV information received and parsed.")

# CCTV 정보 저장
for d in data:
    di.stream_repo.insert(d)
print("CCTV information saved.")