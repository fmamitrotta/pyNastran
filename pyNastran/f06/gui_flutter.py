import os
import sys
import warnings
#from functools import wraps
from pathlib import Path
from typing import Callable, Optional, Any

ICON_PATH = Path('')
try:
    import json5 as json
except ModuleNotFoundError:
    warnings.warn('couldnt find json5, using json')
    import json
from functools import partial
#import numpy as np
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec

from qtpy import QtCore
from qtpy.compat import getopenfilename #, getsavefilename
from qtpy.QtWidgets import (
    QLabel, QWidget,
    QApplication, QMenu, QVBoxLayout, QLineEdit, QComboBox,
    QHBoxLayout, QPushButton, QGridLayout,
    QAction,
    QCheckBox, QListWidgetItem, QAbstractItemView,
    QListWidget, QSpinBox,
)
from qtpy.QtGui import QIcon
QLINEEDIT_WHITE = 'QLineEdit {background-color: white;}'
QLINEEDIT_RED = 'QLineEdit {background-color: red;}'

from cpylog import SimpleLogger
#import pyNastran
from pyNastran.gui.utils.qt.pydialog import QFloatEdit, make_font
from pyNastran.gui.qt_files.named_dock_widget import NamedDockWidget
from pyNastran.gui.qt_files.loggable_gui import LoggableGui

from pyNastran.f06.flutter_response import FlutterResponse, Limit
from pyNastran.f06.parse_flutter import make_flutter_response


X_PLOT_TYPES = ['eas', 'tas', 'rho', 'q', 'mach', 'alt', 'kfreq', '1/kfreq']
PLOT_TYPES = ['x-damp-freq', 'x-damp-kfreq', 'root-locus']
UNITS_IN = ['english_in', 'english_kt', 'english_ft',
            'si', 'si_mm']
UNITS_OUT = UNITS_IN
HOME_DIRNAME = os.path.expanduser('~')
HOME_FILENAME = os.path.join(HOME_DIRNAME, 'plot_flutter.json')

#FONT_SIZE = 12

class Action:
    def __init__(self, name: str, text: str, icon: str='',
                 func=Callable, show: bool=True):
        self.name = name
        self.text = text
        self.ico = icon
        self.func = func
        self.show = show

    def __repr__(self) -> str:
        return f'Action(name={self.name}, text={self.text}'

    @property
    def icon_path(self) -> str:
        if self.ico == '':
            return self.ico
        return str(ICON_PATH / self.ico)

