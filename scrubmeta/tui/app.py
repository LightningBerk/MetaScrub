"""Textual TUI interface for MetaScrub."""

import os
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.widgets import Header, Footer, Input, Button, DataTable, Label, ProgressBar, Log
from textual.worker import Worker, WorkerState
from textual import work

from scrubmeta.core import ScrubSummary, ScrubCallbacks, CancelToken, CoreScrubber
from scrubmeta.utils.result import ScrubResult, ResultType
from scrubmeta.tui.widgets import VisualCheckbox, SelectPathModal

STATUS_LABEL_ID = "#status-label"
BTN_CANCEL_ID = "#btn-cancel"


class MetaScrubTUI(App):
    """A Textual app to manage MetaScrub."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main-container {
        padding: 1 2;
        width: 100%;
        height: 100%;
    }

    .row {
        height: auto;
        margin-bottom: 1;
    }
    
    .input-row {
        height: auto;
        layout: horizontal;
    }

    Input {
        width: 1fr;
        margin-right: 1;
    }

    Button {
        margin-right: 1;
    }

    #options-container {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }

    VisualCheckbox {
        margin-right: 2;
        width: auto;
    }

    #progress-container {
        height: auto;
        margin-bottom: 1;
        layout: vertical;
    }

    #status-label {
        height: 1;
        margin-bottom: 1;
    }

    #results-table {
        height: 1fr;
        border: solid green;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, initial_input: str = ""):
        super().__init__()
        self.initial_input = initial_input
        self.cancel_token: Optional[CancelToken] = None
        self.scrubbing_worker: Optional[Worker] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Horizontal(classes="input-row row"):
                yield Input(placeholder="Input path (file or directory)", id="input-path", value=self.initial_input)
                yield Button("Browse", id="btn-browse-input")
            
            with Horizontal(classes="input-row row"):
                yield Input(placeholder="Output directory", id="output-dir")
                yield Button("Browse", id="btn-browse-output")
            
            with Horizontal(id="options-container"):
                yield VisualCheckbox("Recursive", id="check-recursive")
                yield VisualCheckbox("Keep Structure", id="check-keep-structure")
                yield VisualCheckbox("Overwrite", id="check-overwrite")
                yield VisualCheckbox("Dry Run", id="check-dry-run")
            
            with Horizontal(classes="row"):
                yield Button("Scrub", id="btn-scrub", variant="success")
                yield Button("Cancel", id=BTN_CANCEL_ID[1:], variant="error", disabled=True)
                yield Button("Clear", id="btn-clear")

            with Vertical(id="progress-container"):
                yield Label("Ready", id=STATUS_LABEL_ID[1:])
                yield ProgressBar(id="progress-bar", show_eta=False)

            yield DataTable(id="results-table")
        
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "MetaScrub TUI"
        table = self.query_one(DataTable)
        table.add_columns("Status", "Input", "Output", "Details")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-scrub":
            self.start_scrubbing()
        elif event.button.id == BTN_CANCEL_ID[1:]:
            self.cancel_scrubbing()
        elif event.button.id == "btn-clear":
            self.query_one(DataTable).clear()
            self.query_one(STATUS_LABEL_ID, Label).update("Ready")
            pb = self.query_one(ProgressBar)
            pb.progress = 0
            pb.total = None
        elif event.button.id == "btn-browse-input":
            def set_input(path: str | None) -> None:
                if path:
                    self.query_one("#input-path", Input).value = path
            self.push_screen(SelectPathModal("Select Input File/Directory"), set_input)
        elif event.button.id == "btn-browse-output":
            def set_output(path: str | None) -> None:
                if path:
                    self.query_one("#output-dir", Input).value = path
            self.push_screen(SelectPathModal("Select Output Directory"), set_output)

    def start_scrubbing(self) -> None:
        """Start the scrubbing process."""
        input_path_str = self.query_one("#input-path", Input).value.strip()
        output_dir_str = self.query_one("#output-dir", Input).value.strip()

        if not input_path_str or not output_dir_str:
            self.query_one(STATUS_LABEL_ID, Label).update("[red]Error: Input and Output paths are required.[/red]")
            return

        input_path = Path(input_path_str)
        output_dir = Path(output_dir_str)

        recursive = self.query_one("#check-recursive", VisualCheckbox).value
        keep_structure = self.query_one("#check-keep-structure", VisualCheckbox).value
        overwrite = self.query_one("#check-overwrite", VisualCheckbox).value
        dry_run = self.query_one("#check-dry-run", VisualCheckbox).value

        # Update UI state
        self.query_one("#btn-scrub", Button).disabled = True
        self.query_one("#btn-clear", Button).disabled = True
        self.query_one(BTN_CANCEL_ID, Button).disabled = False
        
        table = self.query_one(DataTable)
        table.clear()
        
        pb = self.query_one(ProgressBar)
        pb.progress = 0
        pb.total = None
        
        self.query_one(STATUS_LABEL_ID, Label).update("Scanning...")

        self.cancel_token = CancelToken()
        self.run_scrub_job(
            input_path, output_dir, recursive, keep_structure, overwrite, dry_run, self.cancel_token
        )

    def cancel_scrubbing(self) -> None:
        """Cancel the current scrub job."""
        if self.cancel_token:
            self.cancel_token.cancel()
            self.query_one(STATUS_LABEL_ID, Label).update("Cancelling... please wait.")
            self.query_one(BTN_CANCEL_ID, Button).disabled = True

    @work(thread=True)
    def run_scrub_job(self, input_path: Path, output_dir: Path, recursive: bool, 
                      keep_structure: bool, overwrite: bool, dry_run: bool, cancel_token: CancelToken) -> None:
        """Run the scrub operation in a separate thread."""
        
        def on_scan_start(total: int) -> None:
            self.call_from_thread(self._update_progress_total, total)
            
        def on_file_start(idx: int, total: int, file_path: Path) -> None:
            self.call_from_thread(self._update_status, f"Processing ({idx}/{total}): {file_path.name}")
            
        def on_file_result(result: ScrubResult) -> None:
            self.call_from_thread(self._add_result_row, result)
            
        def on_progress(idx: int, total: int) -> None:
            self.call_from_thread(self._update_progress, idx)
            
        def on_done(summary: ScrubSummary) -> None:
            self.call_from_thread(self._finish_scrubbing, summary)

        callbacks = ScrubCallbacks(
            on_scan_start=on_scan_start,
            on_file_start=on_file_start,
            on_file_result=on_file_result,
            on_progress=on_progress,
            on_done=on_done,
        )

        scrubber = CoreScrubber()
        scrubber.scrub_path(
            input_path=input_path,
            output_dir=output_dir,
            recursive=recursive,
            keep_structure=keep_structure,
            overwrite=overwrite,
            dry_run=dry_run,
            callbacks=callbacks,
            cancel_token=cancel_token
        )

    def _update_progress_total(self, total: int) -> None:
        """Update progress bar total."""
        pb = self.query_one(ProgressBar)
        pb.total = total
        self.query_one(STATUS_LABEL_ID, Label).update(f"Found {total} files. Starting...")

    def _update_status(self, message: str) -> None:
        """Update status label."""
        self.query_one(STATUS_LABEL_ID, Label).update(message)

    def _add_result_row(self, result: ScrubResult) -> None:
        """Add a result to the DataTable."""
        table = self.query_one(DataTable)
        
        status_color = "white"
        if result.result_type == ResultType.SUCCESS:
            status_color = "[green]SUCCESS[/green]"
        elif result.result_type == ResultType.ERROR:
            status_color = "[red]ERROR[/red]"
        elif result.result_type == ResultType.SKIP:
            status_color = "[yellow]SKIP[/yellow]"
            
        details = ""
        if result.result_type == ResultType.SUCCESS:
            if result.reason:
                details = f"removed: {result.reason}"
        elif result.result_type == ResultType.ERROR:
            details = result.error or "Unknown error"
        elif result.result_type == ResultType.SKIP:
            details = result.reason or "Skipped"
            
        in_path = str(result.input_path)
        out_path = str(result.output_path) if result.output_path else ""
        
        table.add_row(status_color, in_path, out_path, details)
        
        # Auto-scroll to bottom
        table.scroll_end(animate=False)

    def _update_progress(self, current: int) -> None:
        """Update current progress."""
        pb = self.query_one(ProgressBar)
        pb.progress = current

    def _finish_scrubbing(self, summary: ScrubSummary) -> None:
        """Called when scrubbing completes."""
        self.query_one("#btn-scrub", Button).disabled = False
        self.query_one("#btn-clear", Button).disabled = False
        self.query_one(BTN_CANCEL_ID, Button).disabled = True
        self.cancel_token = None
        
        msg = f"Done! Total: {summary.total} | Success: {summary.success} | Skipped: {summary.skipped} | Errors: {summary.errors}"
        if summary.cancelled:
            msg = "[yellow]CANCELLED.[/yellow] " + msg
            
        self.query_one(STATUS_LABEL_ID, Label).update(msg)

def main():
    import sys
    initial_input = ""
    if len(sys.argv) > 1:
        initial_input = sys.argv[1]
    
    app = MetaScrubTUI(initial_input=initial_input)
    app.run()

if __name__ == "__main__":
    main()
