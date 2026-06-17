# -*- coding: utf-8 -*-
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")


def test_bar_dept_claim_exists():
    assert os.path.exists(os.path.join(CHARTS_DIR, "bar_dept_claim.png"))


def test_bar_insurance_reduction_exists():
    assert os.path.exists(os.path.join(CHARTS_DIR, "bar_insurance_reduction.png"))


def test_bar_dept_collection_exists():
    assert os.path.exists(os.path.join(CHARTS_DIR, "bar_dept_collection.png"))


def test_charts_are_nonempty():
    for fname in ["bar_dept_claim.png", "bar_insurance_reduction.png", "bar_dept_collection.png"]:
        fpath = os.path.join(CHARTS_DIR, fname)
        assert os.path.getsize(fpath) > 1000, "{} is too small".format(fname)