class MainWindow(LoggableGui):
    def __init__(self, f06_filename: str=''):
        super().__init__(html_logging=False)
        self.font_size = 10
        self.show_lines = True
        self.show_points = True
        self._units_in = ''
        self._units_out = ''
        self.units_in = ''
        self.units_out = ''
        self.use_dock_widgets = False
        self.qactions = {}
        self.nrecent_files_max = 9
        self.recent_files = []
        self.save_filename = HOME_FILENAME
        self.is_valid = False

        self.data = {}
        self.f06_filename = ''
        self.subcase = 0
        self.x_plot_type = 'eas'
        self.plot_type = 'x-damp-freq'
        self.eas_lim = []
        #self.tas_lim = []
        #self.alt_lim = []
        #self.q_lim = []
        #self.rho_lim = []
        #self.x_lim = []
        self.freq_lim = [None, None]
        self.damping_lim = [None, None]
        self.kfreq_lim = [None, None]
        self.eigr_lim = [None, None]
        self.eigi_lim = [None, None]
        self.responses = {}
        self.modes = []
        self.selected_modes = []
        self.freq_tol = -1.0
        self.freq_tol_remove = -1.0

        self.setup_widgets()
        self.setup_layout()
        self.on_load_settings()
        if f06_filename:
            self.f06_filename_edit.setText(f06_filename)

        self.setup_toolbar()
        self._update_recent_files_actions()
        self.setup_connections()
        self._set_window_title()
        self.on_font_size()

    def setup_toolbar(self):
        #frame = QFrame(self)

        actions_input = {
            #'file_load': Action(name='file_load', text='Load...', func=self.on_file_load, icon='folder.png'),
            #'file_save': Action(name='file_save', text='Save...', func=self.on_file_save, icon='save.png'),
            #'file_save_as': Action(name='file_save_as', text='Save As...', func=self.on_file_save_as),
            'file_exit': Action(name='exit', text='Exit...', icon='exit2.jpg', func=self.on_file_exit),
        }
        recent_files = self._build_recent_file_actions(actions_input)
        actions = build_actions(self, actions_input)
        self.qactions = actions

        file_actions = [
            #'file_load',
            # 'file_save', 'file_save_as',
            ] + recent_files + [
            'file_exit']

        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu('File')
        #self.help_menu = self.menubar.addMenu('Help')

        help_actions = []
        menus_dict = {
            'File': (self.file_menu, file_actions),
            #'Help': (self.help_menu, help_actions),
        }
        build_menus(menus_dict, actions)
        #self.file_menu.addAction(actions['file_load'])
        #self.file_menu.addAction(actions['exit'])

        #self.toolbar = self.addToolBar('Show toolbar')
        #self.toolbar.setObjectName('main_toolbar')
        self.statusbar = self.statusBar()

    def _build_recent_file_actions(self, actions_input: dict[str, Action]) -> list[str]:
        recent_files = []
        nfiles = len(self.recent_files)
        for ifile in range(self.nrecent_files_max):
            name = f'file_{ifile}'
            pth = name
            func = partial(self.set_f06, ifile)
            show = (ifile <= nfiles)
            actions_input[name] = Action(name=name, text=pth, func=func, show=show)
            recent_files.append(name)

        if len(recent_files):
            recent_files.append('') # dash line
        return recent_files

    def set_f06(self, ifile: int) -> None:
        f06_filename = self.recent_files[ifile]
        self.f06_filename_edit.setText(f06_filename)
        self.on_load_f06()

    def setup_modes(self):
        self.modes_widget = QListWidget(self)
        self.modes_widget.setMaximumWidth(100)
        self.modes_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._set_modes_table(self.modes_widget, [0])

    # def dontcrash(func):
    #     @wraps(func)
    #     def wrapper(self, *args, **kwargs):
    #         # do something before `sum`
    #         result = func(self) # , *args, **kwargs
    #         # do something after `sum`
    #         return result
    #     return wrapper

    # @dontcrash
    def on_file_exit(self):
        if hasattr(self, 'on_file_save') and hasattr(self, 'save_filename'):
            self.on_file_save()

    def on_file_save(self) -> None:
        if self.save_filename == '' or not os.path.exists(self.save_filename):
            self.on_file_save_as()
        else:
            self._save(self.save_filename)

    def on_file_save_as(self) -> None:
        # if 0:
        #     #print('on_file_save')
        #     qt_wildcard = '*.json'
        #     basedir = str(DIRNAME)
        #     json_filename, wildcard = getsavefilename(
        #         self, caption=title, basedir=basedir,
        #         filters=qt_wildcard,
        #         #options=QFileDialog.setLabelText('data.json'),
        #     )
        #     self.log.info(f'json_filename={json_filename!r} wildcard={wildcard!r}')
        json_filename = self.save_filename
        self._save(json_filename)

    def _save(self, json_filename: str):
        is_valid = self.validate()
        #self.log.info(f'self.data = {self.data}')
        if json_filename == '' or len(self.data) == 0:
            return
        #print(f'json_filename={json_filename!r} wildcard={wildcard!r}')
        #print(f'self.data = {self.data}')
        with open(json_filename, 'w') as json_file:
            json.dump(self.data, json_file, indent=4)
        #print(f'fname="{fname}"')
        self.log.info(f'finished saving {json_filename!r}\n')
        self.save_filename = json_filename
        self._set_window_title()

    def _apply_settings(self, data: dict[str, Any]) -> None:
        if 'font_size' in data:
            self.font_size = data['font_size']
            self.font_size_edit.setValue(data['font_size'])

        checkboxs = [
            ('show_points', self.show_points_checkbox),
            ('show_lines', self.show_lines_checkbox),
            ('export_to_f06', self.export_f06_checkbox),
            ('export_to_csv', self.export_csv_checkbox),
            ('export_to_zona', self.export_zona_checkbox),
        ]
        # attrs aren't stored
        for (key, checkbox) in checkboxs:
            if key not in data:
                continue
            val = data[key]
            assert isinstance(val, bool), (key, val)
            checkbox.setChecked(val)

        min_max_line_edits = [
            ('eas_lim', self.eas_lim_edit_min, self.eas_lim_edit_max),
            ('xlim', self.xlim_edit_min, self.xlim_edit_max),
            ('damp_lim', self.damp_lim_edit_min, self.damp_lim_edit_max),
            ('freq_lim', self.freq_lim_edit_min, self.freq_lim_edit_max),
            ('kfreq_lim', self.kfreq_lim_edit_min, self.kfreq_lim_edit_max),
        ]
        for key, line_edit_min, line_edit_max in min_max_line_edits:
            if key not in data:
                #print(f'apply_settings: skipping key={key!r}')
                continue
            values = data[key]
            value0 = _to_str(values[0])
            value1 = _to_str(values[1])
            line_edit_min.setText(value0)
            line_edit_max.setText(value1)

        line_edits = [
            ('recent_files', 0, self.f06_filename_edit),
            ('freq_tol', -1, self.freq_tol_edit),
            ('freq_tol_remove', -1, self.freq_tol_remove_edit),
            ('output_directory', -1, self.output_directory_edit),
        ]
        for key, index, line_edit in line_edits:
            if key not in data:
                #print(f'apply_settings: skipping key={key!r}')
                continue
            values = data[key]
            if index != -1:
                value = values[index]
            else:
                value = values

            str_value = _to_str(value)

            #print('type(value) =', type(value))
            #print(f'{key+":":<10} values={values}[{index!r}]={value!r} -> {str_value!r}')
            line_edit.setText(str_value)

        pulldown_edits = [
            ('x_plot_type', self.x_plot_type_pulldown, X_PLOT_TYPES),
            ('plot_type', self.plot_type_pulldown, PLOT_TYPES),
            ('units_in', self.units_in_pulldown, UNITS_IN),
            ('units_out', self.units_out_pulldown, UNITS_OUT),
        ]
        for key, pulldown_edit, values in pulldown_edits:
            value = data[key]
            index = values.index(value)
            pulldown_edit.setCurrentIndex(index)

        self.recent_files = []
        for fname in data['recent_files']:
            abs_path = os.path.abspath(fname)
            if abs_path not in self.recent_files:
                self.recent_files.append(abs_path)

    def on_browse_f06(self) -> None:
        """pops a dialgo to select the f06 file"""
        title = 'Load Nastran Flutter F06 File'
        qt_wildcard = 'F06 File (*.f06)'
        basedir = ''
        fname, wildcard_level = getopenfilename(
            self, caption=title, basedir=basedir, filters=qt_wildcard,)
        self.f06_filename_edit.setText(fname)

    # @dontcrash
    def on_load_settings(self) -> None:
        json_filename = self.save_filename
        if not os.path.exists(json_filename):
            self.log.warning(f'unable to find {json_filename}')
            return
        # self.save_filename = json_filename
        try:
            with open(json_filename, 'r') as json_file:
                data = json.load(json_file)
            is_valid = validate_json(data, self.log)
            self._apply_settings(data)
        except Exception:
            self.log.error(f'failed to load {json_filename}')
            return
        self.log.info(f'finished loading {json_filename!r}')
        #return wildcard_level, fname
        self._set_window_title()

    def _set_window_title(self) -> None:
        if self.save_filename == '':
            self.setWindowTitle('Flutter Plot')
        else:
            self.setWindowTitle(f'Flutter Plot: {self.save_filename}')

    def setup_widgets(self) -> None:
        self.font_size_label = QLabel('Font Size')
        self.font_size_edit = QSpinBox()
        self.font_size_edit.setValue(self.font_size)

        self.f06_filename_label = QLabel('F06 Filename:')
        self.f06_filename_edit = QLineEdit('')
        # self.f06_filename_edit.setText(F06_FILENAME)
        self.f06_filename_browse = QPushButton('Browse...')
        # self.f06_filename_edit.setDisabled(True)
        #self.f06_filename_browse.setDisabled(True)
        #self.f06_filename_browse.setVisible(False)

        self.show_points_checkbox = QCheckBox('Show Points')
        self.show_lines_checkbox = QCheckBox('Show Lines')
        self.show_points_checkbox.setChecked(True)
        self.show_lines_checkbox.setChecked(True)

        self.export_csv_checkbox = QCheckBox('Export CSV')
        self.export_f06_checkbox = QCheckBox('Export F06')
        self.export_zona_checkbox = QCheckBox('Export Zona')
        self.export_csv_checkbox.setChecked(True)
        self.export_f06_checkbox.setChecked(True)
        self.export_zona_checkbox.setChecked(True)

        self.eas_lim_label = QLabel('EAS Limits:')
        self.eas_lim_edit_min = QFloatEdit('0')
        self.eas_lim_edit_max = QFloatEdit()

        self.xlim_label = QLabel('X Limits:')
        self.xlim_edit_min = QFloatEdit('0')
        self.xlim_edit_max = QFloatEdit()

        self.damp_lim_label = QLabel('Damping Limits (g):')
        self.damp_lim_edit_min = QFloatEdit('-0.3')
        self.damp_lim_edit_max = QFloatEdit('0.3')

        self.freq_lim_label = QLabel('Freq Limits (Hz):')
        self.freq_lim_edit_min = QFloatEdit('0')
        self.freq_lim_edit_max = QFloatEdit()

        self.kfreq_lim_label = QLabel('KFreq Limits:')
        self.kfreq_lim_edit_min = QFloatEdit()
        self.kfreq_lim_edit_max = QFloatEdit()


        self.eigr_lim_label = QLabel('Real Eigenvalue:')
        self.eigr_lim_edit_min = QFloatEdit()
        self.eigr_lim_edit_max = QFloatEdit()

        self.eigi_lim_label = QLabel('Imag Eigenvalue:')
        self.eigi_lim_edit_min = QFloatEdit()
        self.eigi_lim_edit_max = QFloatEdit()

        #--------------------------------------------
        self.freq_tol_label = QLabel('dFreq Tol (Hz) Dash:')
        self.freq_tol_edit = QFloatEdit()
        self.freq_tol_edit.setToolTip("Applies a dotted line for modes that don't change by more than some amount")

        self.freq_tol_remove_label = QLabel('dFreq Tol (Hz) Hide:')
        self.freq_tol_remove_edit = QFloatEdit()
        self.freq_tol_remove_edit.setToolTip("Completely remove modes that don't change by more than some amount")
        self.freq_tol_remove_label.setVisible(False)
        self.freq_tol_remove_edit.setVisible(False)

        self.subcase_label = QLabel('Subcase:')
        self.subcase_edit = QComboBox()

        units_msg = (
            "english_in: inch/s, slich/in^3\n"
            "english_ft: ft/s,   slug/ft^3\n"
            "english_kt: knots,  slug/ft^3\n"
            "si:         m/s,    kg/m^3\n"
            "si-mm:      mm/s,   Mg/mm^3\n"
        )
        self.x_plot_type_label = QLabel('X-Axis Plot Type:')
        self.x_plot_type_pulldown = QComboBox(self)
        self.x_plot_type_pulldown.addItems(X_PLOT_TYPES)
        self.x_plot_type_pulldown.setToolTip('sets the x-axis')

        self.plot_type_label = QLabel('Plot Type:')
        self.plot_type_pulldown = QComboBox(self)
        self.plot_type_pulldown.addItems(PLOT_TYPES)
        #self.plot_type_pulldown.setToolTip(units_msg)

        self.units_in_label = QLabel('Units In:')
        self.units_in_pulldown = QComboBox(self)
        self.units_in_pulldown.addItems(UNITS_IN)
        self.units_in_pulldown.setToolTip(units_msg)
        iunits_in = UNITS_IN.index('english_in')
        self.units_in_pulldown.setCurrentIndex(iunits_in)

        self.units_out_label = QLabel('Units Out:')
        self.units_out_pulldown = QComboBox()
        self.units_out_pulldown.addItems(UNITS_OUT)
        self.units_out_pulldown.setToolTip(units_msg)
        iunits_out = UNITS_IN.index('english_kt')
        self.units_out_pulldown.setCurrentIndex(iunits_out)

        self.output_directory_label = QLabel('Output Directory:')
        self.output_directory_edit = QLineEdit('', self)
        self.output_directory_browse = QPushButton('Browse...', self)
        self.output_directory_edit.setDisabled(True)
        self.output_directory_browse.setDisabled(True)

        self.f06_load_button = QPushButton('Load F06', self)
        self.ok_button = QPushButton('Run', self)
        self.setup_modes()
        self.on_plot_type()

    def on_plot_type(self) -> None:
        x_plot_type = self.x_plot_type_pulldown.currentText()
        plot_type = self.plot_type_pulldown.currentText()

        show_eas_lim = False
        show_xlim = False
        show_freq = False
        show_damp = False
        show_root_locus = False

        #PLOT_TYPES = ['x-damp-freq', 'x-damp-kfreq', 'root-locus']
        assert plot_type in PLOT_TYPES, plot_type

        if x_plot_type == 'kfreq':
            show_kfreq = True
        else:
            show_kfreq = False

        if plot_type == 'x-damp-freq':
            show_xlim = True
            show_damp = True
            show_freq = True
        elif plot_type == 'x-damp-kfreq':
            # kfreq-damp-kfreq not handled
            show_xlim = True
            show_damp = True
            show_kfreq = True
        elif plot_type == 'root-locus':
            show_root_locus = True
            show_kfreq = False
        else:  # pragma: no cover
            raise RuntimeError(f'plot_type={plot_type!r}')

        if show_xlim:
            if 'eas' == x_plot_type:
                show_eas_lim = True
                show_xlim = False

        self.x_plot_type_label.setVisible(not show_root_locus)
        self.x_plot_type_pulldown.setVisible(not show_root_locus)

        self.eas_lim_label.setVisible(show_eas_lim)
        self.eas_lim_edit_min.setVisible(show_eas_lim)
        self.eas_lim_edit_max.setVisible(show_eas_lim)

        self.xlim_label.setVisible(show_xlim)
        self.xlim_edit_min.setVisible(show_xlim)
        self.xlim_edit_max.setVisible(show_xlim)

        self.damp_lim_label.setVisible(show_damp)
        self.damp_lim_edit_min.setVisible(show_damp)
        self.damp_lim_edit_max.setVisible(show_damp)

        self.freq_lim_label.setVisible(show_freq)
        self.freq_lim_edit_min.setVisible(show_freq)
        self.freq_lim_edit_max.setVisible(show_freq)

        self.kfreq_lim_label.setVisible(show_kfreq)
        self.kfreq_lim_edit_min.setVisible(show_kfreq)
        self.kfreq_lim_edit_max.setVisible(show_kfreq)

        self.eigr_lim_label.setVisible(show_root_locus)
        self.eigr_lim_edit_min.setVisible(show_root_locus)
        self.eigr_lim_edit_max.setVisible(show_root_locus)

        self.eigi_lim_label.setVisible(show_root_locus)
        self.eigi_lim_edit_min.setVisible(show_root_locus)
        self.eigi_lim_edit_max.setVisible(show_root_locus)

    def setup_layout(self) -> None:
        hbox = QHBoxLayout()
        hbox.addWidget(self.f06_filename_label)
        hbox.addWidget(self.f06_filename_edit)
        hbox.addWidget(self.f06_filename_browse)

        grid = QGridLayout()
        irow = 0

        # grid.addWidget(self.f06_filename_label, irow, 0)
        # grid.addWidget(self.f06_filename_edit, irow, 1)
        # grid.addWidget(self.f06_filename_browse, irow, 2)
        # irow += 1

        grid.addWidget(self.font_size_label, irow, 0)
        grid.addWidget(self.font_size_edit, irow, 1)
        irow += 1

        grid.addWidget(self.units_in_label, irow, 0)
        grid.addWidget(self.units_in_pulldown, irow, 1)
        irow += 1

        grid.addWidget(self.units_out_label, irow, 0)
        grid.addWidget(self.units_out_pulldown, irow, 1)
        irow += 1

        grid.addWidget(self.subcase_label, irow, 0)
        grid.addWidget(self.subcase_edit, irow, 1)
        irow += 1

        grid.addWidget(self.x_plot_type_label, irow, 0)
        grid.addWidget(self.x_plot_type_pulldown, irow, 1)
        irow += 1
        grid.addWidget(self.plot_type_label, irow, 0)
        grid.addWidget(self.plot_type_pulldown, irow, 1)
        irow += 1

        #--------------------------------------------------
        # x-axis
        grid.addWidget(self.eas_lim_label, irow, 0)
        grid.addWidget(self.eas_lim_edit_min, irow, 1)
        grid.addWidget(self.eas_lim_edit_max, irow, 2)
        irow += 1

        grid.addWidget(self.xlim_label, irow, 0)
        grid.addWidget(self.xlim_edit_min, irow, 1)
        grid.addWidget(self.xlim_edit_max, irow, 2)
        irow += 1

        grid.addWidget(self.kfreq_lim_label, irow, 0)
        grid.addWidget(self.kfreq_lim_edit_min, irow, 1)
        grid.addWidget(self.kfreq_lim_edit_max, irow, 2)
        irow += 1
        #--------------------------------------------------
        # y-axes
        grid.addWidget(self.damp_lim_label, irow, 0)
        grid.addWidget(self.damp_lim_edit_min, irow, 1)
        grid.addWidget(self.damp_lim_edit_max, irow, 2)
        irow += 1

        grid.addWidget(self.freq_lim_label, irow, 0)
        grid.addWidget(self.freq_lim_edit_min, irow, 1)
        grid.addWidget(self.freq_lim_edit_max, irow, 2)
        irow += 1
        #--------------------------------------------------

        grid.addWidget(self.eigr_lim_label, irow, 0)
        grid.addWidget(self.eigr_lim_edit_min, irow, 1)
        grid.addWidget(self.eigr_lim_edit_max, irow, 2)
        irow += 1

        grid.addWidget(self.eigi_lim_label, irow, 0)
        grid.addWidget(self.eigi_lim_edit_min, irow, 1)
        grid.addWidget(self.eigi_lim_edit_max, irow, 2)
        irow += 1
        #------------------------------------------
        grid.addWidget(self.freq_tol_label, irow, 0)
        grid.addWidget(self.freq_tol_edit, irow, 1)
        irow += 1
        grid.addWidget(self.freq_tol_remove_label, irow, 0)
        grid.addWidget(self.freq_tol_remove_edit, irow, 1)
        irow += 1

        grid.addWidget(self.output_directory_label, irow, 0)
        grid.addWidget(self.output_directory_edit, irow, 1)
        grid.addWidget(self.output_directory_browse, irow, 2)
        self.output_directory_label.setDisabled(True)
        self.output_directory_edit.setDisabled(True)
        self.output_directory_browse.setDisabled(True)
        irow += 1

        jrow = 0
        grid_check = QGridLayout()
        grid_check.addWidget(self.show_points_checkbox, jrow, 0)
        grid_check.addWidget(self.show_lines_checkbox, jrow, 1)
        jrow += 1
        grid_check.addWidget(self.export_csv_checkbox, jrow, 0)
        grid_check.addWidget(self.export_f06_checkbox, jrow, 1)
        grid_check.addWidget(self.export_zona_checkbox, jrow, 2)
        jrow += 1

        ok_cancel_hbox = QHBoxLayout()
        ok_cancel_hbox.addWidget(self.f06_load_button)
        ok_cancel_hbox.addWidget(self.ok_button)

        hbox_check = QHBoxLayout()
        hbox_check.addLayout(grid_check)
        hbox_check.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(grid)
        vbox.addLayout(hbox_check)
        vbox.addStretch(1)
        vbox.addLayout(ok_cancel_hbox)

        #log_widget = ApplicationLogWidget(self)

        log_widget = self.setup_logging()
        if self.use_dock_widgets:
            self.modes_dock_widget = NamedDockWidget('Modes', self.modes_widget, self)
            self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.modes_dock_widget)
            self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.log_dock_widget)
            vbox2 = vbox
        else:
            #self.log_dock_widget.hide()
            vbox2 = QHBoxLayout()
            vbox2.addWidget(self.modes_widget)
            vbox2.addLayout(vbox)
        widget = QWidget()
        widget.setLayout(vbox2)
        self.setCentralWidget(widget)

    def setup_connections(self) -> None:
        self.f06_load_button.clicked.connect(self.on_load_f06)
        self.x_plot_type_pulldown.currentIndexChanged.connect(self.on_plot_type)
        self.plot_type_pulldown.currentIndexChanged.connect(self.on_plot_type)
        self.subcase_edit.currentIndexChanged.connect(self.on_subcase)
        self.f06_filename_browse.clicked.connect(self.on_browse_f06)
        self.font_size_edit.valueChanged.connect(self.on_font_size)
        #self.modes_widget.itemSelectionChanged.connect(self.on_modes)
        # self.modes_widget.itemClicked.connect(self.on_modes)
        # self.modes_widget.currentRowChanged.connect(self.on_modes)
        self.ok_button.clicked.connect(self.on_ok)

    def on_font_size(self) -> None:
        self.font_size = self.font_size_edit.value()
        font = make_font(self.font_size, is_bold=False)
        self.setFont(font)

    # @dontcrash
    def on_load_f06(self) -> None:
        f06_filename = os.path.abspath(self.f06_filename_edit.text())
        if not os.path.exists(f06_filename) or not os.path.isfile(f06_filename):
            self.f06_filename_edit.setStyleSheet(QLINEEDIT_RED)
            self.log.error(f"can't find {f06_filename}")
            return
        self.f06_filename_edit.setStyleSheet(QLINEEDIT_WHITE)
        self.f06_filename = f06_filename
        f06_units = self.units_in_pulldown.currentText()
        out_units = self.units_out_pulldown.currentText()
        try:
            self.responses: FlutterResponse = make_flutter_response(
                f06_filename,
                f06_units=f06_units, out_units=out_units,
                make_alt=True,
                log=self.log)
        except Exception as e:
            self.log.error(str(e))
            return

        subcases = list(self.responses.keys())
        if len(subcases) == 0:
            self.log.error('No subcases found')
            return
        self._units_in = f06_units
        self._units_out = out_units
        self.add_recent_file(f06_filename)
        self.update_subcases(subcases)

    def add_recent_file(self, f06_filename: str) -> None:
        path = os.path.abspath(f06_filename)
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files = [path] + self.recent_files
        if len(self.recent_files) > self.nrecent_files_max:
            self.recent_files = self.recent_files[:self.nrecent_files_max]

        self._update_recent_files_actions()
        self._save(self.save_filename)

    def _update_recent_files_actions(self) -> None:
        current_directory = os.getcwd()
        for ifile in range(self.nrecent_files_max):
            name = f'file_{ifile}'
            try:
                fname = self.recent_files[ifile]
                show = True
            except IndexError:
                show = False

            action: QAction = self.qactions[name]
            active_text = action.text()

            if show != action.isVisible():
                action.setVisible(show)

            if show and active_text != fname:
                # only update text if it's visible
                relative_fname = os.path.relpath(fname, current_directory)
                text = fname
                if len(relative_fname) < len(fname):
                    text = relative_fname
                action.setText(text)

    def on_subcase(self) -> None:
        subcase, is_subcase_valid = self._get_subcase()
        if not is_subcase_valid:
            return
        self.update_modes_table(self.responses[subcase].modes)

    def _get_subcase(self) -> tuple[int, bool]:
        subcase_str = self.subcase_edit.currentText()
        subcase_sline = subcase_str.split()
        try:
            subcase = int(subcase_sline[1])
            is_valid = True
        except IndexError:
            self.log.error(f'failed parsing subcase={subcase_str}; subcase_sline={subcase_sline}')
            subcase = -1
            is_valid = False
        return subcase, is_valid

    def update_subcases(self, subcases: list[int]) -> None:
        self.subcase_edit.clear()
        subcases_text = [f'Subcase {isubcase}' for isubcase in subcases]
        self.subcase_edit.addItems(subcases_text)

    def update_modes_table(self, modes: list[int]) -> None:
        self.modes = modes
        self._set_modes_table(self.modes_widget, modes)
        self.log.info(f'modes = {self.modes}')

    def on_modes(self) -> None:
        self.on_ok()
        # self.validate()
        # self.plot(self.modes)

    # @dontcrash
    def _set_modes_table(self, modes_widget: QListWidget,
                         modes: list[int]):
        modes_widget.clear()
        for imode in modes:
            mode = QListWidgetItem(f"Mode {imode}")
            # mode.itemClicked.connect(self._on_update_mode)
            mode.setSelected(True)
            modes_widget.addItem(mode)

    def _on_update_mode(self):
        if not self.is_valid:
            self.validate()
        self.plot()

    def on_ok(self) -> None:
        is_valid = self.validate()
        if not is_valid:
            return

        modes = self.selected_modes
        if len(modes) == 0:
            self.log.warning(f'modes = {modes}; assuming all modes -> {self.modes}')
            modes = self.modes
            #return
        self.log.info(f'is_valid = {is_valid}\n')
        self.is_valid = True
        self.plot(modes)
        self._save(self.save_filename)

    # @dontcrash
    def plot(self, modes: list[int]) -> None:
        self.log.info(f'plot; modes = {modes}\n')
        if not self.is_valid:
            self.log.warning(f'not valid\n')
            return
        if len(self.responses) == 0:
            self.log.warning(f'no subcases\n')
            return

        x_plot_type = self.x_plot_type
        plot_type = self.plot_type
        self.log.info(f'plot_type = {plot_type}\n')

        export_to_csv = self.export_csv_checkbox.isChecked()
        export_to_f06 = self.export_f06_checkbox.isChecked()
        export_to_zona = self.export_zona_checkbox.isChecked()

        noline = not self.show_lines
        nopoints = not self.show_points

        freq_tol = self.freq_tol
        freq_tol_remove = self.freq_tol_remove
        self.log.info(f'freq_tol = {freq_tol}\n')
        if noline and nopoints:
            noline = False
            nopoints = True

        if x_plot_type == 'eas':
            xlim = self.eas_lim
        else:
            xlim = self.xlim

        xlim_kfreq = self.kfreq_lim
        ylim_damping = self.ydamp_lim
        ylim_freq = self.freq_lim
        damping_limit = None  # % damping

        # changing directory so we don't make a long filename
        # in teh plot header
        dirname = os.path.abspath(os.path.dirname(self.f06_filename))
        basename = os.path.basename(self.f06_filename)

        base = os.path.splitext(basename)[0]
        current_directory = os.getcwd()
        sys.stdout.flush()
        os.chdir(dirname)

        fig = plt.figure(1)
        fig.clear()
        if plot_type != 'root-locus':
            gridspeci = gridspec.GridSpec(2, 4)
            damp_axes = fig.add_subplot(gridspeci[0, :3])
            freq_axes = fig.add_subplot(gridspeci[1, :3], sharex=damp_axes)

        response = self.responses[self.subcase]

        # you can change the output units without reloading
        if self._units_in != self.units_in or self._units_out != self.units_out:
            # go back to the nominal units
            # _units_in was corrected to units_in
            # and then we go to units_out
            response.convert_units(self._units_out, self._units_in)
            response.convert_units(self.units_in, self.units_out)

        response.noline = noline
        response.nopoints = nopoints
        response.log = self.log
        #print('trying plots...')
        try:
            if plot_type == 'root-locus':
                png_filename = base + '_root-locus.png'
                axes = fig.add_subplot(111)
                response.plot_root_locus(
                    fig=fig, axes=axes,
                    modes=modes, eigr_lim=self.eigr_lim, eigi_lim=self.eigi_lim,
                    freq_tol=freq_tol,
                    show=True, clear=False, close=False,
                    legend=True,
                    png_filename=png_filename,
                )
            elif plot_type == 'x-damp-kfreq':
                #xlabel: eas
                #ylabel1 = r'Structural Damping; $g = 2 \gamma $'
                #ylabel2 = r'KFreq [rad]; $ \omega c / (2 V)$'
                #print('plot_kfreq_damping')
                png_filename = base + f'_{x_plot_type}-damp-kfreq.png'
                response.plot_kfreq_damping(
                    fig=fig, damp_axes=damp_axes, freq_axes=freq_axes,
                    modes=modes, plot_type=x_plot_type,
                    xlim=xlim, ylim_damping=ylim_damping, ylim_kfreq=xlim_kfreq,
                    freq_tol=freq_tol,
                    show=True, clear=False, close=False,
                    legend=True,
                    png_filename=png_filename,
                )
            else:
                assert plot_type in 'x-damp-freq', plot_type
                #print('plot_vg_vf')
                png_filename = base + f'_{x_plot_type}-damp-freq.png'
                response.plot_vg_vf(
                    fig=fig, damp_axes=damp_axes, freq_axes=freq_axes,
                    plot_type=x_plot_type,
                    modes=modes,
                    xlim=xlim, ylim_damping=ylim_damping, ylim_freq=ylim_freq,
                    freq_tol=freq_tol,
                    show=True, clear=False, close=False,
                    legend=True,
                    vd_limit=None, damping_limit=damping_limit,
                    png_filename=png_filename,
                )
        except Exception as e:
            self.log.error(str(e))
            raise

        base2 = os.path.splitext(png_filename)[0]
        csv_filename = base2 + '.export.csv'
        veas_filename = base2 + '.export.veas'
        f06_filename = base2 + '.export.f06'
        if export_to_csv:
            self.log.debug(f'writing {csv_filename}')
            response.export_to_csv(csv_filename, modes=modes)
        if export_to_zona:
            self.log.debug(f'writing {veas_filename}')
            response.export_to_veas(veas_filename, modes=modes)
        if export_to_f06:
            self.log.debug(f'writing {f06_filename}')
            response.export_to_f06(f06_filename, modes=modes)
        os.chdir(current_directory)
        self.log.info(f'saved {png_filename}')

    def get_xlim(self) -> tuple[Limit, Limit, Limit, Limit,
                                Limit, Limit, Limit,
                                Optional[float],
                                Optional[float], bool]:
        eas_lim_min, is_passed1 = get_float_or_none(self.eas_lim_edit_min)
        eas_lim_max, is_passed2 = get_float_or_none(self.eas_lim_edit_max)
        xlim_min, is_passed3 = get_float_or_none(self.xlim_edit_min)
        xlim_max, is_passed4 = get_float_or_none(self.xlim_edit_max)

        is_passed_x = all([is_passed1, is_passed2,
                           is_passed3, is_passed4])
        damp_lim_min, is_passed_damp1 = get_float_or_none(self.damp_lim_edit_min)
        damp_lim_max, is_passed_damp2 = get_float_or_none(self.damp_lim_edit_max)

        freq_lim_min, is_passed_freq1 = get_float_or_none(self.freq_lim_edit_min)
        freq_lim_max, is_passed_freq2 = get_float_or_none(self.freq_lim_edit_max)
        kfreq_lim_min, is_passed_kfreq1 = get_float_or_none(self.kfreq_lim_edit_min)
        kfreq_lim_max, is_passed_kfreq2 = get_float_or_none(self.kfreq_lim_edit_max)

        eigr_lim_min, is_passed_eigr1 = get_float_or_none(self.eigr_lim_edit_min)
        eigr_lim_max, is_passed_eigr2 = get_float_or_none(self.eigr_lim_edit_max)
        eigi_lim_min, is_passed_eigi1 = get_float_or_none(self.eigi_lim_edit_min)
        eigi_lim_max, is_passed_eigi2 = get_float_or_none(self.eigi_lim_edit_max)
        is_passed_eig = all([is_passed_eigr1, is_passed_eigr2,
                             is_passed_eigi1, is_passed_eigi2])

        freq_tol, is_passed_tol1 = get_float_or_none(self.freq_tol_edit)
        freq_tol_remove, is_passed_tol2 = get_float_or_none(self.freq_tol_remove_edit)
        if is_passed_tol1 and freq_tol is None:
            freq_tol = -1.0
        if is_passed_tol2 and freq_tol_remove is None:
            freq_tol_remove = -1.0

        eas_lim= [eas_lim_min, eas_lim_max]
        xlim = [xlim_min, xlim_max]
        damp_lim = [damp_lim_min, damp_lim_max]
        freq_lim = [freq_lim_min, freq_lim_max]
        kfreq_lim = [kfreq_lim_min, kfreq_lim_max]
        eigr_lim = [eigr_lim_min, eigr_lim_max]
        eigi_lim = [eigi_lim_min, eigi_lim_max]
        #self.log.info(f'XLim = {xlim}')
        is_passed_flags = [
            is_passed_x,
            is_passed_damp1, is_passed_damp2,
            is_passed_freq1, is_passed_freq2,
            is_passed_kfreq1, is_passed_kfreq2,
            is_passed_eig,
            is_passed_tol1, is_passed_tol2,
        ]
        is_passed = all(is_passed_flags)
        #print(f'is_passed_flags = {is_passed_flags}')
        #print(f'freq_tol = {freq_tol}')
        out = (
            eas_lim, xlim, damp_lim, freq_lim, kfreq_lim,
            eigr_lim, eigi_lim, freq_tol, freq_tol_remove, is_passed,
        )
        return out

    def get_selected_modes(self) -> list[int]:
        mode_strs = get_selected_items_flat(self.modes_widget)
        modes = [int(mode_str.split(' ')[1]) for mode_str in mode_strs]
        #self.log.info(f'modes = {modes}')
        return modes

    def validate(self) -> bool:
        (eas_lim, xlim,
         ydamp_lim, freq_lim, kfreq_lim,
         eigr_lim, eigi_lim,
         freq_tol, freq_tol_remove, is_valid_xlim) = self.get_xlim()

        subcase, is_subcase_valid = self._get_subcase()
        #if subcase == -1:
            #return False
        selected_modes = self.get_selected_modes()
        self.subcase = subcase
        self.selected_modes = selected_modes
        self.eas_lim = eas_lim
        self.xlim = xlim
        self.ydamp_lim = ydamp_lim
        self.kfreq_lim = kfreq_lim
        self.freq_lim = freq_lim
        self.eigi_lim = eigi_lim
        self.eigr_lim = eigr_lim
        self.freq_tol = freq_tol
        self.freq_tol_remove = freq_tol_remove

        self.x_plot_type = self.x_plot_type_pulldown.currentText()
        self.plot_type = self.plot_type_pulldown.currentText()
        units_in = self.units_in_pulldown.currentText()
        units_out = self.units_out_pulldown.currentText()
        output_directory = self.output_directory_edit.text()

        self.show_lines = self.show_lines_checkbox.isChecked()
        self.show_points = self.show_points_checkbox.isChecked()

        export_to_csv = self.export_csv_checkbox.isChecked()
        export_to_f06 = self.export_f06_checkbox.isChecked()
        export_to_zona = self.export_zona_checkbox.isChecked()
        data = {
            'show_points': self.show_points,
            'show_lines': self.show_lines,
            'export_to_csv': export_to_csv,
            'export_to_f06': export_to_f06,
            'export_to_zona': export_to_zona,

            'recent_files': self.recent_files,
            'font_size': self.font_size,
            'subcase': subcase,
            #'modes': modes,
            'selected_modes': selected_modes,
            'x_plot_type': self.x_plot_type,
            'plot_type': self.plot_type,
            'xlim': xlim,
            'eas_lim': eas_lim,
            'damp_lim': ydamp_lim,
            'freq_lim': freq_lim,
            'kfreq_lim': kfreq_lim,
            'eigr_lim': eigr_lim,
            'eigi_lim': eigi_lim,
            'output_directory': output_directory,
            'units_in': units_in,
            'units_out': units_out,
            'freq_tol': freq_tol,
            'freq_tol_remove': freq_tol_remove,
        }
        self.units_in = units_in
        self.units_out = units_out
        is_passed = all([is_valid_xlim, is_subcase_valid])
        if is_passed:
            self.data = data
            #self.xlim = xlim
            #self.ylim = ydamp_lim
            #self.data = data
            # is_valid = validate_json(self.data, self.log)
            #if is_valid != is_passed:
            #self.log.info(f'passed data:\n{str(self.data)}')
        else:
            del data['recent_files']
            self.log.error(f'failed data:\n{str(data)}')
        return is_passed


