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

    Defined for keys in SEAT_CHOICES:
      "1" general-only  -> needs a general seat
      "2" general-first -> any available seat is acceptable
      "3" special-only  -> needs a special seat
      "4" special-first -> any available seat is acceptable
    Raises KeyError for any other value; the caller is expected to
    validate seat_choice against SEAT_CHOICES first.
    """
    if seat_choice not in SEAT_CHOICES:
        raise KeyError(seat_choice)
    if seat_choice == "1":
        return train.has_general_seat()
    if seat_choice == "3":
        return train.has_special_seat()
    # "2" or "4" — general-first / special-first: any available seat is fine
    return train.has_seat()


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
