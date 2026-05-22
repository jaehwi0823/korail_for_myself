# Seat Class & Passenger Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the reservation macro book a chosen seat class (general/special, only/first) and a mixed passenger party (adult/child/toddler/senior) instead of only general-first adult-only tickets.

**Architecture:** Extract pure, testable helpers into a new `booking.py` module — seat-option mapping, seat-availability filtering, and passenger-count parsing/building. `korail.py` stays a flat interactive script but delegates all of this logic to `booking.py`, so the new logic is unit-tested even though the script itself is not. New `tests/` directory with pytest.

**Tech Stack:** Python 3.9 (venv at `./korail/`), korail2 0.4.0, pytest (new dev dependency).

---

## File Structure

- **Create `booking.py`** — pure helpers, no network/IO: `SEAT_CHOICES`, `reserve_option()`, `train_has_desired_seat()`, `build_passengers()`, `parse_passenger_counts()`.
- **Create `tests/test_booking.py`** — pytest unit tests for every `booking.py` function.
- **Create `requirements-dev.txt`** — pytest.
- **Modify `korail.py`** — replace the single "표 매수" prompt with seat-class + 4 passenger prompts; validate via `booking`; filter and reserve via `booking`.
- **Modify `.gitignore`** — ignore `.pytest_cache/`.

Run all commands from the project root `/Users/jaehwi/Projects/korail`. The venv interpreter is `./korail/bin/python`.

---

### Task 1: Add pytest dev dependency

**Files:**
- Create: `requirements-dev.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Create `requirements-dev.txt`**

```
pytest
```

- [ ] **Step 2: Install pytest into the venv**

Run: `./korail/bin/pip install -r requirements-dev.txt`
Expected: ends with `Successfully installed pytest-... pluggy-... iniconfig-...` (or "Requirement already satisfied").

- [ ] **Step 3: Verify pytest runs**

Run: `./korail/bin/python -m pytest --version`
Expected: prints `pytest 8.x.x` (some 8.x version).

- [ ] **Step 4: Add `.pytest_cache/` to `.gitignore`**

In `.gitignore`, change the python section from:

```
# python
__pycache__/
*.py[cod]
```

to:

```
# python
__pycache__/
*.py[cod]
.pytest_cache/
```

- [ ] **Step 5: Commit**

```bash
git add requirements-dev.txt .gitignore
git commit -m "Add pytest as a dev dependency"
```

---

### Task 2: `booking.py` — seat-class helpers

Implements `SEAT_CHOICES`, `reserve_option()`, and `train_has_desired_seat()`.

**Files:**
- Create: `booking.py`
- Test: `tests/test_booking.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_booking.py`:

```python
import pytest

import booking
from korail2 import AdultPassenger, ReserveOption, ToddlerPassenger


class FakeTrain:
    """Minimal stand-in for a korail2 Train for seat-availability tests."""

    def __init__(self, general, special):
        self._general = general
        self._special = special

    def has_general_seat(self):
        return self._general

    def has_special_seat(self):
        return self._special

    def has_seat(self):
        return self._general or self._special


# --- reserve_option -------------------------------------------------------

def test_reserve_option_maps_each_choice():
    assert booking.reserve_option("1") == ReserveOption.GENERAL_ONLY
    assert booking.reserve_option("2") == ReserveOption.GENERAL_FIRST
    assert booking.reserve_option("3") == ReserveOption.SPECIAL_ONLY
    assert booking.reserve_option("4") == ReserveOption.SPECIAL_FIRST


# --- train_has_desired_seat -----------------------------------------------

def test_general_only_needs_general_seat():
    assert booking.train_has_desired_seat(FakeTrain(general=True, special=False), "1") is True
    assert booking.train_has_desired_seat(FakeTrain(general=False, special=True), "1") is False


def test_special_only_needs_special_seat():
    assert booking.train_has_desired_seat(FakeTrain(general=True, special=False), "3") is False
    assert booking.train_has_desired_seat(FakeTrain(general=False, special=True), "3") is True


def test_first_options_accept_any_seat():
    only_general = FakeTrain(general=True, special=False)
    only_special = FakeTrain(general=False, special=True)
    assert booking.train_has_desired_seat(only_general, "2") is True
    assert booking.train_has_desired_seat(only_special, "2") is True
    assert booking.train_has_desired_seat(only_general, "4") is True
    assert booking.train_has_desired_seat(only_special, "4") is True