def get_selected_items_flat(list_widget: QListWidget) -> list[str]:
    items = list_widget.selectedItems()
    texts = []
    for item in items:
        text = item.text()
        texts.append(text)
    return texts

def build_menus(menus_dict: dict[str, tuple[QMenu, list[str]]],
                actions: dict[str, QAction]) -> None:
    for menu_name, (menu, actions_list) in menus_dict.items():
        assert isinstance(menu_name, str), menu_name
        for action_name in actions_list:
            assert isinstance(action_name, str), action_name
            if action_name == '':
                menu.addSeparator()
                continue
            #print(menu_name, action_name)
            action = actions[action_name]
            menu.addAction(action)
            #print('menu = ', menu)
            #print('action = ', action)

def build_actions(self, actions_input: dict[str, Action]) -> dict[str, QAction]:
    actions = {}
    tip = ''
    for name, action_inputi in actions_input.items():
        assert isinstance(action_inputi, Action), action_inputi
        func = action_inputi.func
        icon_path = action_inputi.icon_path
        txt = action_inputi.text
        show = action_inputi.show

        if icon_path and 0:
            ico = QIcon(icon_path)
            #print('icon_path = ', icon_path)
            assert os.path.exists(icon_path), icon_path
            action = QAction(txt, self)
            action.setIcon(ico)
        else:
            action = QAction(txt, self)

        if not show:
            action.setVisible(show)
        #action.setText(name)
        #action.setIcon()
        #action.setCheckable()
        #action.setShortcut(QKeySequence(name))
        if tip:
            #print(f'  found tip for {name}')
            action.setStatusTip(tip)
        if func:
            #print(f'  found func for {name}')
            action.triggered.connect(func)
        actions[name] = action
    return actions


