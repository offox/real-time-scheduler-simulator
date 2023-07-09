#!/bin/python3

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QTableWidget, QTableView, QTableWidgetItem, QHBoxLayout, QVBoxLayout, QGridLayout, QRadioButton, QLineEdit, QAbstractItemView
from PyQt5.QtChart import QHorizontalStackedBarSeries, QHorizontalBarSeries, QChart, QChartView, QValueAxis, QBarCategoryAxis, QBarSet, QBarSeries
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, QAbstractTableModel, QVariant
from PyQt5.Qt import Qt, QBrush, QColor, QPainter, QPainterPath, QPen, QPointF, QStandardItem
import PyQt5.QtCore as QtCore
import sys
import random
import signal

class TableModel(QAbstractTableModel):
    def __init__(self, datain, headerdata, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = datain
        self.headerdata = headerdata

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if len(self.arraydata) > 0: 
            return len(self.arraydata[0]) 
        return 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.arraydata[index.row()][index.column()])

    def setData(self, index, value, role):
        pass         # not sure what to put here

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.headerdata[col])
        return QVariant()

    def sort(self, Ncol, order):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))       
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        self.emit(SIGNAL("layoutChanged()"))

    def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), position, position + rows - 1)
        for _ in range(rows):
            del self.arraydata[position]
        self.endRemoveRows()

    def addRow(self, row):
        self.arraydata.append(row)
        self.layoutChanged.emit()

class TableView(QTableWidget):
    def __init__(self, data, *args):
        QTableWidget.__init__(self, *args)
        self.setWindowTitle("Real Time Scheduler")
        self.data = data
        
