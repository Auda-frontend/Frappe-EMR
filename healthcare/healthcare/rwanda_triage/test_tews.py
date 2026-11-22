# -*- coding: utf-8 -*-
"""
Boundary tests for tews.py, built from "TEWS Scoring Tables: Adult, Maternity,
Child and Infant Triage" and the rulings confirmed on 19 Nov 2026.

Runs with plain Python, no Frappe site needed:
    python3 -m unittest test_tews -v
(from the folder that holds tews.py and this file).
"""

import importlib.util
import os
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("tews", os.path.join(_HERE, "tews.py"))
tews = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tews)


def adult(**over):
    data = dict(mobility="0", rr=12, hr=80, sbp=120, temperature=36.8, avpu="Alert", trauma=0)
    data.update(over)
    return data


def child(**over):
    data = dict(mobility="0", rr=19, hr=90, temperature=36.8, avpu="Alert", trauma=0)
    data.update(over)
    return data


def infant(**over):
    data = dict(mobility="0", rr=30, hr=100, temperature=36.8, avpu="Alert", trauma=0)
    data.update(over)
    return data


def score(form, data, component):
    result = tews.calculate_tews(form, data)
    assert result["complete"], result
    return result["component_scores"][component]


def colour(form, data):
    return tews.determine_triage_color(form, data, tews.calculate_tews(form, data))


class BandTests(unittest.TestCase):
    def check(self, form, make, field, component, cases):
        for value, expected in cases:
            with self.subTest(form=form, field=field, value=value):
                self.assertEqual(score(form, make(**{field: value}), component), expected)

    def test_adult_and_maternity_rr(self):
        cases = [(8, 2), (9, 0), (14, 0), (15, 1), (20, 1), (21, 2), (29, 2), (30, 3)]
        for form in ("Adult", "Maternity"):
            self.check(form, adult, "rr", "rr_score", cases)

    def test_adult_and_maternity_hr(self):
        cases = [(40, 2), (41, 1), (50, 1), (51, 0), (100, 0), (101, 1),
                 (110, 1), (111, 2), (129, 2), (130, 3)]
        for form in ("Adult", "Maternity"):
            self.check(form, adult, "hr", "hr_score", cases)

    def test_adult_and_maternity_sbp(self):
        cases = [(70, 3), (71, 2), (80, 2), (81, 1), (100, 1), (101, 0),
                 (199, 0), (200, 2)]
        for form in ("Adult", "Maternity"):
            self.check(form, adult, "sbp", "sbp_score", cases)

    def test_child_rr(self):
        cases = [(14, 3), (15, 2), (16, 2), (17, 0), (21, 0), (22, 1), (26, 1), (27, 2)]
        self.check("Child", child, "rr", "rr_score", cases)

    def test_child_hr(self):
        cases = [(59, 3), (60, 2), (79, 2), (80, 0), (99, 0), (100, 1), (129, 1), (130, 2)]
        self.check("Child", child, "hr", "hr_score", cases)

    def test_infant_rr(self):
        cases = [(19, 3), (20, 2), (25, 2), (26, 0), (39, 0), (40, 1), (49, 1), (50, 2)]
        self.check("Infant", infant, "rr", "rr_score", cases)

    def test_infant_hr(self):
        cases = [(69, 3), (70, 2), (79, 2), (80, 0), (130, 0), (131, 1), (159, 1), (160, 2)]
        self.check("Infant", infant, "hr", "hr_score", cases)

    def test_temperature_is_the_same_on_every_form(self):
        cases = [(34.9, 2), (35.0, 0), (38.4, 0), (38.41, 2), (38.5, 2), (40.0, 2)]
        for form, make in (("Adult", adult), ("Maternity", adult),
                           ("Child", child), ("Infant", infant)):
            self.check(form, make, "temperature", "temp_score", cases)

    def test_avup(self):
        cases = [("Alert", 0), ("Voice", 1), ("Reacts to Voice", 1), ("Pain", 2),
                 ("Reacts to Pain", 2), ("Confused", 2), ("Unresponsive", 3)]
        for form, make in (("Adult", adult), ("Child", child), ("Infant", infant)):
            self.check(form, make, "avpu", "avpu_score", cases)

    def test_trauma(self):
        self.assertEqual(score("Adult", adult(trauma=1), "trauma_score"), 1)
        self.assertEqual(score("Adult", adult(trauma=0), "trauma_score"), 0)


class MobilityTests(unittest.TestCase):
    def test_adult_and_maternity_accept_0_1_2(self):
        for form in ("Adult", "Maternity"):
            for value in ("0", "1", "2"):
                with self.subTest(form=form, value=value):
                    self.assertEqual(score(form, adult(mobility=value), "mobility_score"), int(value))

    def test_child_and_infant_accept_only_0_and_2(self):
        for form, make in (("Child", child), ("Infant", infant)):
            self.assertEqual(score(form, make(mobility="0"), "mobility_score"), 0)
            self.assertEqual(score(form, make(mobility="2"), "mobility_score"), 2)
            with self.assertRaises(ValueError):
                tews.calculate_tews(form, make(mobility="1"))

    def test_adult_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            tews.calculate_tews("Adult", adult(mobility="3"))


