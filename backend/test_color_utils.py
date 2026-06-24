from color_utils import color_distance, pick_most_distinct_color
from models import COLOR_PALETTE


def test_pick_most_distinct_color_avoids_nearby_green_options(monkeypatch):
    captured_choices = []

    def fake_choice(options):
        captured_choices.append(options)
        return options[0]

    monkeypatch.setattr("color_utils.random.choice", fake_choice)

    picked = pick_most_distinct_color(COLOR_PALETTE, {"#1b4332"})

    nearby_green_bgs = {"#0a2f1f", "#1a2e05"}
    candidate_bgs = {entry["bg"] for entry in captured_choices[0]}
    assert picked in COLOR_PALETTE
    assert not candidate_bgs & nearby_green_bgs
    assert color_distance(picked["bg"], "#1b4332") > max(
        color_distance(bg, "#1b4332") for bg in nearby_green_bgs
    )


def test_pick_most_distinct_color_with_empty_used_set_returns_palette_entry(monkeypatch):
    def fake_choice(options):
        return options[0]

    monkeypatch.setattr("color_utils.random.choice", fake_choice)

    picked = pick_most_distinct_color(COLOR_PALETTE, set())

    assert picked == COLOR_PALETTE[0]


def test_pick_most_distinct_color_with_exhausted_palette_returns_palette_entry(monkeypatch):
    def fake_choice(options):
        return options[0]

    monkeypatch.setattr("color_utils.random.choice", fake_choice)

    used_bgs = {entry["bg"] for entry in COLOR_PALETTE}
    picked = pick_most_distinct_color(COLOR_PALETTE, used_bgs)

    assert picked in COLOR_PALETTE
