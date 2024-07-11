from cctv_recanalyzer.core.model import CCTVStream, CCTVRecord

from abc import ABC, abstractmethod

# CCTV 스트리밍 정보를 관리하는 레포지토리
class CCTVStreamRepo(ABC):

    @abstractmethod
    def find_all(self) -> list[CCTVStream]:
        pass

    @abstractmethod
    def find_by_id(self, id: str) -> CCTVStream:
        """
        id에 맞는 CCTV 스트리밍 정보를 찾아 반환한다.
        """
        pass

    @abstractmethod
    def get_hls_by_id(self, id: str) -> str:
        """
        id에 맞는 CCTV 스트리밍 정보의 HLS 주소를 반환한다.
        """
        pass

    @abstractmethod
    def insert(self, cctv: CCTVStream) -> CCTVStream:
        """
        CCTV 스트리밍 정보를 추가한다.
        """
        pass

    @abstractmethod
    def update(self, cctv: CCTVStream) -> CCTVStream:
        """
        id 정보를 이용해 CCTV 스트리밍 정보를 수정한다.
        """
        pass

    @abstractmethod
    def delete(self, id: str):
        """
        id 정보를 이용해 CCTV 스트리밍 정보를 삭제한다.
        """
        pass


# 녹화된 또는 녹화 중인 CCTV 영상 정보를 관리하는 레포지토리
class CCTVRecordRepo(ABC):
    
    @abstractmethod
    def find_all(self) -> list[CCTVRecord]:
        pass

    @abstractmethod
    def find_by_id(self, id: str) -> CCTVRecord:
        """
        id에 맞는 CCTV 녹화 정보를 찾아 반환한다.
        """
        pass

    @abstractmethod
    def insert(self, record: CCTVRecord) -> CCTVRecord:
        """
        CCTV 녹화 정보를 추가한다.
        """
        pass

    @abstractmethod
    def update(self, record: CCTVRecord) -> CCTVRecord:
        """
        id 정보를 이용해 CCTV 녹화 정보를 수정한다.
        """
        pass

    @abstractmethod
    def delete(self, id: str):
        """
        id 정보를 이용해 CCTV 녹화 정보를 삭제한다.
        """
        pass
