"""Models for presenting scrub results in the GUI."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtCore import QSortFilterProxyModel


class ResultsTableModel(QAbstractTableModel):
    """Table model holding scrub results."""

    headers = ["Status", "Input", "Output", "Message"]

    def __init__(self) -> None:
        super().__init__()
        self._rows: List[dict] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.ToolTipRole):
            return None

        row = self._rows[index.row()]
        column = index.column()

        if column == 0:
            return row.get("status", "")
        if column == 1:
            return row.get("input", "")
        if column == 2:
            return row.get("output", "")
        if column == 3:
            return row.get("message", "")
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # type: ignore[override]
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.headers):
            return self.headers[section]
        return None

    def append_row(self, row: dict) -> None:
        """Append a single result row."""
        self.beginInsertRows(QModelIndex(), len(self._rows), len(self._rows))
        self._rows.append(row)
        self.endInsertRows()

    def append_rows(self, rows: List[dict]) -> None:
        """Append multiple rows in one batch."""
        if not rows:
            return
        start = len(self._rows)
        end = start + len(rows) - 1
        self.beginInsertRows(QModelIndex(), start, end)
        self._rows.extend(rows)
        self.endInsertRows()

    def clear(self) -> None:
        """Clear all rows."""
        if not self._rows:
            return
        self.beginResetModel()
        self._rows.clear()
        self.endResetModel()

    def rows(self) -> List[dict]:
        """Return a shallow copy of rows for exporting/logging."""
        return list(self._rows)


class ResultFilterProxy(QSortFilterProxyModel):
    """Proxy model for filtering by status type."""

    def __init__(self) -> None:
        super().__init__()
        self.status_filter = "All"

    def set_status_filter(self, status: str) -> None:
        self.status_filter = status
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:  # type: ignore[override]
        if self.status_filter == "All":
            return True
        index = self.sourceModel().index(source_row, 0, source_parent)  # type: ignore[arg-type]
        value = self.sourceModel().data(index, Qt.DisplayRole)  # type: ignore[arg-type]
        return value == self.status_filter
