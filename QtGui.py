import sys, os, random, time, csv
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

imgPath = os.getcwd() + '/scantest/vis_ref.png'

class OmPyGUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.scan_status = 'select'
        self.scan_points = ScanPoints(parent=self)
        self.working_dir = '/Users/michael/github_repos/FTIR/scantest2/data'
        self.image_path = os.path.join(self.working_dir, 'vis_ref.png')
        self.box_selectable = False
        self.current_scan_i = None
        self.initUI()
        self.update_UI()

    def initUI(self): 
        MAXUI_WIDTH = 1200
        self.container = QWidget(self)
        self.btn_toggle_scan = QPushButton('Scan', self)
        self.btn_toggle_scan.setEnabled(False)
        self.btn_toggle_scan.clicked.connect(self.toggle_scanning)

        self.btn_stop_scan = QPushButton('Stop Scanning', self)
        self.btn_stop_scan.setEnabled(False)
        self.btn_stop_scan.clicked.connect(self.stop_scanning)

        self.btn_select_dir = QPushButton('Set Directory', self)
        self.btn_select_dir.setEnabled(True)
        self.btn_select_dir.clicked.connect(self.select_dir)

        self.statusBar().showMessage('Ready')

        self.boxSelector = ScanBoxSelect(0, 0, parent = self) 
        self.spec_vis = SpectralVisualizer(parent = self)
        
        # Fix the size of of box selector
        self.boxSelector.setFixedSize(self.boxSelector.size())

        #self.spec_vis.setFixedHeight(self.boxSelector.size().height())
        #self.spec_vis.resize(self.boxSelector.size())

        selector_height = self.boxSelector.size().height()
        spec_aspect_ratio = self.spec_vis.aspect_ratio
        spec_width = spec_aspect_ratio * selector_height
        if spec_width + self.boxSelector.size().width() > MAXUI_WIDTH:
            spec_width = MAXUI_WIDTH - self.boxSelector.size().width()
            spec_height = spec_width / spec_aspect_ratio
            self.spec_vis.setFixedSize(spec_width, spec_height)
        else:
            self.spec_vis.setFixedSize(spec_aspect_ratio * selector_height, selector_height)

        spec_cont = DenseContainer()
        spec_cont_layout = QVBoxLayout()
        spec_cont_layout.addStretch(1)
        spec_cont_layout.addWidget(self.spec_vis)
        spec_cont_layout.addStretch(1)
        spec_cont_layout.setContentsMargins(0, 0, 0, 0)
        spec_cont.setLayout(spec_cont_layout)
        spec_cont.setFixedHeight(self.boxSelector.size().height())

        buttonRow = QHBoxLayout()
        buttonRow.addWidget(self.btn_select_dir)
        buttonRow.addWidget(self.btn_toggle_scan)
        buttonRow.addWidget(self.btn_stop_scan)

        display_row = QHBoxLayout()
        display_row.addWidget(self.boxSelector)
        #display_row.addWidget(self.spec_vis)
        display_row.addWidget(spec_cont)

        layout = QVBoxLayout()
        layout.addLayout(buttonRow)
        layout.addLayout(display_row)

        self.container.setLayout(layout) 


        self.setCentralWidget(self.container)
        self.show()

    def start_scanning(self): 
        self.scan_thread = QThread()
        self.scan_runner = ScanRunner(self.scan_points, self.working_dir)
        self.scan_runner.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_runner.run)

        self.scan_runner.begin_scan_pt.connect(self.begin_scanning_point)
        self.scan_runner.done_scan_pt.connect(self.done_scanning_point)
        self.scan_runner.finished.connect(self.finished_scanning)

        self.scan_thread.start()

        self.update_UI()

    def begin_scanning_point(self, i):
        self.current_scan_i = i
        self.update_UI()

    def done_scanning_point(self, i):
        self.scan_points.set_scanned(i)

    def toggle_scanning(self): 
        print('toggle scanning-----')
        print('Sender: {}'.format(self.sender().text()))
        print(self.scan_status)
        print('-----')
        if self.scan_status == 'ready':
            self.scan_status = 'scanning'
            self.start_scanning()

        elif self.scan_status == 'scanning':
            self.scan_status = 'paused'
            self.scan_runner.is_scanning = False
            #self.update_UI()

        elif self.scan_status == 'paused':
            self.scan_status = 'scanning'
            self.start_scanning()

    def update_UI(self):
        if self.scan_status == 'select':
            self.btn_toggle_scan.setEnabled(False) 
            self.btn_stop_scan.setEnabled(False)
            self.btn_toggle_scan.setText('Start Scan')
            if self.working_dir:
                self.statusBar().showMessage('Select region for scanning')
                self.box_selectable = True
            else:
                self.statusBar().showMessage('Select directory to store files')
                self.box_selectable = False
        elif self.scan_status == 'ready': 
            self.btn_toggle_scan.setEnabled(True) 
            self.btn_stop_scan.setEnabled(False) 
            self.btn_toggle_scan.setText('Start Scan')
            self.statusBar().showMessage('Ready for scanning')
            self.box_selectable = True
        elif self.scan_status == 'scanning':
            self.btn_toggle_scan.setEnabled(True)
            self.btn_stop_scan.setEnabled(True)
            self.btn_toggle_scan.setText('Pause')
            if self.current_scan_i:
                x, y = self.scan_points.xy[self.current_scan_i]
                self.statusBar().showMessage('Scanning ({}, {})'.format(x, y))
            else:
                self.statusBar().showMessage('Scanning...')
            self.box_selectable = False
        elif self.scan_status == 'paused':
            print('status paused')
            self.btn_toggle_scan.setEnabled(True)
            self.btn_stop_scan.setEnabled(True) 
            self.btn_toggle_scan.setText('Resume Scan')
            self.statusBar().showMessage('Scanning Paused')
            self.box_selectable = False
        elif self.scan_status == 'finished':
            print('status finished')
            self.btn_toggle_scan.setEnabled(False)
            self.btn_stop_scan.setEnabled(False) 
            self.statusBar().showMessage('Finished Scaning')
            self.box_selectable = False
        elif self.scan_status == 'stopping':
            self.btn_toggle_scan.setEnabled(False)
            self.btn_stop_scan.setEnabled(False) 
            self.statusBar().showMessage('Stopping Scan')
            self.box_selectable = False
            
    def stop_scanning(self):
        print('stop scanning-----')
        print(self.sender())
        if self.scan_runner.is_scanning:
            self.scan_runner.is_scanning = False
            self.scan_thread.exit()
            #self.scan_points.clear_points()
            self.scan_status = 'stopping'
        else:
            self.scan_status = 'select'
        self.update_UI()

    def finished_scanning(self):
        print('finished scan')
        if self.scan_status == 'stopping':
            self.scan_status = 'select'
            self.scan_points.clear_points()
        else: 
            if 0 in self.scan_points.status:
                self.scan_status = 'paused'
                self.scan_thread.exit()
            else:
                self.scan_status = 'finished'
                self.scan_thread.exit()

        self.update_UI()

    def select_dir(self):
        self.working_dir = QFileDialog.getExistingDirectory(self, 'Select working directory') 
        self.update_UI()


