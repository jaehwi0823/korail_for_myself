from korail2 import *
import requests
import time as tt
import datetime
import os


# licence
print("#"*80)
print("""
    KORAIL 반복 예매 간이 프로그램입니다. (API wrapped program)

    :KORAIL API - https://github.com/carpedm20/korail2
    :original license - BSD
    :this program license - MIT
""")
print("#"*80)
print("")


# get idpw
try:
    login_dict = {}
    with open('./credentials/idpw', 'r') as f:
        for l in f.readlines():
            k, v = l.split()
            login_dict[k] = v
    ko_id = login_dict['ID']
    ko_pw = login_dict['PW']
except:
    ko_id = input("KORAIL ID를 입력해주세요.\n>> ")
    ko_pw = input("KORAIL PW를 입력해주세요.\n>> ")
    print("ID: ", ko_id)
    print("PW: ", ko_pw)


# get url
slack_use = False
url = ''
try:
    with open('./credentials/slack', 'r') as f:
        for l in f.readlines():
            if 'URL' in l.split():
                _, url = l.split()

    slack_use = True
    print("Slack 사용 ON!")
except:
    slack_use = False

# define messeging func
def msg_to_slcak(msg, url=url):
    r = requests.post(
            url,
            json = {"text": msg},
            headers = {'Content-type': 'application/json'}
    )
    # print("posting msg result: ", r)

# 시간 계산 함수
def get_moving_time(train):
    info_str = train.__repr__()

    st_idx = info_str.find("(")
    ed_idx = info_str.find(")")
    info_time = info_str[st_idx+1 : ed_idx]

    sttm = info_time.split("~")[0].split(":")
    edtm = info_time.split("~")[1].split(":")

    diff_list = []
    for st, ed in zip(sttm, edtm):
        diff_list.append(int(ed) - int(st))
    
    total_min = diff_list[0]*60 + diff_list[1]
    train_hour = total_min // 60
    train_min = total_min - train_hour*60
    
    return train_hour, train_min



# object creation, log-in test
KR = Korail(ko_id, ko_pw)
if KR.login():
    print("로그인 성공 ! \n")


    # 정보 가져오기 ===================================================================
    dep = input("출발역을 정확히 입력해주세요. <예>용산\n>> ")
    arr = input("도착역을 정확히 입력해주세요. <예>순천\n>> ")
    date = input("출발일을 YYMMDD 형식으로 정확히 입력해주세요. 입력 안하시면 오늘 열차를 검색합니다.<예>20210917\n>> ")
    if date == '':
        date = None
        time = None
    else: 
        time = input("검색할 기차 출발시간을 HHMMSS 형식으로 입력해주세요. 입력시간 이후의 기차만 검색합니다. <예>183000\n>> ")
    if time == '':
        time = None

    want_ktx = input("검색조건을 입력해 주세요. 1:모든기차, 2:KTX만, 3:KTX제외 <예>1\n>> ")
    people_num = input("표 몇 매가 필요하십니까? <예>1\n>> ")
    time_limit = input("몇 시간 안에 이동해야 하나요? 입력 안하시면 모든 기차를 검색합니다. <예>3\n>> ")

    # 정보 체크
    raise_err = False

    # 검색조건 1 ~ 3 only
    if want_ktx not in [str(i) for i in range(1,4)]:
        raise_err = True
    
    # 표 매수 1 ~ 8 only
    if people_num == "":
        people_num = 1
    elif people_num not in [str(i) for i in range(1,9)]:
        print("표는 1매 ~ 8매가 가능합니다")
        raise_err = True
    else:
        people_num = int(people_num)
    
    # 시간제한
    if time_limit == "":
        time_limit = 999
    elif time_limit not in [str(i) for i in range(1,25)]:
        print("이동시간 제한은 1시간 ~ 24시간만 가능합니다")
    else:
        time_limit = int(time_limit)

    if not raise_err:
        # 문제없음 로그
        print("\n", "="*100)
        if date and time:
            print(f"{date}(년월일) {time}(시분초) 이후 열차 중, {dep} -> {arr} 열차표 예매를 시도하겠습니다!\n")
        else:
            print(f"현재 시간 이후 열차 중, {dep} -> {arr} 열차표 반복 예매를 시작합니다!\n")
        print("열차 찾는중..")
        # print("="*20, " 표 예매를 반복적으로 시도합니다! ", "="*20)

        # 반복 시작
        state = True
        idx = 1
        while(state):
            # 10분 단위 로그
            if idx % 600 == 0:
                print(f"\n[{datetime.datetime.now()}] {dep} 출발 -> {arr} 도착 기차표를 예매 시도중입니다...")
                for train in trains:
                    print(train)
            
            # 기차
            trains = KR.search_train(dep, arr, date, time, include_no_seats=True)

            # 기차 반복 찾기
            interesting_train = None
            for train in trains:
                train_info = train.__repr__()
                Thour, Tmin = get_moving_time(train)
                if Thour < time_limit:
                    if want_ktx == '2':
                        if 'KTX' in train_info:
                            if '원' in train_info.split(' ')[-1]:
                                interesting_train = train
                                break
                    elif want_ktx == '3': 
                        if 'KTX' not in train_info:
                            if '원' in train_info.split(' ')[-1]:
                                interesting_train = train
                                break
                    else:
                        if '원' in train_info.split(' ')[-1]:
                            interesting_train = train
                            break
            
            if interesting_train:
                try:
                    rslt= KR.reserve(interesting_train, [AdultPassenger(int(people_num))])
                    if '구입기한' in rslt.__repr__().split(' '):
                        if slack_use:
                            msg_to_slcak(rslt.__repr__())
                        state = False
                        print("\n","="*20, " 열차표 예매에 성공했습니다!! 20분 내로 결제 해주십시오. ", "="*20)
                except Exception as e:
                    if 'WRR800029' in e.__repr__():
                        state = False
                        print("예매 과정에서 에러가 발생하여 프로그램을 종료합니다. 에러 로그를 확인하세요")
                    print(e)
            tt.sleep(1)
            idx += 1
else:
    print("로그인 실패.. ID 또는 PW가 잘못됐습니다 :(")

print(datetime.datetime.now())
print("프로그램을 종료합니다!")
os.system("pause")