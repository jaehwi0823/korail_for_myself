import datetime
import os
import random
import time as tt

import requests
from dotenv import load_dotenv
from korail2 import AdultPassenger, NoResultsError, TrainType

import notify
from ktx_booking import PatchedKorail as Korail


load_dotenv()

# --- tunables -------------------------------------------------------------
POLL_MIN_SEC = 2.0           # polling interval lower bound
POLL_MAX_SEC = 3.5           # polling interval upper bound (randomized to
                             # avoid a fixed request cadence anti-bot pattern)
LOG_INTERVAL_SEC = 600       # progress log cadence (10 min)
MAX_RUNTIME_SEC = 6 * 3600   # safety stop: give up after this long
# --------------------------------------------------------------------------


def get_required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required in .env")
    return value


ko_id = get_required_env("KORAIL_ID")
ko_pw = get_required_env("KORAIL_PW")

# Kakao 알림 자격증명 — 누락 시 시작 시점에 바로 실패
for _key in notify.REQUIRED_ENV:
    get_required_env(_key)


# licence
print("#" * 80)
print("""
    KORAIL 반복 예매 간이 프로그램입니다. (API wrapped program)

    :KORAIL API - https://github.com/carpedm20/korail2
    :original license - BSD
    :this program license - MIT
""")
print("#" * 80)
print("")

print("카카오톡 알림 ON!")