def test_sold_out_train_rejected_for_all_choices():
    sold_out = FakeTrain(general=False, special=False)
    for choice in ("1", "2", "3", "4"):
        assert booking.train_has_desired_seat(sold_out, choice) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./korail/bin/python -m pytest tests/test_booking.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'booking'`.

- [ ] **Step 3: Create `booking.py` with the seat-class helpers**

```python
"""Passenger composition and seat-class helpers for the reservation loop.

Pure functions — no network, no I/O — so they can be unit tested
independently of the interactive korail.py script.
"""
from korail2 import (
    AdultPassenger,
    ChildPassenger,
    ReserveOption,
    SeniorPassenger,
    ToddlerPassenger,
)

# seat choice key -> (Korean label, korail2 ReserveOption)
SEAT_CHOICES = {
    "1": ("일반실만", ReserveOption.GENERAL_ONLY),
    "2": ("일반실 우선", ReserveOption.GENERAL_FIRST),
    "3": ("특실만", ReserveOption.SPECIAL_ONLY),
    "4": ("특실 우선", ReserveOption.SPECIAL_FIRST),
}


def reserve_option(seat_choice):
    """Return the korail2 ReserveOption for a seat choice key ('1'-'4')."""
    return SEAT_CHOICES[seat_choice][1]


def train_has_desired_seat(train, seat_choice):
    """Whether a train has a seat matching the seat choice.

    '1' general-only -> needs a general seat
    '3' special-only -> needs a special seat
    '2'/'4' *-first  -> any seat is acceptable
    """
    if seat_choice == "1":
        return train.has_general_seat()
    if seat_choice == "3":
        return train.has_special_seat()
    return train.has_seat()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./korail/bin/python -m pytest tests/test_booking.py -v`
Expected: PASS — 5 tests pass (`test_reserve_option_maps_each_choice`, `test_general_only_needs_general_seat`, `test_special_only_needs_special_seat`, `test_first_options_accept_any_seat`, `test_sold_out_train_rejected_for_all_choices`).

- [ ] **Step 5: Commit**

```bash
git add booking.py tests/test_booking.py
git commit -m "Add seat-class helpers to booking module"
```

---

### Task 3: `booking.py` — passenger helpers

Implements `build_passengers()` and `parse_passenger_counts()`.

**Files:**
- Modify: `booking.py`
- Test: `tests/test_booking.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_booking.py`:

```python
# --- build_passengers -----------------------------------------------------

def test_build_passengers_single_type():
    result = booking.build_passengers(adults=2)
    assert len(result) == 1
    assert isinstance(result[0], AdultPassenger)
    assert result[0].count == 2


def test_build_passengers_multiple_types():
    result = booking.build_passengers(adults=1, toddlers=1)
    assert len(result) == 2
    assert {type(p) for p in result} == {AdultPassenger, ToddlerPassenger}


def test_build_passengers_skips_zero_counts():
    result = booking.build_passengers(adults=1, children=0, toddlers=0, seniors=0)
    assert len(result) == 1
    assert isinstance(result[0], AdultPassenger)


def test_build_passengers_rejects_empty():
    with pytest.raises(ValueError):
        booking.build_passengers()


# --- parse_passenger_counts -----------------------------------------------

def test_parse_passenger_counts_basic():
    counts = booking.parse_passenger_counts(adults="1", toddlers="1")
    assert counts == {"adults": 1, "children": 0, "toddlers": 1, "seniors": 0}


def test_parse_passenger_counts_empty_means_zero():
    counts = booking.parse_passenger_counts(adults="2")
    assert counts == {"adults": 2, "children": 0, "toddlers": 0, "seniors": 0}


def test_parse_passenger_counts_rejects_non_numeric():
    with pytest.raises(ValueError):
        booking.parse_passenger_counts(adults="two")


def test_parse_passenger_counts_rejects_zero_total():
    with pytest.raises(ValueError):
        booking.parse_passenger_counts()


def test_parse_passenger_counts_rejects_over_max():
    with pytest.raises(ValueError):
        booking.parse_passenger_counts(adults="10")
```

- [ ] **Step 2: Run new tests to verify they fail**

Run: `./korail/bin/python -m pytest tests/test_booking.py -v -k "build_passengers or parse_passenger_counts"`
Expected: FAIL — `AttributeError: module 'booking' has no attribute 'build_passengers'`.

- [ ] **Step 3: Append the passenger helpers to `booking.py`**

Add at the end of `booking.py`:

```python
# passenger-count dict key -> (Korean label, korail2 Passenger class)
_PASSENGER_TYPES = {
    "adults": ("어른", AdultPassenger),
    "children": ("어린이", ChildPassenger),
    "toddlers": ("유아", ToddlerPassenger),
    "seniors": ("경로", SeniorPassenger),
}


