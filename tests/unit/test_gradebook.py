from types import SimpleNamespace
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "backend"))

from app.services.gradebook import calculate_component_marks


def test_component_marks_use_average_percentage():
    component = SimpleNamespace(name="Assignments", item_count=4, item_total_marks=5, total_marks=10)

    assert calculate_component_marks(component, [4, 5, 3, 4]) == 8.0


def test_component_marks_reject_out_of_range_scores():
    component = SimpleNamespace(name="Assignments", item_count=4, item_total_marks=5, total_marks=10)

    with pytest.raises(ValueError, match="between 0 and 5"):
        calculate_component_marks(component, [4, 5, 3, 6])


@pytest.mark.parametrize("score", [float("nan"), float("inf"), float("-inf")])
def test_component_marks_reject_non_finite_scores(score):
    component = SimpleNamespace(name="Assignments", item_count=1, item_total_marks=5, total_marks=10)

    with pytest.raises(ValueError, match="between 0 and 5"):
        calculate_component_marks(component, [score])
