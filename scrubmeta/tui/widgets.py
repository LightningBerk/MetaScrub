import os
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Button, Label, Static
from textual.reactive import reactive
from textual import events

class VisualCheckbox(Static, can_focus=True):
    """A custom checkbox that displays a green check or red X."""
    
    value = reactive(False)
    
    def __init__(self, label: str, id: str | None = None, value: bool = False, **kwargs):
        super().__init__(id=id, **kwargs)
        self.label_text = label
        self.value = value
    
    def on_mount(self) -> None:
        self.update_render()
        
    def watch_value(self, old_value: bool, new_value: bool) -> None:
        self.update_render()
        
    def update_render(self) -> None:
        if self.value:
            self.update(f"[green]✓[/green] {self.label_text}")
        else:
            self.update(f"[red]✗[/red] {self.label_text}")
            
    def on_click(self) -> None:
        self.value = not self.value
        
    def on_key(self, event: events.Key) -> None:
        if event.key == "space" or event.key == "enter":
            self.value = not self.value
            event.stop()

class SelectPathModal(ModalScreen[str]):
    """A modal to select a file or directory."""
    
    CSS = """
    SelectPathModal {
        align: center middle;
    }
    #dialog {
        width: 80%;
        height: 80%;
        border: thick $background 80%;
        background: $surface;
        layout: vertical;
    }
    #tree-container {
        height: 1fr;
        padding: 1;
    }
    #buttons {
        height: auto;
        dock: bottom;
        layout: horizontal;
        padding: 1;
        align: right middle;
    }
    #btn-select-current {
        margin-right: 1;
    }
    """
    
    def __init__(self, title: str = "Select Path", initial_path: str = "~", **kwargs):
        super().__init__(**kwargs)
        self.modal_title = title
        self.initial_path = os.path.expanduser(initial_path)
        
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.modal_title, id="title")
            with Vertical(id="tree-container"):
                yield DirectoryTree(self.initial_path, id="dir-tree")
            with Horizontal(id="buttons"):
                yield Button("Select Highlighted", id="btn-select-current", variant="primary")
                yield Button("Cancel", id="btn-cancel", variant="error")
                
    def on_mount(self) -> None:
        title = self.query_one("#title", Label)
        title.styles.padding = (1, 2)
        title.styles.text_style = "bold"

    def on_tree_node_highlighted(self, event: DirectoryTree.NodeHighlighted) -> None:
        if event.node.data:
            self.query_one("#title", Label).update(f"Selected: {event.node.data.path}")
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-select-current":
            tree = self.query_one("#dir-tree", DirectoryTree)
            if tree.cursor_node and tree.cursor_node.data:
                self.dismiss(str(tree.cursor_node.data.path))
            else:
                self.dismiss(str(tree.path))
        elif event.button.id == "btn-cancel":
            self.dismiss(None)
