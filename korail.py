import os
from time import sleep

import requests
from dotenv import load_dotenv
from korail2 import (
    AdultPassenger,
    NoResultsError,
    ReserveOption,
    TrainType,
)

from ktx_booking import PatchedKorail as Korail


load_dotenv()

KORAIL_ID = os.environ['KORAIL_ID']
KORAIL_PW = os.environ['KORAIL_PW']
SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']


def msg_to_slack(msg, url=SLACK_WEBHOOK_URL):
    r = requests.post(
        url,
        json={"text": msg},
        headers={'Content-type': 'application/json'},
    )
    print("response: ", r)


korail = Korail(KORAIL_ID, KORAIL_PW)

dep = '순천'
arr = '용산'
date = '20260606'
time = '123000'
passengers = [AdultPassenger(1)]


print("Korail Reservation Trying Starts!")
while not korail.reservations():
    try:
        trains = korail.search_train(
            dep,
            arr,
            date,
            time,
            train_type=TrainType.KTX,
            passengers=passengers)

        if trains[0].dep_time > '140000':
            print(trains[0].dep_time)
            sleep(2)
            continue

        seat = korail.reserve(trains[0],
                              passengers,
                              ReserveOption.SPECIAL_FIRST)
        msg_to_slack(f"Korail Reservation Success!: {seat}")
        print([att for att in dir(trains[0]) if not att.startswith('_')])

    except NoResultsError:
        sleep(2)
    except Exception as e:
        msg_to_slack(f"Korail Reservation Failed!: {e}")
        break

print(korail.reservations())