class ChartView(QChartView):
    _lines = None

    @property
    def lines(self):
        return self._lines

    @lines.setter
    def lines(self, lines):
        self._lines = lines
        self.update()

    def drawForeground(self, painter, rect):
        if self.lines is None:
            return

        painter.save()

        pen = QPen(QColor("black"))
        pen.setWidth(3)
        painter.setPen(pen)

        r = self.chart().plotArea()

        for label, x in self.lines:
            p = self.chart().mapToPosition(QPointF(x, 0))

            p1 = QPointF(p.x(), r.top() + r.top() * 0.6)
            p2 = QPointF(p.x(), r.bottom())
            painter.drawLine(p1, p2)

            path = QPainterPath();
            path.moveTo(p.x(), r.top() + r.top() * 0.3)
            path.lineTo(p.x() - 5, r.top() + r.top() * 0.6)
            path.lineTo(p.x() + 5, r.top() + r.top() * 0.6)

            painter.fillPath(path, QBrush(QColor ("black")));

            painter.drawText(int(p.x() - len(label) * 4), int(r.top() + r.top() * 0.3), label)

        painter.restore()


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Real Time Scheduler')
        self.setGeometry(0, 0, 1920, 1080)

        self.colorList = [ 'green', 'red', 'blue', 'yellow', 'orange', 'black' ]

        data = [['A','10','20','20'],
                ['B','25','50','25'],
                ['C','30','60','10']]

        header = ['PID','Ci','Di', 'Pi']

        layout = QGridLayout()

        tableLabel = QLabel("Processes table")
        layout.addWidget(tableLabel, 4, 0)

        self.model = TableModel(data, header)
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setModel(self.model)
        self.table.show()
        layout.addWidget(self.table, 5, 0)

        hlay = QHBoxLayout()

        label1 = QLabel("PID - Process ID")
        hlay.addWidget(label1)

        self.pidtext = QLineEdit()
        hlay.addWidget(self.pidtext)

        label2 = QLabel("Pi - Priority")
        hlay.addWidget(label2)

        self.pitext = QLineEdit()
        hlay.addWidget(self.pitext)

        label3 = QLabel("Ci - Computing time")
        hlay.addWidget(label3)

        self.citext = QLineEdit()
        hlay.addWidget(self.citext)

        label4 = QLabel("Di - Deadline time")
        hlay.addWidget(label4)

        self.ditext = QLineEdit()
        hlay.addWidget(self.ditext)

        addButton = QPushButton("Add process")
        addButton.clicked.connect(self.onClickedAdd)
        addButton.setFixedHeight(40)
        hlay.addWidget(addButton)

        deleteButton = QPushButton("Delete process")
        deleteButton.clicked.connect(self.onClickedDelete)
        deleteButton.setFixedHeight(40)
        hlay.addWidget(deleteButton)

        addWidget = QWidget()
        addWidget.setLayout(hlay)
        layout.addWidget(addWidget, 3, 0)

        runButton = QPushButton("Run")    
        runButton.clicked.connect(self.onClickedRun)
        runButton.setFixedHeight(40)

        clearButton = QPushButton("Clear")    
        clearButton.clicked.connect(self.onClickedClear)
        clearButton.setFixedHeight(40)

        self.processColor = []
        self.colorListIndex = 0

        self.chart = QChart()
        self.chart.setTitle('Scheduler')
        self.chart.setAnimationOptions(QChart.SeriesAnimations)

        months = ('Tasks EDF', 'Task RM', 'Task DM')

        self.axisX = QValueAxis()

        axisY = QBarCategoryAxis()
        axisY.append(months)

        self.chart.addAxis(self.axisX, Qt.AlignBottom)
        self.chart.addAxis(axisY, Qt.AlignLeft)

        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self.chartView = ChartView(self.chart)
        self.chartView.setRenderHint(QPainter.Antialiasing)

        layout.addWidget(self.chartView, 6, 0)
        layout.addWidget(runButton, 7, 0)
        layout.addWidget(clearButton, 8, 0)

        mainWidget = QWidget()
        mainWidget.setLayout(layout)
        
        self.setCentralWidget(mainWidget)

    def getVerticalLines(self, indexValue):
        self.pidAndTime = []
        self.verticalLines = []

        # List all PID and times
        for i in range(0, self.model.rowCount(self)):
            self.pidAndTime.append((self.model.data(self.model.index(i, 0)).value(), int(self.model.data(self.model.index(i, indexValue)).value())))

        # Create all lines to each PID
        for i in range(0, self.model.rowCount(self)):
            count = 1    
            while True:
                if (self.pidAndTime[i][1] * count) > (self.pidAndTime[self.model.rowCount(self) - 1][1] + 10):
                    break

                self.verticalLines.append((self.pidAndTime[i][0], (self.pidAndTime[i][1] * count)))
                count += 1

        # Concate each line
        removeVerticalLines = []
        for i in range(0, len(self.verticalLines) - 1):
            for j in range(i+1, len(self.verticalLines)): 
                if self.verticalLines[i][1] == self.verticalLines[j][1]:
                    self.verticalLines[i] = (self.verticalLines[i][0] + ',' + self.verticalLines[j][0], self.verticalLines[i][1])
                    if not j in removeVerticalLines:
                        removeVerticalLines.append(j);

        print(removeVerticalLines)
        for i in range(0, len(removeVerticalLines)):
            del self.verticalLines[removeVerticalLines[i]] 
                    
        return self.verticalLines

    def EDF(self):
        pidAndCi = []
        pidAndCiTemp = []
        barSets = []

        self.colorListIndex = 0 

        for i in range(0, self.model.rowCount(self)):
            index = self.model.index(i, 0)
            pid = self.model.data(index).value() 
            index = self.model.index(i, 2)
            ci = self.model.data(index).value() 
            pidAndCi.append((pid, ci)) 

        stopPoint = 0

        while(True):
            for i in range(0, len(pidAndCi)):
                newBarSet = QBarSet(pidAndCi[i][0])
                newBarSet.setColor(QColor(self.colorList[self.colorListIndex]))
                self.processColor.append((pid, self.colorList[self.colorListIndex]))
                self.colorListIndex += 1
                newBarSet.append(int(pidAndCi[i][1]))
                barSets.append(newBarSet)
            break

        return barSets

    def RM(self):
        pidAndCi = []
        pidAndCiTemp = []
        barSets = []

        self.colorListIndex = 0 

        for i in range(0, self.model.rowCount(self)):
            index = self.model.index(i, 0)
            pid = self.model.data(index).value() 
            index = self.model.index(i, 1)
            ci = self.model.data(index).value() 
            pidAndCi.append((pid, ci)) 

        stopPoint = 0

        while(True):
            for i in range(0, len(pidAndCi)):
                newBarSet = QBarSet(pidAndCi[i][0])
                newBarSet.setColor(QColor(self.colorList[self.colorListIndex]))
                self.processColor.append((pid, self.colorList[self.colorListIndex]))
                self.colorListIndex += 1
                newBarSet.append(int(pidAndCi[i][1]))
                barSets.append(newBarSet)
            break

        return barSets

    def DM(self):
        pass

    def onClickedRun(self):
        endscale = 50
        self.processColor.clear()

        self.chart.removeAllSeries()

        self.series = []

        for i in range(0, 3):
            self.series.append(QHorizontalStackedBarSeries())

        # Switch
        vl = self.getVerticalLines(1)
        self.chartView.lines = vl

        self.series[0].append(self.EDF())
        self.series[1].append(self.RM())
        self.series[2].append(self.RM())

        self.axisX.setRange(0, endscale)
        self.chart.addSeries(self.series[0])
        self.chart.addSeries(self.series[1])
        self.chart.addSeries(self.series[2])

        self.chartView.setVisible(True)

    def onClickedClear(self):
        self.chartView.setVisible(False)

    def onClicked(self):
        self.radioButton = self.sender()

    def onClickedAdd(self):
        self.model.addRow([self.pidtext.text(), self.pitext.text(), self.citext.text(), self.ditext.text()])

    def onClickedDelete(self):
        indexes = self.table.selectionModel().selectedRows() 
        for index in sorted(indexes):
            self.model.removeRows(index.row()) 

if __name__=="__main__":
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
 
