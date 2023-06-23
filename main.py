#!/bin/python3

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QAction, QTableWidget, QTableView, QTableWidgetItem, QHBoxLayout, QVBoxLayout, QGridLayout, QRadioButton, QLineEdit, QAbstractItemView
from PyQt5.QtChart import QHorizontalStackedBarSeries, QHorizontalBarSeries, QChart, QChartView, QValueAxis, QBarCategoryAxis, QBarSet, QBarSeries
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, QAbstractTableModel, QVariant
from PyQt5.Qt import Qt, QColor
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

    def removwRows(self, position, rows=1, index=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), position, position + rows - 1)
        for _ in range(rows):
            del self.arraydata[position]
        self.endRemoveRows()

    def addRow(self):
        self.insertRows(self.rowCount(), 1)

class TableView(QTableWidget):
    def __init__(self, data, *args):
        QTableWidget.__init__(self, *args)
        self.setWindowTitle("Real Time Scheduler")
        self.data = data
        self.setData()
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def setData(self): 
        horHeaders = []
        for n, key in enumerate(sorted(self.data.keys())):
            horHeaders.append(key)
            for m, item in enumerate(self.data[key]):
                newitem = QTableWidgetItem(item)
                self.setItem(m, n, newitem)
        self.setHorizontalHeaderLabels(horHeaders)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Real Time Scheduler')
        self.setGeometry(0, 0, 1920, 1080)

        colorList = [ 'green', 'red', 'blue', 'yellow' ]

        data = [['A','10','10','30'],
                ['B','20','20','30'],
                ['C','30','30','40']]

        header = ['PID','Pi','Ci','Di']

        layout = QGridLayout()

        h1lay = QHBoxLayout()

        radiobutton = QRadioButton("EDF - Earliest Deadline First")
        radiobutton.setChecked(True)
        radiobutton.scheduler = "EDF"
        radiobutton.toggled.connect(self.onClicked)
        h1lay.addWidget(radiobutton)

        radiobutton = QRadioButton("RM - Rate Monotonic")
        radiobutton.scheduler = "RM"
        radiobutton.toggled.connect(self.onClicked)
        h1lay.addWidget(radiobutton)

        radiobutton = QRadioButton("DM - Deadline Monotonic")
        radiobutton.scheduler = "DM"
        radiobutton.toggled.connect(self.onClicked)
        h1lay.addWidget(radiobutton)

        radioButtonWidget = QWidget()
        radioButtonWidget.setLayout(h1lay)

        layout.addWidget(radioButtonWidget, 2, 0)

        tableLabel = QLabel("Processes table")
        layout.addWidget(tableLabel, 4, 0)

        self.model = TableModel(data, header)
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setModel(self.model)
        self.table.show()
        layout.addWidget(self.table, 5, 0)

        h2lay = QVBoxLayout()

        label2 = QLabel("PID - Process ID")
        h2lay.addWidget(label2)

        text2 = QLineEdit()
        h2lay.addWidget(text2)

        label3 = QLabel("Ci - Computing time")
        h2lay.addWidget(label3)

        text3 = QLineEdit()
        h2lay.addWidget(text3)

        label4 = QLabel("Di Deadline time")
        h2lay.addWidget(label4)

        text4 = QLineEdit()
        h2lay.addWidget(text4)

        addButton = QPushButton("Add process")
        addButton.clicked.connect(self.onClickedAdd)
        addButton.setFixedHeight(40)
        h2lay.addWidget(addButton)

        deleteButton = QPushButton("Delete process")
        deleteButton.clicked.connect(self.onClickedDelete)
        deleteButton.setFixedHeight(40)
        h2lay.addWidget(deleteButton)

        addWidget = QWidget()
        addWidget.setFixedHeight(280)
        addWidget.setFixedWidth(200)
        addWidget.setLayout(h2lay)
        layout.addWidget(addWidget, 3, 0)

        runButton = QPushButton("Run")    
        runButton.clicked.connect(self.onClickedRun)
        runButton.setFixedHeight(40)

        clearButton = QPushButton("Clear")    
        clearButton.clicked.connect(self.onClickedClear)
        clearButton.setFixedHeight(40)

        barSets = []
        processColor = []
        colorListIndex = 0

        series = QHorizontalStackedBarSeries()

        for i in range(0, self.model.rowCount(self)):
            index = self.model.index(i, 0)
            pid = self.model.data(index).value() 
            index = self.model.index(i, 1)
            pi = self.model.data(index).value() 
            newBarSet = QBarSet(pid)
            newBarSet.setColor(QColor(colorList[colorListIndex]))
            processColor.append((pid, colorList[colorListIndex]))
            colorListIndex += 1
            newBarSet.append(int(pi))
            barSets.append(newBarSet)
            series.append(newBarSet)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle('Scheduler')
        chart.setAnimationOptions(QChart.SeriesAnimations)

        months = ('Tasks')

        axisX = QValueAxis()
        axisX.setRange(0, 16)

        axisY = QBarCategoryAxis()
        axisY.append(months)

        chart.addAxis(axisX, Qt.AlignBottom)
        chart.addAxis(axisY, Qt.AlignLeft)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        self.chartView = QChartView(chart)
        self.chartView.setVisible(False)

        layout.addWidget(self.chartView, 6, 0)
        layout.addWidget(runButton, 7, 0)
        layout.addWidget(clearButton, 8, 0)

        mainWidget = QWidget()
        mainWidget.setLayout(layout)

        self.setCentralWidget(mainWidget)

    def onClickedRun(self):
        self.chartView.setVisible(True)

    def onClickedClear(self):
        self.chartView.setVisible(False)

    def onClicked(self):
        self.radioButton = self.sender()

    def onClickedAdd(self):
        self.model.addRow()

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
 
