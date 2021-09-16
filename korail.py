from korail2 import *
import requests
import time as tt
import datetime


# get idpw
login_dict = {}
with open('./credentials/idpw', 'r') as f:
    for l in f.readlines():
        k, v = l.split()
        login_dict[k] = v

# get url
url = ''
with open('./credentials/slack', 'r') as f:
    for l in f.readlines():
        if 'URL' in l.split():
            _, url = l.split()

# define messeging func
def msg_to_slcak(msg, url=url):
    r = requests.post(
            url,
            json = {"text": msg},
            headers = {'Content-type': 'application/json'}
    )
    print("posting msg result: ", r)
# msg_to_slcak("slack api test")

KR = Korail(login_dict['ID'], login_dict['PW'])
dep = '용산'
arr = '순천'
date = '20210922'
time = '130000'
# time = '000000'
print(f"[{datetime.datetime.now()}] {date} {time} 이후 열차 중, {dep} -> {arr} 열차표를 예매 중입니다...")

state = True
idx = 1
while(state):
    if idx % 600 == 0:
        print(f"[{datetime.datetime.now()}] {date}, {time}, {dep} -> {arr} 열차표를 예매 중입니다...")
        print(trains)
    trains = KR.search_train(dep, arr, date, time, include_no_seats=True)
    interesting_train = None
    for train in trains:
        if 'KTX' in train.__repr__():
            if '원' in train.__repr__().split(' ')[-1]:
                interesting_train = train
                break
    
    if interesting_train:
        try:
            rslt = KR.reserve(interesting_train, [AdultPassenger()])
            if '구입기한' in rslt.__repr__().split(' '):
                msg_to_slcak(rslt.__repr__())
                state = False
        except Exception as e:
            print(e)
    tt.sleep(1)
    idx += 1

print(datetime.datetime.now())
print("프로그램을 종료합니다!")