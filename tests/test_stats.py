# tests/test_stats.py
from mindflow.stats import Stats, StatsTracker


def test_acceptance_rate_zero_when_nothing_shown():
    assert Stats().acceptance_rate == 0.0


def test_acceptance_rate_computed():
    s = Stats(predictions_shown=4, suggestions_accepted=1)
    assert s.acceptance_rate == 0.25


def test_increment_and_persist(tmp_path):
    path = tmp_path / "stats.json"
    tracker = StatsTracker(path)
    tracker.increment("suggestions_accepted")
    tracker.increment("suggestions_accepted")
    tracker.increment("predictions_shown", 3)
    tracker.save()

    reloaded = StatsTracker(path)
    assert reloaded.stats.suggestions_accepted == 2
    assert reloaded.stats.predictions_shown == 3


def test_increment_unknown_field_is_ignored(tmp_path):
    tracker = StatsTracker(tmp_path / "stats.json")
    tracker.increment("does_not_exist")  # must not raise
    assert not hasattr(tracker.stats, "does_not_exist")


def test_disabled_tracker_does_not_count_or_write(tmp_path):
    path = tmp_path / "stats.json"
    tracker = StatsTracker(path, enabled=False)
    tracker.increment("suggestions_accepted")
    tracker.save()
    assert tracker.stats.suggestions_accepted == 0
    assert not path.exists()


def test_reset(tmp_path):
    path = tmp_path / "stats.json"
    tracker = StatsTracker(path)
    tracker.increment("suggestions_accepted")
    tracker.reset()
    assert tracker.stats.suggestions_accepted == 0


def test_corrupted_stats_file_starts_fresh(tmp_path):
    path = tmp_path / "stats.json"
    path.write_text("not valid json{{{")
    tracker = StatsTracker(path)
    assert tracker.stats.suggestions_accepted == 0