def validate_json(data: dict[str, Any],
                  log: SimpleLogger) -> bool:
    is_valid = True
    #log.warning(f'keys = {list(data.keys())}')
    key_allowed_values = [
        ('units_in', UNITS_IN),
        ('units_out', UNITS_OUT),
        ('plot_type', PLOT_TYPES),
    ]
    for (key, allowed_values) in key_allowed_values:
        if key not in data:
            is_valid = False
            log.error(f'data[{key}] is missing; defaulting to {allowed_values[0]}')
            default_value = allowed_values[0]
            data[key] = default_value
            continue

        value = data[key]
        if value not in allowed_values:
            is_valid = False
            log.error(f'{key}={value!r} not in {allowed_values}; defaulting to {allowed_values[0]}')
            default_value = allowed_values[0]
            data[key] = default_value
    return is_valid

def get_float_or_none(line_edit: QLineEdit) -> tuple[Optional[float], bool]:
    # is_passed = False
    if not line_edit.isVisible():
        value = None
        is_passed = True
        return value, is_passed

    text = line_edit.text().strip()
    if len(text) == 0:
        value = None
        is_passed = True
    else:
        try:
            value = float(text)
            is_passed = True
        except ValueError:
            value = None
            is_passed = False
    return value, is_passed


def _to_str(value: Optional[int | float]) -> str:
    if value is None:
        str_value = ''
    else:
        str_value = str(value)
    return str_value

def main(f06_filename: str='') -> None:  # pragma: no cover
    # kills the program when you hit Cntl+C from the command line
    # doesn't save the current state as presumably there's been an error
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import sys
    # Someone is launching this directly
    # Create the QApplication
    app = QApplication(sys.argv)
    # The Main window

    main_window = MainWindow(f06_filename)
    main_window.show()
    # Enter the main loop
    app.exec_()


if __name__ == '__main__':
    main()
