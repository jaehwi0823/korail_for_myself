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
