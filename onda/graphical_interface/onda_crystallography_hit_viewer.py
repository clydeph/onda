#!/usr/bin/env python
#    This file is part of OnDA.
#
#    OnDA is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OnDA is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with OnDA.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
import copy
import os
import os.path
import signal
import sys

import numpy
import pyqtgraph as pg

import cfelpyutils.cfel_geom as cgm
import ondautils.onda_zmq_gui_utils as zgut

try:
    from PyQt5 import QtCore, QtGui
    from PyQt5.uic import loadUiType
except ImportError:
    from PyQt4 import QtCore, QtGui
    from PyQt4.uic import loadUiType


class MainFrame(QtGui.QMainWindow):

    _listening_thread_start_processing = QtCore.pyqtSignal()
    _listening_thread_stop_processing = QtCore.pyqtSignal()

    def __init__(self, geom_filename, rec_ip, rec_port):
        super(MainFrame, self).__init__()

        self._pixel_maps = cgm.pixel_maps_for_image_view(geom_filename)
        self._img_shape = cgm.get_image_shape(geom_filename)
        self._img = numpy.zeros(self._img_shape, dtype=numpy.float)

        self._data = collections.deque(maxlen=20)
        self._data_index = -1

        self._init_listening_thread(rec_ip, rec_port)

        self._ring_pen = pg.mkPen('r', width=2)
        self._peak_canvas = pg.ScatterPlotItem()
        ui_mainwindow, _ = loadUiType(os.path.join(os.environ['ONDA_INSTALLATION_DIR'], 'GUI', 'ui_files',
                                                   'OndaCrystallographyHitViewerGUI.ui'))
        self._ui = ui_mainwindow()
        self._ui.setupUi(self)
        self._init_ui()

        self._refresh_timer = QtCore.QTimer()
        self._init_timer()
        self.show()

    def _init_ui(self):
        self._ui.imageView.ui.menuBtn.hide()
        self._ui.imageView.ui.roiBtn.hide()

        self._ui.imageView.getView().addItem(self._peak_canvas)

        self._ui.backButton.clicked.connect(self._back_button_clicked)
        self._ui.forwardButton.clicked.connect(self._forward_button_clicked)
        self._ui.playPauseButton.clicked.connect(self._play_pause_button_clicked)

    def _back_button_clicked(self):
        if self._refresh_timer.isActive():
            self._stop_stream()
        if self._data_index > 0:
            self._data_index -= 1
            self._update_image_plot()

    def _forward_button_clicked(self):
        if self._refresh_timer.isActive():
            self._stop_stream()
        if (self._data_index + 1) < len(self._data):
            self._data_index += 1
            self._update_image_plot()

    def _stop_stream(self):
        self._refresh_timer.stop()
        self._ui.playPauseButton.setText('Play')
        self._data_index = len(self._data) - 1

    def _start_stream(self):
        self._refresh_timer.start(250)
        self._ui.playPauseButton.setText('Pause')

    def _play_pause_button_clicked(self):
        if self._refresh_timer.isActive():
            self._stop_stream()
        else:
            self._start_stream()

    def _init_listening_thread(self, rec_ip, rec_port):
        self.zeromq_listener_thread = QtCore.QThread()
        self.zeromq_listener = zgut.ZMQListener(rec_ip, rec_port, u'ondarawdata')
        self.zeromq_listener.zmqmessage.connect(self._data_received)
        self.zeromq_listener.start_listening()
        self._listening_thread_start_processing.connect(self.zeromq_listener.start_listening)
        self._listening_thread_stop_processing.connect(self.zeromq_listener.stop_listening)
        self.zeromq_listener.moveToThread(self.zeromq_listener_thread)
        self.zeromq_listener_thread.start()
        self._listening_thread_start_processing.emit()

    def _init_timer(self):
        self._refresh_timer.timeout.connect(self._update_image_plot)
        self._refresh_timer.start(250)

    def _data_received(self, datdict):
        self._data.append(copy.deepcopy(datdict))

    def _update_image_plot(self):
        if self._data:

            data = self._data[self._data_index]

            self._img[self._pixel_maps.y, self._pixel_maps.x] = data['raw_data'].ravel().astype(self._img.dtype)

            QtGui.QApplication.processEvents()

            peak_x = []
            peak_y = []
            for peak_fs, peak_ss in zip(data['peak_list'].fs, data['peak_list'].ss):
                peak_in_slab = int(round(peak_ss))*data['raw_data'].shape[1]+int(round(peak_fs))
                peak_x.append(self._pixel_maps.x[peak_in_slab])
                peak_y.append(self._pixel_maps.y[peak_in_slab])

            QtGui.QApplication.processEvents()

            self._ui.imageView.setImage(self._img.T, autoLevels=False, autoRange=False, autoHistogramRange=False)
            self._peak_canvas.setData(peak_x, peak_y, symbol='o', size=[5] * len(data['peak_list'].intensity),
                                      brush=(255, 255, 255, 0), pen=self._ring_pen,
                                      pxMode=False)

            QtGui.QApplication.processEvents()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)
    if len(sys.argv) == 2:
        geom_filename = sys.argv[1]
        rec_ip = '127.0.0.1'
        rec_port = 12321
    elif len(sys.argv) == 4:
        geom_filename = sys.argv[1]
        rec_ip = sys.argv[2]
        rec_port = int(sys.argv[3])
    else:
        print('Usage: onda_crystallography_hit_viewer_gui.py geometry_filename <listening ip> <listening port>')
        sys.exit()

    _ = MainFrame(geom_filename, rec_ip, rec_port)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()