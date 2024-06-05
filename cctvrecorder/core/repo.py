from cctvrecorder.core.model import CCTVStream, CCTVRecord

from abc import ABC, abstractmethod
from typing import List

# CCTV 스트리밍 정보를 관리하는 레포지토리
class CCTVStreamRepo(ABC):

    @abstractmethod
    def find_all(self) -> List[CCTVStream]:
        pass

    @abstractmethod
    def find_by_id(self, id: str) -> CCTVStream:
        """
        id에 맞는 CCTV 스트리밍 정보를 찾아 반환한다.
        """
        pass

    """
    <데이터를 추가하는 연산을 정의할 때 고려할 사항, 이성호, 20240528>
    레포지토리에서 새로운 데이터를 추가하는 연산을 정의할 때 아래의 방법을 고려해볼 수 있다.
        1. 사용자가 모델의 인스턴스를 만들어서 통째로 레포지토리에 넘기는 경우
        2. 데이터를 추가하는 연산에 오직 필요한 매개변수만을 정의하여 이를 넘기는 경우
    두 방법 중 어느 것이 더 나을까?
    
    1번 방법은 사용자가 모델의 인스턴스를 만들어야 하므로, 모델의 구조를 알아야 한다.
    이는 모델의 구조가 변경되면 사용자도 이를 변경해야 한다는 것을 의미한다(그러나 사용자는 이를 알 수밖에 없다).
    그리고 ID를 사용자가 직접 부여해야 한다는 것도 문제가 될 수 있다.
    
    2번 방법은 사용자가 모델의 구조를 알 필요가 없다. 오직 추가 연산에 집중하면 된다.
    하지만 1번과 마찬가지로 레포지토리의 연산이 변경되면 사용자도 변경해야 한다.
    그리고 꼭 데이터 추가에 필요한 매개변수를 정의하는 일도 어렵다. 반대로 꼭 필요한 매개변수만 전달할 수 있다.
    모델의 특정 필드가 정적으로 유지되는 경우에는 문제가 없겠지만, 동적으로 변할 수 있는 경우에는 사용자가 정의하기 어려울 것이다.
    예를 들어, 해당 모델에 대한 url이 동적으로 변할 경우가 있을 것이다. 이럴 때에는 해당 url을 받지 않고,
    레포지토리 레이어가 동적으로 생성하여 처리해야 할 것이다.

    결국, 모델의 필드가 동적으로 결정되는 경우에 위와 같은 고민이 발생한다.
    모델의 필드를 프로그래머가 모두 지정해줄 수 있으면 1번 방법, 그렇지 않으면 2번 방법을 사용하는 것이 좋아 보인다.

    준호와 이야기해 본 결과 아래의 방법도 고려해볼 수 있다.
        3. 팩토리 메서드를 이용하여 모델의 인스턴스를 생성하여 넘기는 경우
    
    구현체에 따라 필드가 동적일 수도 정적일 수도 있다. 그리고 사용자가 직접 지정해줄 수 있고 그렇지 않을 수도 있다.
    그러므로 1번 방법으로 인터페이스(추상 클래스)를 구현하되,
    구현체에서는 3번 방법을 통해 인스턴스를 생성하는 factory 클래스를 구현하는 방법이 있다.
    """

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
    def find_all(self) -> List[CCTVRecord]:
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
