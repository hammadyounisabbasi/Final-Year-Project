from math import isfinite


def calculate_component_marks(component, scores):
    """Convert item scores into the configured component marks by average percentage."""
    if len(scores) != component.item_count:
        raise ValueError(f"{component.name} requires {component.item_count} scores")
    if not isfinite(component.item_total_marks) or component.item_total_marks <= 0:
        raise ValueError(f"{component.name} has an invalid item total")
    if any(not isfinite(score) or score < 0 or score > component.item_total_marks for score in scores):
        raise ValueError(f"Scores for {component.name} must be between 0 and {component.item_total_marks:g}")
    average_ratio = sum(scores) / len(scores) / component.item_total_marks
    return round(average_ratio * component.total_marks, 4)
