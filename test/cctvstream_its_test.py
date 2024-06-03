from cctvrecorder.core.repos import CCTVStreamRepo
from cctvrecorder.repos.cctvstream_its import CCTVStreamITSRepo

if __name__ == "__main__":
    # get api key from `api.key` file
    with open("api.key", "r") as f:
        apikey = f.read().strip()

    repo: CCTVStreamRepo = CCTVStreamITSRepo("./cctvstream_its_test.db", apikey)

    if not isinstance(repo, CCTVStreamRepo):
        raise TypeError("CCTVStreamRepo 구현체가 아닙니다.")

    print("CCTVStream 생성 테스트")
    stream1 = repo.create("[서해안선] 서평택", (126.868976, 36.997973))
    stream2 = repo.create("[서해안선] 서해주탑", (126.838330, 36.950560))
    print()

    print("CCTVStream HLS 주소 조회 테스트")
    print("1.", stream1.hls)
    print("2.", stream2.hls)
    print()

    print("CCTVStream 추가 테스트")
    repo_stream1 = repo.insert(stream1)
    repo_stream2 = repo.insert(stream2)
    print()

    print("CCTVStream 전체 조회 테스트")
    for cctv in repo.find_all(): print("-", cctv)
    print()

    print("CCTVStream ID로 조회 테스트")
    print("1.", repo.find_by_id(stream1.id))
    print("2.", repo.find_by_id(stream2.id))
    print("-.", repo.find_by_id("test"))
    print()

    print("CCTVStream 수정 테스트")
    stream1.name = "[서해안선] 서평택(수정)"
    repo.update(stream1)
    print("1.", repo.find_by_id(stream1.id))
    fake_stream = repo.create("fake", (0, 0))
    try: repo.update(fake_stream)
    except Exception as e: print(e)
    print()

    print("CCTVStream 삭제 전 전체 조회")
    for cctv in repo.find_all(): print("-", cctv)
    print()

    print("CCTVStream 삭제 테스트")
    repo.delete(stream1.id)
    repo.delete(stream2.id)
    try: repo.delete("test")
    except Exception as e: print(e)
    print()

    print("CCTVStream 전체 조회")
    for cctv in repo.find_all(): print("-", cctv)
    print()

