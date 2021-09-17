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
# 필요정보 get
def get_train_info(dep = '용산', arr = '순천', 
                   date = None, time = None):
    dep = input("출발역을 정확히 입력해주세요. <예>용산\n>> ")
    arr = input("도착역을 정확히 입력해주세요. <예>순천\n>> ")
    date = input("출발일을 YYMMDD 형식으로 정확히 입력해주세요. 입력 안하시면 오늘 열차를 검색합니다.<예>20210917\n>> ")
    if date == '':
        date = None
        time = None
        print(f"현재 시간 이후 열차 중, {dep} -> {arr} 열차표 예매를 시도하겠습니다!\n")
    else: 
        time = input("검색할 기차 출발시간을 HHMMSS 형식으로 입력해주세요. 입력시간 이후의 기차만 검색합니다. <예>183000\n>> ")

    print("")
    if date and time:
        print(f"{date}(년월일) {time}(시분초) 이후 열차 중, {dep} -> {arr} 열차표 예매를 시도하겠습니다!\n")
    
    return dep, arr, date, time

# object creation, log-in test
KR = Korail(ko_id, ko_pw)
if KR.login():
    print("로그인 성공 ! \n")
    dep, arr, date, time = get_train_info()
    want_ktx = input("검색조건을 입력해 주세요. 1:모든기차, 2:KTX만, 3:KTX제외 <예>1\n>> ")
    people_num = int(input("표 몇 매가 필요하십니까? <예>1\n>> "))
    state = True
    idx = 1
    print("\n")
    print("="*20, " 표 예매를 반복적으로 시도합니다! ", "="*20)
    print("열차 찾는중..")
    while(state):
        if idx % 600 == 0:
            print(f"\n[{datetime.datetime.now()}] {date}, {time}, {dep} -> {arr} 기차표를 예매 시도중입니다...")
            print(trains)
        trains = KR.search_train(dep, arr, date, time, include_no_seats=True)
        interesting_train = None
        is_err = False
        for train in trains:
            if want_ktx == '2':
                if 'KTX' in train.__repr__():
                    if '원' in train.__repr__().split(' ')[-1]:
                        interesting_train = train
                        break
            elif want_ktx == '3': 
                if 'KTX' not in train.__repr__():
                    if '원' in train.__repr__().split(' ')[-1]:
                        interesting_train = train
                        break
            elif want_ktx == '1': 
                if '원' in train.__repr__().split(' ')[-1]:
                    interesting_train = train
                    break
            else:
                is_err = True
        
        if is_err:
            print("검색조건을 잘못 입력하셔서 프로그램을 종료합니다.\n1:모든기차, 2:KTX만, 3:KTX제외")
            break
        
        if interesting_train:
            try:
                rslt, rtxt = KR.reserve(interesting_train, [AdultPassenger(people_num)])
                if '구입기한' in rslt.__repr__().split(' '):
                    if slack_use:
                        msg_to_slcak(rslt.__repr__())
                    state = False
                    print("\n\n")
                    print("="*20, " 열차표 예매에 성공했습니다!! 20분 내로 결제 해주십시오. ", "="*20)
                elif 'WRR800029' in rtxt:
                    state = False
                    print("\n\n")
                    print("="*20, " 에러가 발생하여 프로그램을 종료합니다 :( ", "="*20)
            except Exception as e:
                print(e)
        tt.sleep(1)
        idx += 1
else:
    print("ID 또는 PW가 잘못됐습니다 :(")

print(datetime.datetime.now())
print("프로그램을 종료합니다!")
os.system("pause")