# 시간 계산 함수
def get_moving_time(train):
    """Return (hours, minutes) of travel time from train attributes."""
    dep = datetime.datetime.strptime(train.dep_time, "%H%M%S")
    arr = datetime.datetime.strptime(train.arr_time, "%H%M%S")
    delta = arr - dep
    if delta.days < 0:  # arrival past midnight
        delta += datetime.timedelta(days=1)
    total_min = int(delta.total_seconds() // 60)
    return total_min // 60, total_min % 60


def poll_sleep():
    """Randomized wait between search attempts."""
    tt.sleep(random.uniform(POLL_MIN_SEC, POLL_MAX_SEC))


# object creation, log-in test
KR = Korail(ko_id, ko_pw, auto_login=False)
if KR.login():
    print("로그인 성공 ! \n")

    # 정보 가져오기 ===================================================================
    dep = input("출발역을 정확히 입력해주세요. <예>용산\n>> ")
    arr = input("도착역을 정확히 입력해주세요. <예>순천\n>> ")
    date = input("출발일을 YYMMDD 형식으로 정확히 입력해주세요. 입력 안하시면 오늘 열차를 검색합니다.<예>20210917\n>> ")
    if date == "":
        date = None
        train_time = None
    else:
        train_time = input("검색할 기차 출발시간을 HHMMSS 형식으로 입력해주세요. 입력시간 이후의 기차만 검색합니다. <예>183000\n>> ")
    if train_time == "":
        train_time = None

    last_departure = input("최대로 늦은 기차 출발 시간은 언제까지 가능하세요?(몇시 전에는 기차가 출발해야 하나요?) <예>19\n>> ")
    want_ktx = input("검색조건을 입력해 주세요. 1:모든기차, 2:KTX만, 3:KTX제외 <예>1\n>> ")
    people_num = input("표 몇 매가 필요하십니까? <예>1\n>> ")
    time_limit = input("몇 시간 안에 이동해야 하나요? 입력 안하시면 모든 기차를 검색합니다. <예>3\n>> ")

    # 정보 체크
    raise_err = False

    # 검색조건 1 ~ 3 only
    if want_ktx not in [str(i) for i in range(1, 4)]:
        print("검색조건은 1, 2, 3 중 하나여야 합니다")
        raise_err = True

    # 표 매수 1 ~ 8 only
    if people_num == "":
        people_num = 1
    elif people_num not in [str(i) for i in range(1, 9)]:
        print("표는 1매 ~ 8매가 가능합니다")
        raise_err = True
    else:
        people_num = int(people_num)

    # 출발 시간 제한
    if last_departure == "":
        last_departure = 24
    elif last_departure not in [str(i) for i in range(1, 25)]:
        print("이동시간 제한은 1시 ~ 24시만 가능합니다")
        raise_err = True
    else:
        last_departure = int(last_departure)

    # 시간제한
    if time_limit == "":
        time_limit = 999
    elif time_limit not in [str(i) for i in range(1, 25)]:
        print("이동시간 제한은 1시간 ~ 24시간만 가능합니다")
        raise_err = True
    else:
        time_limit = int(time_limit)

    if not raise_err:
        # 문제없음 로그
        print("\n", "=" * 100)
        if date and train_time:
            print(f"{date}(년월일) {train_time}(시분초) 이후 열차 중, {dep} -> {arr} 열차표 예매를 시도하겠습니다!\n")
        else:
            print(f"현재 시간 이후 열차 중, {dep} -> {arr} 열차표 반복 예매를 시작합니다!\n")
        print("열차 찾는중..")

        # KTX만 검색하는 경우 서버 측에서 미리 필터링한다
        search_type = TrainType.KTX if want_ktx == "2" else TrainType.ALL

        # 반복 시작
        state = True
        trains = []
        start_time = tt.monotonic()
        last_log_time = start_time
        while state:
            now = tt.monotonic()

            # 안전 종료: 최대 실행 시간 초과
            if now - start_time > MAX_RUNTIME_SEC:
                print(f"\n최대 실행 시간({MAX_RUNTIME_SEC // 3600}시간)을 초과하여 종료합니다.")
                break

            # 진행 로그 (시간 기준)
            if now - last_log_time >= LOG_INTERVAL_SEC:
                last_log_time = now
                print(f"\n[{datetime.datetime.now()}] {dep} 출발 -> {arr} 도착 기차표를 예매 시도중입니다...")
                for train in trains:
                    print(train)

            # 기차 검색 (일시 오류에도 매크로가 죽지 않도록 보호)
            try:
                trains = KR.search_train(
                    dep, arr, date, train_time,
                    train_type=search_type,
                    include_no_seats=True,
                )
            except NoResultsError:
                poll_sleep()
                continue
            except requests.RequestException as e:
                print(f"[warn] 열차 조회 실패, 재시도합니다: {e}")
                poll_sleep()
                continue

            # 조건에 맞는 기차 찾기
            interesting_train = None
            for train in trains:
                if not train.has_seat():
                    continue

                st_hour = int(train.dep_time[:2])
                train_hour, _ = get_moving_time(train)

                # 소요시간 / 최대 늦은 출발시간 제한
                if train_hour >= time_limit or st_hour >= last_departure:
                    continue

                is_ktx = "KTX" in train.train_type_name
                if want_ktx == "2" and not is_ktx:
                    continue
                if want_ktx == "3" and is_ktx:
                    continue

                interesting_train = train
                break

            if interesting_train:
                try:
                    rslt = KR.reserve(interesting_train, [AdultPassenger(int(people_num))])
                    if rslt:
                        notify.send(f"KTX 예매 성공!\n{rslt}\n20분 내로 결제해주세요.")
                        print("\n", "=" * 20, " 열차표 예매에 성공했습니다!! 20분 내로 결제 해주십시오. ", "=" * 20)
                        print(rslt)

                        # 추가 예매 요건
                        repeat_yn = input("동일한 조건으로 예매를 추가로 진행하시겠습니까?(Y/N) <예>N\n>> ")
                        if repeat_yn in ("Y", "y"):
                            state = True
                            start_time = tt.monotonic()
                            last_log_time = start_time
                        else:
                            state = False

                except Exception as e:
                    if "WRR800029" in repr(e):
                        state = False
                        print("예매 과정에서 에러가 발생하여 프로그램을 종료합니다. 에러 로그를 확인하세요")
                        notify.send(f"KTX 예매 매크로 오류로 종료되었습니다.\n{e}")
                    print(e)

            if state:
                poll_sleep()
else:
    print("로그인 실패.. ID 또는 PW가 잘못됐습니다 :(")

print(datetime.datetime.now())
print("프로그램을 종료합니다!")
