import json
import requests
import threading

from core.model import CCTVStream, EntityNotFound
from core.repo import CCTVStreamRepository

class CCTVStreamITSRepo(CCTVStreamRepository):
    _lock = threading.Lock()
    _delta_coord = 0.01
    _dist_epsilon = 1e-6

    def __init__(self, json_path: str, api_key: str):
        self._json_path = json_path
        self._api_key = api_key
        self._data: list[CCTVStream] = []
        self._load_data()

    def _load_data(self):
        try:
            with open(self._json_path, "r") as f:
                json_data = f.read()
                self._data = CCTVStream.schema().loads(json_data, many=True)
        except FileNotFoundError:
            pass

    def _save_data(self):
        data = CCTVStream.schema().dumps(self._data, many=True)
        with open(self._json_path, "w") as f:
            json.dump(json.loads(data), f, ensure_ascii=False, indent=2)

    def save(self, name: str, coord: tuple[float, float]) -> CCTVStream:
        """
        CCTV 스트리밍 정보를 추가한다.
        """
        with self._lock:
            cctv = CCTVStream(name=name, coordx=coord[0], coordy=coord[1])
            self._data.append(cctv)
            self._save_data()
            return cctv

    def delete(self, name: str) -> CCTVStream:
        """
        CCTV 스트리밍 정보를 삭제한다.
        """
        with self._lock:
            for stream in self._data:
                if stream.name == name:
                    self._data.remove(stream)
                    self._save_data()
                    return stream
            else:
                raise EntityNotFound(f"CCTV가 존재하지 않습니다.")

    def get_by_name(self, name: str) -> CCTVStream:
        """
        CCTV 스트리밍 정보를 반환한다.
        """
        for stream in self._data:
            if stream.name == name:
                return stream
        raise EntityNotFound(f"CCTV가 존재하지 않습니다.")

    def get_all(self) -> list[CCTVStream]:
        """
        CCTV 스트리밍 정보 목록을 반환한다.
        """
        return [stream for stream in self._data] # shallow copy

    def get_hls(self, cctvstream: CCTVStream) -> str:
        """
        ITS 국가교통정보센터 API를 통해 CCTV 스트리밍 주소(HLS)를 반환한다.
        x, y 좌표를 기준으로 일정(delta) 간격으로 API 요청을 하고, coord와 가장 가까운 CCTV를 찾는다.
        """
        # CCTV 이름에 해당하는 좌표를 찾는다.
        cctv = self.get_by_name(cctvstream.name)
        x, y = cctv.coordx, cctv.coordy

        # API 호출
        res = requests.get("https://openapi.its.go.kr:9443/cctvInfo", params={
            "apiKey": self._api_key,
            "type": "ex",
            "cctvType": 1,
            "minX": x - self._delta_coord,
            "maxX": x + self._delta_coord,
            "minY": y - self._delta_coord,
            "maxY": y + self._delta_coord,
            "getType": "json"
        })

        if res.status_code != 200:
            raise EntityNotFound(f"API 호출에 실패하였습니다.")

        """
        cctvtype    string  CCTV 유형(1: 실시간 스트리밍(HLS) / 2: 동영상 파일 / 3: 정지 영상)
        cctvurl     string  CCTV 영상 주소
        coordx      string  경도 좌표
        coordy      string  위도 좌표
        cctvformat  string  CCTV 형식
        cctvname    string  CCTV 설치 장소명
        """
        data = res.json()['response']['data']
        
        # [2024/06/12] data가 배열이 아닐 경우도 있다.
        if not isinstance(data, list):
            data = [data]

        # 유클리드 거리를 이용하여 가장 가까운 CCTV를 찾는다.
        min_dist = float("inf")
        min_cctv = None
        for cctv in data:
            cctv_x, cctv_y = float(cctv['coordx']), float(cctv['coordy'])
            dist = (x - cctv_x) ** 2 + (y - cctv_y) ** 2
            if dist < min_dist:
                min_dist = dist
                min_cctv = cctv

        if min_dist > self._dist_epsilon:
            raise EntityNotFound(f"HLS 주소를 찾을 수 없습니다.")

        return min_cctv['cctvurl']