def build_passengers(adults=0, children=0, toddlers=0, seniors=0):
    """Build a korail2 passenger list from per-type counts.

    Types with a zero count are omitted. Raises ValueError if the total
    passenger count is zero.
    """
    counts = {"adults": adults, "children": children,
              "toddlers": toddlers, "seniors": seniors}
    if sum(counts.values()) < 1:
        raise ValueError("승객은 최소 1명이어야 합니다")
    return [
        _PASSENGER_TYPES[key][1](count)
        for key, count in counts.items()
        if count > 0
    ]


def parse_passenger_counts(adults="", children="", toddlers="", seniors="",
                           max_total=9):
    """Parse raw string inputs into a {type: int} dict for build_passengers().

    An empty string counts as 0. Raises ValueError with a Korean message
    if any value is not a non-negative integer, or the total is not in
    1..max_total.
    """
    raw = {"adults": adults, "children": children,
           "toddlers": toddlers, "seniors": seniors}
    counts = {}
    for key, value in raw.items():
        value = value.strip()
        if value == "":
            counts[key] = 0
        elif value.isdigit():
            counts[key] = int(value)
        else:
            label = _PASSENGER_TYPES[key][0]
            raise ValueError(f"{label} 인원은 0 이상의 숫자여야 합니다")
    total = sum(counts.values())
    if not (1 <= total <= max_total):
        raise ValueError(f"승객은 총 1명 ~ {max_total}명이어야 합니다")
    return counts
```

- [ ] **Step 4: Run the full test file to verify all pass**

Run: `./korail/bin/python -m pytest tests/test_booking.py -v`
Expected: PASS — 14 tests pass (5 from Task 2 + 9 new).

- [ ] **Step 5: Commit**

```bash
git add booking.py tests/test_booking.py
git commit -m "Add passenger composition helpers to booking module"
```

---

### Task 4: Wire seat class and passengers into `korail.py`

`korail.py` runs its whole flow at import time and reads `input()`, so it is verified by compiling it and by feeding scripted stdin — not by pytest.

**Files:**
- Modify: `korail.py` (6 edits below, in order)

- [ ] **Step 1: Edit imports**

Change (currently around lines 8-11):

```python
from korail2 import AdultPassenger, NoResultsError, TrainType

import notify
from ktx_booking import PatchedKorail as Korail
```

to:

```python
from korail2 import NoResultsError, TrainType

import booking
import notify
from ktx_booking import PatchedKorail as Korail
```

- [ ] **Step 2: Edit the input prompts**

Change (currently around lines 89-92):

```python
    last_departure = input("최대로 늦은 기차 출발 시간은 언제까지 가능하세요?(몇시 전에는 기차가 출발해야 하나요?) <예>19\n>> ")
    want_ktx = input("검색조건을 입력해 주세요. 1:모든기차, 2:KTX만, 3:KTX제외 <예>1\n>> ")
    people_num = input("표 몇 매가 필요하십니까? <예>1\n>> ")
    time_limit = input("몇 시간 안에 이동해야 하나요? 입력 안하시면 모든 기차를 검색합니다. <예>3\n>> ")
```

to:

```python
    last_departure = input("최대로 늦은 기차 출발 시간은 언제까지 가능하세요?(몇시 전에는 기차가 출발해야 하나요?) <예>19\n>> ")
    want_ktx = input("검색조건을 입력해 주세요. 1:모든기차, 2:KTX만, 3:KTX제외 <예>1\n>> ")
    seat_choice = input("좌석 등급을 선택해주세요. 1:일반실만, 2:일반실 우선, 3:특실만, 4:특실 우선 <예>2\n>> ")
    adults = input("어른은 몇 명인가요? 입력 안하시면 0명입니다. <예>1\n>> ")
    children = input("어린이(만 6~12세)는 몇 명인가요? 입력 안하시면 0명입니다. <예>0\n>> ")
    toddlers = input("유아(만 6세 미만)는 몇 명인가요? 입력 안하시면 0명입니다. <예>0\n>> ")
    seniors = input("경로(만 65세 이상)는 몇 명인가요? 입력 안하시면 0명입니다. <예>0\n>> ")
    time_limit = input("몇 시간 안에 이동해야 하나요? 입력 안하시면 모든 기차를 검색합니다. <예>3\n>> ")
```

- [ ] **Step 3: Edit the validation block**

Change (currently around lines 102-109):

```python
    # 표 매수 1 ~ 8 only
    if people_num == "":
        people_num = 1
    elif people_num not in [str(i) for i in range(1, 9)]:
        print("표는 1매 ~ 8매가 가능합니다")
        raise_err = True
    else:
        people_num = int(people_num)
```

to:

```python
    # 좌석 등급 1 ~ 4 only
    if seat_choice not in booking.SEAT_CHOICES:
        print("좌석 등급은 1, 2, 3, 4 중 하나여야 합니다")
        raise_err = True

    # 승객 인원 (빈 값은 0명, 총 1 ~ 9명)
    passenger_counts = None
    try:
        passenger_counts = booking.parse_passenger_counts(
            adults, children, toddlers, seniors
        )
    except ValueError as e:
        print(e)
        raise_err = True
