import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend/backend"))

from app.services.timetable_validation import default_weekly_sessions, overlaps, time_minutes


class TimetableValidationUnitTests(unittest.TestCase):
    def test_credit_hours_supply_weekly_session_default(self):
        self.assertEqual(default_weekly_sessions(1), 1)
        self.assertEqual(default_weekly_sessions(2), 2)
        self.assertEqual(default_weekly_sessions(3), 3)

    def test_adjacent_sessions_do_not_overlap(self):
        self.assertFalse(overlaps("09:00", "10:00", "10:00", "11:00"))
        self.assertTrue(overlaps("09:00", "10:30", "10:00", "11:00"))

    def test_time_format_is_strict(self):
        self.assertEqual(time_minutes("08:30"), 510)
        with self.assertRaises(ValueError):
            time_minutes("8:30")
        with self.assertRaises(ValueError):
            time_minutes("25:00")


if __name__ == "__main__":
    unittest.main()