class ScanBoxSelect(QWidget):

    def __init__(self, x0, y0, a = 3, b = -3, parent = None ):
        super().__init__(parent)
        self.parent = parent
        
        self.a = a
        self.b = b
        self.x0 = x0
        self.y0 = y0

        self.xRes = 5

        self.selecting = False

        self.initUI()

    def initUI(self): 
        #Draw bg image
        self.setWindowTitle('Image test') 
        self.loadRefImg()
        self.boxSelect = Selector(self) 
        self.scanPointVis = PointVis(self.parent.scan_points, self)
        #self.show()

    def loadRefImg(self):
        self.refImg  = QLabel(self)
        pixmap = QPixmap(self.parent.image_path)
        self.refImg.setPixmap(pixmap)
        self.rImgW = pixmap.width()
        self.rImgH = pixmap.height()
        self.refImg.resize(self.rImgW, self.rImgH)
        self.resize(self.rImgW, self.rImgH)

    def mousePressEvent(self, event):
        if self.parent.box_selectable:
            self.parent.scan_points.clear_points()
            self.selecting = True
            self.curPos = event.pos()
            self.origin = event.pos()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.curPos = event.pos()
            self.parent.scan_points.set_points_to_scan(self.getPtSelected())
            self.update()

    def mouseReleaseEvent(self, event):
        if self.selecting:
            self.selecting = False
            self.parent.scan_points.set_points_to_scan(self.getPtSelected())
            if self.parent.scan_points.xy:
                self.parent.scan_status = 'ready'
            else:
                self.parent.scan_status = 'select' 
            self.parent.update_UI()
            self.update() 

    def getPtSelected(self):
        u0, v0 = self.origin.x(), self.origin.y()
        u1, v1 = self.curPos.x(), self.curPos.y()
        x0, y0 = self.uv_to_xy(u0, v0)
        x1, y1 = self.uv_to_xy(u1, v1)

        x0 = (x0 // self.xRes + 1) * self.xRes
        y0 = (y0 // self.xRes + 1) * self.xRes
        x1 = (x1 // self.xRes + 1) * self.xRes
        y1 = (y1 // self.xRes + 1) * self.xRes
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0

        xList = np.arange(x0, x1, self.xRes)
        yList = np.arange(y0, y1, self.xRes)

        return [(x, y) for y in yList for x in xList]

    def uv_to_xy(self, u, v):
        x = (u - self.rImgW/2) / self.a + self.x0
        y = (v - self.rImgH/2) / self.b + self.y0
        return x, y

    def xy_to_uv(self, x, y):
        u = (x - self.x0) * self.a + self.rImgW / 2
        v = (y - self.x0) * self.b + self.rImgH / 2
        return u, v


class Selector(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent = parent
        self.resize(parent.size())
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, e):
        q = QPainter(self)
        if self.parent.selecting:
            q.setPen(QColor(255, 0, 0))
            q.drawRect(
                    QRect(self.parent.origin, self.parent.curPos).normalized()
                    )


class PointVis(QWidget):

    def __init__(self, points, parent = None):
        super().__init__(parent)
        self.parent = parent
        self.points = points
        self.resize(parent.size())
        self.setAttribute(Qt.WA_TransparentForMouseEvents)


    def paintEvent(self, e):
        q = QPainter(self)
        ptXY = self.points.xy
        ptStat = self.points.status
        for xy, s in zip(ptXY, ptStat):
            uv = self.parent.xy_to_uv(*xy)
            q.setPen(Qt.NoPen)
            if s == 0:
                q.setBrush(QBrush(Qt.red))
            if s == -1:
                q.setBrush(QBrush(Qt.blue))
            if s == 1:
                q.setBrush(QBrush(Qt.green))
            #q.drawPoint(*uv)
            r = self.parent.xRes * 0.6
            q.drawEllipse(QPoint(*uv), r, r)


class ScanPoints(object):

    def __init__(self, xy = [], status = [], parent = None):
        self.parent = parent
        self.xy = xy
        self.status = status
        #self.points_updated()

    def clear_points(self):
        self.xy = []
        self.status = []
        self.points_updated()

    def set_points_to_scan(self, points):
        self.xy = points
        self.status = [0 for p in points]
        self.points_updated()

    def append_point(self, pt, s=0):
        self.xy.append(pt)
        self.status.append(s)
        self.points_updated()

    def set_status(self, i, s):
        self.status[i] = s
        self.points_updated()

    def set_scanned(self, i):
        self.set_status(i, 1)

    def set_scanning(self, i):
        self.set_status(i, -1)

    def set_to_scan(self, i):
        self.set_status(i, 0)

    def points_updated(self):
        self.max_idx = len(self.xy)
        self.parent.update_UI()
        self.parent.update()


class ScanRunner(QObject):

    finished = pyqtSignal()
    begin_scan_pt = pyqtSignal(int)
    done_scan_pt = pyqtSignal(int)

    def __init__(self, points, dir):
        super().__init__()
        self.points = points
        self.dir = dir
        self.is_scanning = True

    def run(self):
        sample_fname = os.path.join(self.dir, 'sample.csv')
        sample_arr = np.genfromtxt(sample_fname, delimiter = ',')
        sample_freq = sample_arr[:,0]
        scan_csv_fname = os.path.join(self.dir, 'scan_points.csv')
        while self.is_scanning:
            if 0 in self.points.status:
                i = self.points.status.index(0)
                self.points.set_scanning(i)
                xy = self.points.xy[i]
                self.begin_scan_pt.emit(i)

                fname = os.path.join(self.dir, str(i) + '.csv')
                mock_scan(xy, fname, sample_arr)
                line = [xy[0], xy[1], time.time()]
                with open(scan_csv_fname, 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow(line)

                self.done_scan_pt.emit(i)
            else:
                break
        self.finished.emit()


class PointVis(QWidget):

    def __init__(self, points, parent = None):
        super().__init__(parent)
        self.parent = parent
        self.points = points
        self.resize(parent.size())
        self.setAttribute(Qt.WA_TransparentForMouseEvents)


    def paintEvent(self, e):
        q = QPainter(self)
        ptXY = self.points.xy
        ptStat = self.points.status
        for xy, s in zip(ptXY, ptStat):
            uv = self.parent.xy_to_uv(*xy)
            q.setPen(Qt.NoPen)
            if s == 0:
                q.setBrush(QBrush(Qt.red))
            if s == -1:
                q.setBrush(QBrush(Qt.blue))
            if s == 1:
                q.setBrush(QBrush(Qt.green))
            #q.drawPoint(*uv)
            r = self.parent.xRes * 0.6
            q.drawEllipse(QPoint(*uv), r, r)


class SpectralVisualizer(QWidget):

    def __init__(self, parent = None):
        #Assuming that points are spaced isotropically (x-, y- direction) in a rect. lattice
        super().__init__(parent)
        self.parent = parent
        self.working_dir = self.parent.working_dir
        scanned_csv_fname = os.path.join(self.working_dir, 'scan_points.csv')
        scanned_points = np.loadtxt(
                open(scanned_csv_fname, 'rb'), delimiter=',', skiprows = 1
                )
        self.max_x, self.max_y, _ = scanned_points.max(0)
        self.min_x, self.min_y, _ = scanned_points.min(0)
        self.data_w = self.max_x - self.min_x
        self.data_h = self.max_y - self.min_y
        self.aspect_ratio = self.data_w / self.data_h
        self.initUI()

    def initUI(self): 
        pts_fname = os.path.join(self.working_dir, 'points_scanned.csv')
        

    def paintEvent(self, e):
        q = QPainter(self)
        q.setBrush(QBrush(Qt.red))
        q.drawRect(self.rect())
        frame_w, frame_h = self.size().width(), self.size().height()


class DenseContainer(QWidget):
    
    def paintEvent(self, e):
        q = QPainter(self)
        q.setBrush(QBrush(Qt.Dense6Pattern))
        q.drawRect(self.rect())
        

def mock_scan(xy, fname, sample_arr):
    #Make fake data
    freq = sample_arr[:,0]
    sample_arr[:,1] = (np.random.rand(sample_arr.shape[0]))
    time.sleep(.1)

    np.savetxt(fname, sample_arr, delimiter = ',')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = OmPyGUI()
    sys.exit(app.exec_())