class CompletenessTests(unittest.TestCase):
    def test_blank_or_zero_vitals_are_not_recorded(self):
        for field in ("rr", "hr", "sbp", "temperature"):
            for blank in (None, "", 0):
                with self.subTest(field=field, blank=blank):
                    result = tews.calculate_tews("Adult", adult(**{field: blank}))
                    self.assertFalse(result["complete"])
                    self.assertIn(field, result["missing_fields"])
                    self.assertIsNone(result["total"])

    def test_missing_choice_fields(self):
        for field in ("mobility", "avpu"):
            result = tews.calculate_tews("Adult", adult(**{field: ""}))
            self.assertFalse(result["complete"])
            self.assertIn("avpu" if field == "avpu" else "mobility", result["missing_fields"])

    def test_mobility_zero_is_a_real_answer(self):
        self.assertTrue(tews.calculate_tews("Adult", adult(mobility="0"))["complete"])

    def test_child_and_infant_do_not_need_sbp(self):
        for form, make in (("Child", child), ("Infant", infant)):
            result = tews.calculate_tews(form, make())
            self.assertTrue(result["complete"])
            self.assertNotIn("sbp_score", result["component_scores"])

    def test_adult_and_maternity_need_sbp(self):
        for form in ("Adult", "Maternity"):
            result = tews.calculate_tews(form, adult(sbp=None))
            self.assertFalse(result["complete"])
            self.assertEqual(result["missing_fields"], ["sbp"])

    def test_unknown_form_type(self):
        with self.assertRaises(ValueError):
            tews.calculate_tews("Teenager", adult())


class TotalTests(unittest.TestCase):
    def test_adult_example(self):
        # mobility 1, RR 22 (2), HR 105 (1), SBP 95 (1), temp 38.6 (2), Pain (2), trauma (1)
        data = adult(mobility="1", rr=22, hr=105, sbp=95, temperature=38.6, avpu="Pain", trauma=1)
        self.assertEqual(tews.calculate_tews("Adult", data)["total"], 10)

    def test_infant_example(self):
        # mobility 2, RR 52 (2), HR 165 (2), temp 36 (0), Voice (1), no trauma
        data = infant(mobility="2", rr=52, hr=165, temperature=36.0, avpu="Voice")
        self.assertEqual(tews.calculate_tews("Infant", data)["total"], 7)


class ColourTests(unittest.TestCase):
    def total_and_colour(self, data):
        result = tews.calculate_tews("Adult", data)
        return result["total"], tews.determine_triage_color("Adult", data, result)

    def test_total_to_colour(self):
        cases = [
            (adult(mobility="1", rr=15), 2, "GREEN"),
            (adult(mobility="1", rr=15, hr=101), 3, "YELLOW"),
            (adult(mobility="1", rr=15, hr=101, trauma=1), 4, "YELLOW"),
            (adult(mobility="2", rr=15, hr=101, trauma=1), 5, "ORANGE"),
            (adult(mobility="2", rr=15, hr=101, trauma=1, avpu="Voice"), 6, "ORANGE"),
            (adult(mobility="2", rr=15, hr=101, trauma=1, avpu="Pain"), 7, "RED"),
        ]
        for data, total, expected in cases:
            with self.subTest(total=total):
                self.assertEqual(self.total_and_colour(data), (total, expected))

    def test_emergency_sign_is_red_even_with_incomplete_vitals(self):
        data = {"alarm_not_breathing": 1}
        result = tews.calculate_tews("Adult", data)
        self.assertEqual(tews.determine_triage_color("Adult", data, result), "RED")

    def test_group_specific_emergency_signs(self):
        self.assertEqual(colour("Maternity", adult(alarm_prolapsed_cord=1)), "RED")
        self.assertEqual(colour("Child", child(alarm_central_cyanosis=1)), "RED")
        # A maternity sign on an adult form is not an emergency sign.
        self.assertEqual(colour("Adult", adult(alarm_prolapsed_cord=1)), "GREEN")

    def test_spo2(self):
        self.assertEqual(colour("Adult", adult(spo2=91)), "RED")
        self.assertEqual(colour("Adult", adult(spo2=92)), "GREEN")
        # 0 or blank is not recorded, so it must not turn the patient red.
        self.assertEqual(colour("Adult", adult(spo2=0)), "GREEN")
        self.assertEqual(colour("Adult", adult(spo2=None)), "GREEN")

    def test_very_urgent_sign_routes_to_orange(self):
        self.assertEqual(colour("Adult", adult(yellow_chest_pain=1)), "ORANGE")
        self.assertEqual(colour("Infant", infant(yellow_tiny_baby=1)), "ORANGE")

    def test_urgent_sign_routes_to_yellow(self):
        self.assertEqual(colour("Adult", adult(green_cant_drink=1)), "YELLOW")

    def test_incomplete_without_alarm_has_no_colour(self):
        self.assertIsNone(colour("Adult", adult(sbp=None)))


class FormTypeTests(unittest.TestCase):
    ON = "2026-11-19"

    def form(self, dob, maternity=False):
        return tews.detect_form_type(dob, maternity, self.ON)

    def test_three_years_is_infant(self):
        self.assertEqual(self.form("2023-11-19"), "Infant")   # exactly 36 months
        self.assertEqual(self.form("2023-11-20"), "Infant")   # 35 months 30 days
        self.assertEqual(self.form("2023-10-19"), "Child")    # 37 months

    def test_twelve_years_is_child_over_twelve_is_adult(self):
        self.assertEqual(self.form("2014-11-19"), "Child")    # exactly 144 months
        self.assertEqual(self.form("2014-10-19"), "Adult")    # 145 months

    def test_newborn_and_adult(self):
        self.assertEqual(self.form("2026-11-19"), "Infant")
        self.assertEqual(self.form("1990-05-01"), "Adult")

    def test_maternity_overrides_age(self):
        self.assertEqual(self.form("2012-01-01", maternity=True), "Maternity")
        self.assertEqual(self.form(None, maternity=True), "Maternity")

    def test_missing_dob_for_non_maternity_is_an_error(self):
        with self.assertRaises(ValueError):
            self.form(None)

    def test_future_dob_is_an_error(self):
        with self.assertRaises(ValueError):
            self.form("2027-01-01")


if __name__ == "__main__":
    unittest.main()
