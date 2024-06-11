"""
HLS 스트리밍을 녹화하고 그 상태 및 목록을 관리하는 엔드포인트
endpoint example: `/record`
"""

from flask import Flask, request
from cctv_recanalyzer.http.flask_injector import FlaskInjector

from datetime import datetime

from cctv_recanalyzer.core.model import CCTVRecord
from cctv_recanalyzer.core.srv import CCTVRecordJobSrv

class CCTVRecorderView(FlaskInjector):
    def __init__(self, cctv_recorder: CCTVRecordJobSrv):
        self._recorder = cctv_recorder

    def _conv_record(self, record: CCTVRecord):
        return {
            'id': record.id,
            'state': record.state.name,
            'cctvid': record.cctvid,
            'reqat': record.reqat,
            'startat': record.startat,
            'endat': record.endat,
            'srcid': record.srcid,
        }

    def _get_all_record(self):
        """
        녹화 중인 CCTV 목록을 반환한다.
        """
        data = self._recorder.get_all()
        return [self._conv_record(rec) for rec in data]
    
    def _post_submit_record(self):
        """
        CCTV 녹화 작업을 제출한다.
        """
        try:
            cctvid = request.json['cctvid']
            start_time = request.json['start_time']
            end_time = request.json['end_time']

            start_time = datetime.fromisoformat(start_time)
            end_time = datetime.fromisoformat(end_time)
        except KeyError as err:
            return f"{str(err)} 필드가 없습니다.", 400

        record = self._recorder.submit(cctvid, start_time, end_time)
        return self._conv_record(record)
    
    def _cancel_record(self, id: str):
        """
        CCTV 녹화 작업을 취소한다.
        """
        try:
            self._recorder.cancel(id)
        except Exception as err:
            return str(err), 400
        
        return '', 200
    
    def _remove_record(self, id: str):
        """
        CCTV 녹화 작업을 삭제한다.
        """
        try:
            self._recorder.remove(id)
        except Exception as err:
            return str(err), 400
        
        return '', 200

    def inject(self, app: Flask, endpoint: str):
        app.add_url_rule(endpoint, None, self._get_all_record, methods=['GET'])
        app.add_url_rule(endpoint, None, self._post_submit_record, methods=['POST'])
        app.add_url_rule(f'{endpoint}/cancel/<id>', None, self._cancel_record, methods=['GET'])
        app.add_url_rule(f'{endpoint}/<id>', None, self._remove_record, methods=['DELETE'])