```

- [ ] **Step 4: Build the passenger list once, after validation passes**

Change (currently around lines 129-136):

```python
    if not raise_err:
        # 문제없음 로그
        print("\n", "=" * 100)
        if date and train_time:
            print(f"{date}(년월일) {train_time}(시분초) 이후 열차 중, {dep} -> {arr} 열차표 예매를 시도하겠습니다!\n")
        else:
            print(f"현재 시간 이후 열차 중, {dep} -> {arr} 열차표 반복 예매를 시작합니다!\n")
        print("열차 찾는중..")
```

to:

```python
    if not raise_err:
        passengers = booking.build_passengers(**passenger_counts)
        seat_label = booking.SEAT_CHOICES[seat_choice][0]

        # 문제없음 로그
        print("\n", "=" * 100)
        if date and train_time:
            print(f"{date}(년월일) {train_time}(시분초) 이후 열차 중, {dep} -> {arr} 열차표 예매를 시도하겠습니다!\n")
        else:
            print(f"현재 시간 이후 열차 중, {dep} -> {arr} 열차표 반복 예매를 시작합니다!\n")
        print(f"좌석 등급: {seat_label} / 승객 {sum(passenger_counts.values())}명")
        print("열차 찾는중..")
```

- [ ] **Step 5: Edit the seat-availability filter**

Change (currently around lines 178-180):

```python
            for train in trains:
                if not train.has_seat():
                    continue
```

to:

```python
            for train in trains:
                if not booking.train_has_desired_seat(train, seat_choice):
                    continue
```

- [ ] **Step 6: Edit the reserve call**

Change (currently around line 200):

```python
                    rslt = KR.reserve(interesting_train, [AdultPassenger(int(people_num))])
```

to:

```python
                    rslt = KR.reserve(
                        interesting_train,
                        passengers,
                        option=booking.reserve_option(seat_choice),
                    )
```

- [ ] **Step 7: Verify it compiles and unit tests still pass**

Run: `./korail/bin/python -m py_compile korail.py booking.py && ./korail/bin/python -m pytest tests/ -v`
Expected: no compile output (success), then 14 pytest tests PASS.

- [ ] **Step 8: Verify the validation/abort path (invalid seat choice)**

Run:
```bash
printf '용산\n순천\n\n19\n2\n9\n1\n0\n0\n0\n3\n' | ./korail/bin/python korail.py 2>&1 | tail -5
```
(11 stdin lines: dep, arr, date=empty, last_departure, want_ktx, seat_choice=9 invalid, adults, children, toddlers, seniors, time_limit.)
Expected: prints `좌석 등급은 1, 2, 3, 4 중 하나여야 합니다`, then the closing datetime line and `프로그램을 종료합니다!`. No traceback.

- [ ] **Step 9: Verify the live loop with seat+passenger config (no reservation)**

Run in background — `time_limit=1` makes 용산→순천 (~3h) never match, so the loop searches but never reserves:
```bash
printf '용산\n순천\n\n24\n2\n3\n1\n0\n1\n0\n1\n' | ./korail/bin/python -u korail.py > /tmp/korail_seat_test.log 2>&1 &
```
Wait ~20 seconds, then run:
```bash
pgrep -f korail.py >/dev/null && echo ALIVE || echo EXITED
grep -E 'Traceback|Error' /tmp/korail_seat_test.log || echo "no errors"
grep -F '좌석 등급: 특실만 / 승객 2명' /tmp/korail_seat_test.log
```
Expected: `ALIVE`, `no errors`, and the `좌석 등급: 특실만 / 승객 2명` line present (adults=1 + toddlers=1 = 2). Then stop it: `pkill -f korail.py` and `rm -f /tmp/korail_seat_test.log`.

- [ ] **Step 10: Commit**

```bash
git add korail.py
git commit -m "Add seat-class and passenger-type selection to reservation flow"
```

---

## Verification of the original request

After this plan, the request "2026-05-25 순천→용산, 13:00 이후 출발, KTX, 특실, 어른 1 + 유아 1" is entered as:

```
출발역: 순천
도착역: 용산
출발일: 20260525
검색 출발시간: 130000
최대 늦은 출발시간: 15        (13~14시대 KTX 통과; 분 단위 컷오프는 범위 외)
검색조건: 2                   (KTX만)
좌석 등급: 3                  (특실만)
어른: 1
어린이: 0
유아: 1
경로: 0
시간제한: (공란)
```

The minute-level cutoff (exact 14:30) is intentionally out of scope per the user's instruction.
