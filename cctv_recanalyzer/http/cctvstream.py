"""
HLS 스트리밍을 제공하는 CCTV 목록을 관리하는 엔드포인트
endpoint example: `/cctvstream`
"""

from flask import Flask

from cctv_recanalyzer.core.model import CCTVStream
from cctv_recanalyzer.core.repo import CCTVStreamRepo
from cctv_recanalyzer.http.flask_injector import FlaskInjector

class CCTVStreamView(FlaskInjector):
    def __init__(self, stream_repo: CCTVStreamRepo):
        self._stream_repo = stream_repo

    def _conv_dict(self, data: CCTVStream):
        return {
            "id": data.id,
            "name": data.name,
            "coordx": data.coord[0],
            "coordy": data.coord[1],
        }

    def _get_all_cctv(self):
        """
        CCTV 스트리밍 목록을 반환한다.
        """
        data = self._stream_repo.find_all()
        data = [self._conv_dict(d) for d in data if d.avail]
        return {
            "data": data
        }

    def _get_cctv_by_id(self, id: str):
        """
        id에 해당하는 CCTV 스트리밍 정보를 반환한다.
        """
        try:
            data = self._stream_repo.find_by_id(id)
        except Exception as err:
            return str(err), 404
        
        return self._conv_dict(data)
    
    def inject(self, app: Flask, endpoint: str):
        app.add_url_rule(endpoint, None, self._get_all_cctv, methods=['GET']) # root
        app.add_url_rule(endpoint + '/<id>', None, self._get_cctv_by_id, methods=['GET'])
