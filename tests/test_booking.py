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
