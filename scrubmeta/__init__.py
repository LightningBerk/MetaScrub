"""MetaScrub - A tool for removing metadata from files."""

from .core import scrub_path, ScrubCallbacks, CancelToken, ScrubSummary

__version__ = "1.0.0"
__all__ = [
	"scrub_path",
	"ScrubCallbacks",
	"CancelToken",
	"ScrubSummary",
]
