"""Tests for core scrubbing API."""

from pathlib import Path
import tempfile
import shutil

from PIL import Image

from scrubmeta.core import scrub_path, ScrubCallbacks, CancelToken
from scrubmeta.utils.result import ResultType


def _make_image(path: Path, color: str = "red") -> None:
    img = Image.new("RGB", (32, 32), color=color)
    img.save(path, "PNG")


def test_scrub_path_invokes_callbacks():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        input_file = temp_dir / "input.png"
        output_dir = temp_dir / "out"
        output_dir.mkdir()
        _make_image(input_file)

        events = {"scan": 0, "file_start": 0, "file_result": 0, "progress": 0, "done": 0}

        callbacks = ScrubCallbacks(
            on_scan_start=lambda total: events.__setitem__("scan", total),
            on_file_start=lambda i, t, p: events.__setitem__("file_start", i),
            on_file_result=lambda r: events.__setitem__("file_result", events["file_result"] + 1),
            on_progress=lambda c, t: events.__setitem__("progress", c),
            on_done=lambda s: events.__setitem__("done", s.total),
        )

        results, summary = scrub_path(
            input_path=input_file,
            output_dir=output_dir,
            callbacks=callbacks,
        )

        assert summary.total == 1
        assert summary.success == 1
        assert results[0].result_type == ResultType.SUCCESS
        assert (output_dir / input_file.name).exists()
        assert events["scan"] == 1
        assert events["file_start"] == 1
        assert events["file_result"] == 1
        assert events["progress"] == 1
        assert events["done"] == 1
    finally:
        shutil.rmtree(temp_dir)


def test_cancel_stops_processing():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        input_dir = temp_dir / "inputs"
        input_dir.mkdir()
        output_dir = temp_dir / "out"
        output_dir.mkdir()

        _make_image(input_dir / "a.png", color="red")
        _make_image(input_dir / "b.png", color="blue")

        token = CancelToken()

        def on_result(res):
            # Cancel after the first result so the second file is skipped
            token.cancel()

        callbacks = ScrubCallbacks(on_file_result=on_result)

        results, summary = scrub_path(
            input_path=input_dir,
            output_dir=output_dir,
            callbacks=callbacks,
            cancel_token=token,
        )

        assert summary.cancelled is True
        assert summary.success == 1
        assert summary.skipped == 1
        assert summary.total == 2
        assert len(results) == 1
    finally:
        shutil.rmtree(temp_dir)
