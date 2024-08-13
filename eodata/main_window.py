from eodata.__about__ import __version__
from pathlib import Path
from typing import Final, List, cast

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QTabBar,
    QVBoxLayout,
    QMenuBar,
    QMenu,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, QSettings, QItemSelection, QPoint
from PySide6.QtGui import QKeySequence, QAction, QKeyEvent

from eodata.edf import EDF
from eodata.table import EDFTableModel, EDFTableView


class MainWindow(QMainWindow):
    MAX_RECENT: Final[int] = 10

    _tab_bar: QTabBar
    _table: EDFTableView
    _table_model: EDFTableModel

    _open_recent_menu: QMenu
    _edit_menu: QMenu

    _save_action: QAction
    _save_as_action: QAction
    _close_folder_action: QAction
    _cut_action: QAction
    _copy_action: QAction
    _paste_action: QAction
    _insert_rows_action: QAction
    _remove_rows_action: QAction
    _undo_action: QAction
    _redo_action: QAction
    _open_recent_actions: List[QAction]

    _data_folder: Path | None
    _edfs: List[EDF]

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Endless Data Studio")
        self.resize(1067, 750)

        self._tab_bar = QTabBar()
        self._tab_bar.addTab("Credits")
        self._tab_bar.addTab("Curse Filter")
        self._tab_bar.addTab("Jukebox")
        self._tab_bar.addTab("Game 1")
        self._tab_bar.addTab("Game 2")
        self._tab_bar.currentChanged.connect(self._tab_changed)

        self._table = EDFTableView()
        self._table.verticalHeader().setFixedWidth(30)
        self._table.horizontalHeader().setDefaultSectionSize(250)

        layout = QVBoxLayout()
        layout.addWidget(self._tab_bar)
        layout.addWidget(self._table)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        menu_bar = self._create_menu_bar()
        self._install_context_menus()

        self.setMenuBar(menu_bar)
        self._update_open_recent_actions()
        self._close_data_folder()

    def _create_menu_bar(self) -> QMenuBar:
        menu_bar = QMenuBar()

        open_action = QAction(
            "&Open Folder...",
            self,
            shortcut=QKeySequence.StandardKey.Open,
            statusTip="Open data folder",
            triggered=self._open_data_folder,
        )

        self._open_recent_menu = QMenu("Open &Recent", self)
        self._open_recent_actions = []

        for _ in range(MainWindow.MAX_RECENT):
            action = QAction(self, visible=False, triggered=self._open_recent)
            self._open_recent_actions.append(action)

        clear_recent_action = QAction(
            "&Clear Recently Opened...",
            self,
            statusTip="Clear recently opened folders",
            triggered=self._clear_recent,
        )

        self._open_recent_menu.addActions(self._open_recent_actions)
        self._open_recent_menu.addSeparator()
        self._open_recent_menu.addAction(clear_recent_action)

        self._save_action = QAction(
            "&Save",
            self,
            shortcut=QKeySequence.StandardKey.Save,
            statusTip="Save data files",
            triggered=self._save,
        )

        self._save_as_action = QAction(
            "Save &As",
            self,
            shortcut=QKeySequence.StandardKey.SaveAs,
            statusTip="Save data files under a new folder",
            triggered=self._save_as,
        )

        self._close_folder_action = QAction(
            "&Close Folder",
            self,
            shortcut=QKeySequence.StandardKey.Close,
            statusTip="Close data folder",
            triggered=self._close_data_folder,
        )

        exit_action = QAction(
            "E&xit",
            self,
            shortcut=QKeySequence.StandardKey.Quit,
            statusTip="Exit the application",
            triggered=QApplication.closeAllWindows,
        )

        self._cut_action = QAction(
            "Cu&t",
            self,
            shortcut=QKeySequence.StandardKey.Cut,
            statusTip="Cut selected cells to the clipboard",
            triggered=self._cut,
        )

        self._copy_action = QAction(
            "&Copy",
            self,
            shortcut=QKeySequence.StandardKey.Copy,
            statusTip="Copy selected cells to the clipboard",
            triggered=self._copy,
        )

        self._paste_action = QAction(
            "&Paste",
            self,
            shortcut=QKeySequence.StandardKey.Paste,
            statusTip="Paste data from the clipboard",
            triggered=self._paste,
        )

        self._clear_action = QAction(
            "C&lear",
            self,
            shortcut=QKeySequence.StandardKey.Delete,
            statusTip="Clear selected cells",
            triggered=self._clear,
        )

        self._insert_rows_action = QAction(
            "&Insert 1 row",
            self,
            shortcuts=[QKeySequence('Ctrl+Shift++'), QKeySequence('Ctrl++')],
            statusTip="Insert rows",
            triggered=self._insert_rows,
        )

        self._remove_rows_action = QAction(
            "&Delete 0 rows",
            self,
            shortcut=QKeySequence('Ctrl+-'),
            statusTip="Delete rows",
            triggered=self._remove_rows,
            enabled=False,
        )

        self._undo_action = QAction(
            "&Undo",
            self,
            shortcut=QKeySequence.StandardKey.Undo,
            statusTip="Undo the last action",
            triggered=self._undo,
        )

        self._redo_action = QAction(
            "&Redo",
            self,
            shortcut=QKeySequence.StandardKey.Redo,
            statusTip="Redo the last action",
            triggered=self._redo,
        )

        about_action = QAction(
            "&About",
            self,
            statusTip="Show information about the application",
            triggered=self._about,
        )

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(open_action)
        file_menu.addMenu(self._open_recent_menu)
        file_menu.addSeparator()
        file_menu.addAction(self._save_action)
        file_menu.addAction(self._save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self._close_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction(self._undo_action)
        edit_menu.addAction(self._redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._cut_action)
        edit_menu.addAction(self._copy_action)
        edit_menu.addAction(self._paste_action)
        edit_menu.addAction(self._clear_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._insert_rows_action)
        edit_menu.addAction(self._remove_rows_action)
        self._edit_menu = edit_menu

        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(about_action)

        return menu_bar

    def _install_context_menus(self) -> None:
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._table_context_menu_requested)

        self._table.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.horizontalHeader().customContextMenuRequested.connect(
            self._table_horizontal_header_context_menu_requested
        )

        self._table.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.verticalHeader().customContextMenuRequested.connect(
            self._table_vertical_header_context_menu_requested
        )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        if self._tab_bar.isEnabled():
            if event.matches(QKeySequence.StandardKey.NextChild):
                next_index = self._tab_bar.currentIndex() + 1
                if next_index >= self._tab_bar.count():
                    next_index = 0
                self._tab_bar.setCurrentIndex(next_index)
            elif event.matches(QKeySequence.StandardKey.PreviousChild):
                previous_index = self._tab_bar.currentIndex() - 1
                if previous_index < 0:
                    previous_index = self._tab_bar.count() - 1
                self._tab_bar.setCurrentIndex(previous_index)

    def _open_data_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select data directory")
        if folder:
            self._load_data_folder(Path(folder))

    def _open_recent(self) -> None:
        action = self.sender()
        if action:
            self._load_data_folder(Path(cast(QAction, action).data()))

    def _clear_recent(self) -> None:
        self._set_recent_list([])

    def _load_data_folder(self, path: Path) -> None:
        self._data_folder = path

        recent_list = self._get_recent_list()

        try:
            recent_list.remove(str(path))
        except ValueError:
            pass

        if self._update_data_folder(path):
            recent_list.insert(0, str(path))
            del recent_list[MainWindow.MAX_RECENT :]

        self._set_recent_list(recent_list)

    def _save(self) -> None:
        if self._data_folder is not None:
            self._do_save(self._data_folder)

    def _save_as(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select destination data directory")
        if folder:
            self._do_save(Path(folder))

    def _do_save(self, path: Path) -> None:
        writer = EDF.Writer(path)

        for i in range(12):
            edf_path = writer.write(self._edfs[i])
            if i == 0:
                # we just wrote the dat001 credits file, so now we can update the dat002 checksum
                self._update_checksum(edf_path)

    def _close_data_folder(self) -> None:
        self._data_folder = None
        self._update_data_folder(None)

    def _update_checksum(self, dat001) -> None:
        file_size = dat001.stat().st_size

        aeo_count = 0
        with open(dat001, 'r') as file:
            for character in file.read():
                if character in ['a', 'A', 'e', 'E', 'o', 'O']:
                    aeo_count = aeo_count + 1

        checksum = f"DAT001.ID{{{file_size * 3013 - 11}:145:{aeo_count}:{file_size * 21}}}"

        dat002 = self._edfs[1]
        dat002.lines.clear()
        dat002.lines.append(checksum)

    def _cut(self) -> None:
        self._table.cut()

    def _copy(self) -> None:
        self._table.copy()

    def _paste(self) -> None:
        self._table.paste()

    def _clear(self) -> None:
        self._table.clear()

    def _insert_rows(self) -> None:
        self._table.insert_rows()

    def _remove_rows(self) -> None:
        self._table.remove_rows()

    def _undo(self) -> None:
        # TODO: undo/redo
        pass

    def _redo(self) -> None:
        # TODO: undo/redo
        pass

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "About",
            "<h3>Endless Data Studio</h3>\n"
            + f"<p style=\"text-align:center\">version {__version__}</p>",
        )

    def _update_data_folder(self, path: Path | None) -> bool:
        model: EDFTableModel | None

        try:
            if path is None:
                self._edfs = []
                model = None
            else:
                reader = EDF.Reader(path)
                self._edfs = [reader.read(id) for id in range(1, 13)]
                model = EDFTableModel(self._edfs)

            self._table.setModel(model)
            self._tab_bar.setCurrentIndex(0)
            self._tab_bar.setEnabled(path is not None)
            self._data_folder = path

            selection_model = self._table.selectionModel()
            if selection_model:
                selection_model.selectionChanged.connect(self._selection_changed)
        except OSError as e:
            QMessageBox.information(
                self,
                'Could not open data folder',
                f'The specified data folder could not be opened.\n{e.strerror}',
                QMessageBox.StandardButton.Ok,
            )
            return False

        self._update_window_title()
        self._update_actions_enabled()
        self._update_insert_remove_actions()

        return True

    def _update_window_title(self):
        title = "Endless Data Studio"
        if self._data_folder is not None:
            display_path = str(self._data_folder.stem)
            title = f'{display_path} - {title}'
        self.setWindowTitle(title)

    def _update_actions_enabled(self):
        folder_open = self._data_folder is not None

        self._save_action.setEnabled(folder_open)
        self._save_as_action.setEnabled(folder_open)
        self._close_folder_action.setEnabled(folder_open)
        self._cut_action.setEnabled(folder_open)
        self._copy_action.setEnabled(folder_open)
        self._paste_action.setEnabled(folder_open)
        self._clear_action.setEnabled(folder_open)

    def _update_open_recent_actions(self):
        files = self._get_recent_list()
        recent_len = min(len(files), MainWindow.MAX_RECENT)

        for i in range(recent_len):
            self._open_recent_actions[i].setText(cast(str, files[i]).replace('&', '&&'))
            self._open_recent_actions[i].setData(files[i])
            self._open_recent_actions[i].setVisible(True)

        for i in range(recent_len, MainWindow.MAX_RECENT):
            self._open_recent_actions[i].setVisible(False)

        self._open_recent_menu.setEnabled(recent_len > 0)

    def _update_insert_remove_actions(self) -> None:
        selected_rows = self._table.selected_rows()

        if selected_rows:
            consecutive = selected_rows == list(range(min(selected_rows), max(selected_rows) + 1))
            insert_row_count = len(selected_rows) if consecutive else 0
            remove_row_count = len(selected_rows)
        else:
            insert_row_count = 1 if self._data_folder is not None else 0
            remove_row_count = 0

        self._insert_rows_action.setText(
            f"&Insert {insert_row_count} row{'' if insert_row_count == 1 else 's'}"
        )
        self._remove_rows_action.setText(
            f"&Delete {remove_row_count} row{'' if remove_row_count == 1 else 's'}"
        )
        self._insert_rows_action.setEnabled(insert_row_count != 0)
        self._remove_rows_action.setEnabled(remove_row_count != 0)

    def _tab_changed(self) -> None:
        if self._table.model():
            self._table.model().beginResetModel()
            cast(EDFTableModel, self._table.model()).kind = self._edf_kind_from_tab_index()
            self._table.model().endResetModel()
        self._update_insert_remove_actions()

    def _selection_changed(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        self._update_insert_remove_actions()

    def _table_context_menu_requested(self, point: QPoint) -> None:
        self._edit_menu.popup(self._table.viewport().mapToGlobal(point))

    def _table_horizontal_header_context_menu_requested(self, point: QPoint) -> None:
        column: int = self._table.horizontalHeader().logicalIndexAt(point)
        selection_model = self._table.selectionModel()
        if not selection_model.isColumnSelected(column):
            self._table.selectColumn(column)
        self._edit_menu.popup(self._table.viewport().mapToGlobal(point))

    def _table_vertical_header_context_menu_requested(self, point: QPoint) -> None:
        row: int = self._table.verticalHeader().logicalIndexAt(point)
        selection_model = self._table.selectionModel()
        if not selection_model.isRowSelected(row):
            self._table.selectRow(row)
        self._edit_menu.popup(self._table.viewport().mapToGlobal(point))

    def _edf_kind_from_tab_index(self) -> EDF.Kind:
        tab_index = self._tab_bar.currentIndex()
        match tab_index:
            case 0:
                return EDF.Kind.CREDITS
            case 1:
                return EDF.Kind.CURSE_FILTER
            case 2:
                return EDF.Kind.JUKEBOX
            case 3:
                return EDF.Kind.GAME_1
            case 4:
                return EDF.Kind.GAME_2
            case _:
                raise ValueError(f'Unhandled tab index: {tab_index}')

    def _get_recent_list(self) -> List[str]:
        settings = self._get_settings()
        result = settings.value('recentList')
        return result if isinstance(result, List) else []

    def _set_recent_list(self, recent_list: List[str]) -> None:
        settings = self._get_settings()
        settings.setValue('recentList', recent_list)
        self._update_open_recent_actions()

    def _get_settings(self) -> QSettings:
        return QSettings('cirras', 'Endless Data Studio')
