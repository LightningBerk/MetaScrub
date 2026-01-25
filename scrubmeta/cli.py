"""Command-line interface for MetaScrub."""

import argparse
import sys
from pathlib import Path
from typing import List

from .core import CancelToken, ScrubCallbacks, scrub_path
from .utils.result import ScrubResult, ResultType, ErrorCategory


def print_summary(results: List[ScrubResult]) -> None:
    """
    Print summary of scrubbing results.

    Args:
        results: List of ScrubResults
    """
    total = len(results)
    success = sum(1 for r in results if r.result_type == ResultType.SUCCESS)
    skipped = sum(1 for r in results if r.result_type == ResultType.SKIP)
    errors = sum(1 for r in results if r.result_type == ResultType.ERROR)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total scanned:  {total}")
    print(f"Successfully scrubbed: {success}")
    print(f"Skipped:        {skipped}")
    print(f"Errors:         {errors}")

    # Break down errors by category
    if errors > 0:
        error_results = [r for r in results if r.result_type == ResultType.ERROR]
        category_counts = {}
        for result in error_results:
            cat = result.error_category or ErrorCategory.PROCESSING_ERROR
            category_counts[cat] = category_counts.get(cat, 0) + 1

        print("\nError breakdown by category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category.value}: {count}")

    print("=" * 60)


def scrub_command(args: argparse.Namespace) -> int:
    """
    Execute the scrub command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    input_path = Path(args.input_path).resolve()
    output_dir = Path(args.out).resolve()

    # Validate input
    if not input_path.exists():
        print(f"ERROR: Input path does not exist: {input_path}")
        return 1

    # Create output directory
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"ERROR: Failed to create output directory: {e}")
        return 1

    # Run scrubber through shared core
    results: List[ScrubResult] = []

    def handle_result(res: ScrubResult) -> None:
        results.append(res)
        print(res.format_line())

    callbacks = ScrubCallbacks(on_file_result=handle_result)
    cancel_token = CancelToken()

    _, summary = scrub_path(
        input_path=input_path,
        output_dir=output_dir,
        recursive=args.recursive,
        keep_structure=args.keep_structure,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        ffmpeg_cmd=args.ffmpeg_path,
        callbacks=callbacks,
        cancel_token=cancel_token,
    )

    if summary.total == 0:
        print(f"No supported files found in: {input_path}")
        return 0

    print_summary(results)

    if summary.errors:
        return 1

    return 0


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="scrubmeta",
        description="Remove metadata from images, PDFs, Office docs, and audio/video files, writing clean copies to an output directory."
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrub command
    scrub_parser = subparsers.add_parser("scrub", help="Scrub metadata from files")
    scrub_parser.add_argument(
        "input_path",
        help="Path to a single file or directory to process"
    )
    scrub_parser.add_argument(
        "--out",
        required=True,
        help="Output directory for cleaned files"
    )
    scrub_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process subdirectories recursively (when input is a directory)"
    )
    scrub_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without actually processing files"
    )
    scrub_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files (default: append suffix for duplicates)"
    )
    scrub_parser.add_argument(
        "--keep-structure",
        action="store_true",
        help="Preserve directory structure in output (for batch processing)"
    )
    scrub_parser.add_argument(
        "--ffmpeg-path",
        default="ffmpeg",
        help="Path or command name for ffmpeg (used for audio/video scrubbing; default: ffmpeg in PATH)",
    )

    args = parser.parse_args()

    if args.command == "scrub":
        sys.exit(scrub_command(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
