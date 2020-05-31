# coding: utf-8
#-*- coding:utf-8 -*-
import sys
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import uic
from PyQt5 import QtCore as core
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMessageBox

from pymodbus.client.sync import ModbusSerialClient
from pymodbus.client.sync import ModbusTcpClient

import time
import datetime
import threading
from time import gmtime, strftime
import os
import cx_Oracle
# import fix_qt_import_error


class Form(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = uic.loadUi("sample_mbCollector_seoulSemicon.ui", self)
        self.ui.show()
        self.ui.label.setText("Modbus/TCP")
        self.ui.lineEdit.setDisabled(False)
        self.ui.lineEdit_2.setDisabled(True)
        self.ui.comboBox_2.setDisabled(True)
        self.ui.pushButton_2.setDisabled(True)
        self.slot_1()
        # fix_qt_import_error._append_run_path()

    @pyqtSlot()
    def slot_1(self):
        modbusMode = self.ui.comboBox.currentText()
        ip_address = self.ui.lineEdit.text()
        com_port = self.ui.lineEdit_2.text()
        sampling_time = self.ui.lineEdit_3.text()
        modbusRegisterNum = self.ui.lineEdit_4.text()
        modbusStartAddress = self.ui.lineEdit_5.text()
        baudRate = self.ui.comboBox_2.currentText()

        global stop
        stop = False
        t = MyThread(com_port, sampling_time, modbusRegisterNum, modbusStartAddress, modbusMode, ip_address, baudRate)

        try:
            t.daemon = True             # Daemon True is necessary
            t.start()
        except:
            self.ui.label.setText("Thread Fail")
        else:
            self.ui.label.setText("Trying to Connect")
            self.ui.pushButton_3.setDisabled(True)
            self.ui.pushButton_2.setDisabled(False)

    @pyqtSlot()
    def slot_2(self):
        global stop
        stop = True
        self.ui.label.setText("Disconnected")
        self.ui.pushButton_3.setDisabled(False)
        self.ui.pushButton_2.setDisabled(True)

    @pyqtSlot()
    def slot_3(self):
        self.ui.label.setText("세번째 버튼")

    @pyqtSlot()
    def slot_4(self):
        if self.ui.comboBox.currentIndex() == 0 :
            self.ui.label.setText("Modbus/TCP")
            self.ui.lineEdit.setDisabled(False)
            self.ui.lineEdit_2.setDisabled(True)
            self.ui.comboBox_2.setDisabled(True)

        elif self.ui.comboBox.currentIndex() == 1 :
            self.ui.label.setText("Modbus/RTU")
            self.ui.lineEdit.setDisabled(True)
            self.ui.lineEdit_2.setDisabled(False)
            self.ui.comboBox_2.setDisabled(False)

    @pyqtSlot()
    def slot_5(self):
        self.ui.label_21.setText("Trying to connect")
        host = self.ui.lineEdit_6.text()
        port = int(self.ui.lineEdit_7.text())
        service = self.ui.lineEdit_8.text()
        user = self.ui.lineEdit_9.text()
        password = self.ui.lineEdit_10.text()
        sqlQuery = self.ui.lineEdit_11.text()

        try:
            db, conn, oraError = dbOracle(host, port, service, user, password)
        except:
            print("error")
        else:
            self.ui.label_21.setText("Successed!")
            db.execute(sqlQuery)
            for record in db:
                print(record)
                self.ui.listWidget_2.addItem(str(record))
            db.close()
            conn.close()

class MyThread(threading.Thread):
    def __init__(self, com_port, Sampling_time, modbusRegisterNum, modbusStartAddress, modbusMode, ip_address, baudRate):
        threading.Thread.__init__(self)
        self.modbusMode = modbusMode
        self.com_port = com_port
        self.sampling_time = Sampling_time
        self.modbusRegisterNum = modbusRegisterNum
        self.modbusStartAddress = modbusStartAddress
        self.ip_address = ip_address
        self.baudRate = baudRate

    def run(self):
        SERVER_PORT = 502
        COM_PORT = self.com_port
        BAUD_RATE = int(self.baudRate)

        if self.modbusMode == "Modbus/RTU" :
            connection = ModbusSerialClient(method = "rtu", port = COM_PORT, stopbits = 1, bytesize = 8, parity = 'N', baudrate = BAUD_RATE)
        elif self.modbusMode == "Modbus/TCP" :
            connection = ModbusTcpClient(host = self.ip_address, port = 502)
        else :
            print("ELSE!")

        modbusNum = int(self.modbusRegisterNum)
        modbusStart = int(self.modbusStartAddress)
        register_buffer = []

        # 저장할 디렉토리 확인 후 없으면 생성
        folderDir = './log'
        makeDirectory(folderDir)
        progressBarNum = 0

        tempMaxThreshold = [w.ui.lineEdit_12.text(), w.ui.lineEdit_17.text(), w.ui.lineEdit_21.text()]
        tempMinThreshold = [w.ui.lineEdit_15.text(), w.ui.lineEdit_16.text(), w.ui.lineEdit_20.text()]
        humidityMaxThreshold = [w.ui.lineEdit_13.text(), w.ui.lineEdit_19.text(), w.ui.lineEdit_23.text()]
        humidityMinThreshold = [w.ui.lineEdit_14.text(), w.ui.lineEdit_18.text(), w.ui.lineEdit_22.text()]

        while True:
            if not connection.connect():
                errString = self.modbusMode + " Connection Error, Check Your Input Information"
                print(errString)
                print(self.ip_address)
                w.ui.label.setText(errString)
                break
            else:
                try:
                    if self.modbusMode == "Modbus/RTU" :
                        input_buffer_regs = connection.read_holding_registers(address=modbusStart, count=modbusNum, unit=0x01)
                    elif self.modbusMode == "Modbus/TCP" :
                        input_buffer_regs = connection.read_input_registers(modbusStart, modbusNum)
                except:
                    print("Error occur while communication.")
                else:
                    w.ui.label.setText("Trying to Connect")
                    if register_buffer == []:
                        register_buffer = input_buffer_regs.registers
                    else :
                        w.ui.label.setText("Connected")
                        listWidgetClear(5)

                        now = datetime.datetime.now()
                        timeSentence = "Updated Time: " +str(datetime.time(now.hour, now.minute, now.second))
                        w.ui.label_11.setText(timeSentence)

                        host = w.ui.lineEdit_6.text()
                        port = int(w.ui.lineEdit_7.text())
                        service = w.ui.lineEdit_8.text()
                        user = w.ui.lineEdit_9.text()
                        password = w.ui.lineEdit_10.text()

                        for i in range(3) :
                            if register_buffer[i*2]/100 < int(humidityMinThreshold[i]) or \
                                register_buffer[i*2]/100 > int(humidityMaxThreshold[i]) or \
                                register_buffer[i*2+1]/20 < int(tempMinThreshold[i]) or \
                                register_buffer[i*2+1]/20 > int(tempMaxThreshold[i]) :
                                OKNG_DIV = "'N'"
                                connection.write_register(i,1)
                                if register_buffer[i*2] >= 32767 or register_buffer[i*2+1] >= 32767 :
                                    MEMO ="'Wireless or Sensor Connection problem'"
                                else :
                                    MEMO = "'Normal'"

                            else :
                                connection.write_register(i,0)
                                OKNG_DIV = "'Y'"
                                MEMO = "'Normal'"

                            try:
                                db, conn, oraError = dbOracle(host, port, service, user, password)
                            except:
                                print("failed")
                            else:
                                tempNodeNum = "'TURCK_TEMP_0" + str(i+1) +"'"
                                today = datetime.datetime.today()
                                currentTime = "'" + str(today).split('.')[0] + "'"
                                currentTimeTodate = 'TO_DATE(' + currentTime + ", 'YYYY-MM-DD HH24:MI:SS')"
                                sqlQueryFront = 'INSERT INTO ' + 'TB_CHECK_ENVIRON_IOT(EQUIP_CODE, TEMP, WET, TEMP_MAX, TEMP_MIN, WET_MAX, WET_MIN, SAVE_DTTM, OKNG_DIV, MEMO) VALUES ('
                                sqlQueryLast = (tempNodeNum + ', ' + str(register_buffer[i*2+1]/20) +', '
                                                + str(register_buffer[i*2]/100) + ', '
                                                + tempMaxThreshold[i] +', '
                                                + tempMinThreshold[i] +', '
                                                + humidityMaxThreshold[i] + ', '
                                                + humidityMinThreshold[i] + ', '
                                                + currentTimeTodate + ', '
                                                + OKNG_DIV + ', '
                                                + MEMO + ')')
                                sqlQuery = sqlQueryFront + sqlQueryLast
                                print(sqlQuery)

                                db.execute(sqlQuery)
                                conn.commit()
                                db.close()
                                conn.close()

                            nodeName = "Node" + str(i+1)
                            w.ui.listWidget.addItem(nodeName)
                            listExpression = "상대습도(%RH): " + str(register_buffer[i*2]/100) + ", " + "온도(˚C): " + str(register_buffer[i*2+1]/20)
                            w.ui.listWidget.addItem(listExpression)
                            w.ui.listWidget.addItem("")

                        if register_buffer != list(input_buffer_regs.registers) :
                            register_buffer = input_buffer_regs.registers
                            dataLogging(folderDir, register_buffer)

            time_interval = int(self.sampling_time)/1000             # sleep 'n'second before next polling
            time.sleep(time_interval)

            if stop == True:
                print("Communication Disconnected!")
                connection.close()
                break

def dbOracle(host, port, service, user, password):
    try:
        dsn = cx_Oracle.makedsn(host,port,service)
        conn = cx_Oracle.connect(user,password,dsn)
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print("FAILED with error:", error.message)
        db ='Error'
        oraError = error.message
        w.ui.listWidget_2.addItem(oraError)
        w.ui.label_21.setText("Failed!")
    else:
        db = conn.cursor()
        oraError = ''
    return db, conn, oraError

def makeDirectory(folderDir):
    if not os.path.isdir(folderDir):
        os.mkdir(folderDir)

def dataLogging(folderDir, register_buffer):
    logging_file_name = folderDir + '/' + str(datetime.datetime.today().strftime("%Y%m%d")) +'.txt'
    f = open(logging_file_name, mode='a', encoding='utf-8')
    str_read_list = str(register_buffer)[1:-1]
    now = datetime.datetime.now()
    cur_time = datetime.time(now.hour, now.minute, now.second)
    RF_logging = str(cur_time) + ', ' + str_read_list +'\n'
    f.write(RF_logging)
    f.close()

def listWidgetClear(clearNumber):
    if w.ui.listWidget.count() > clearNumber:
        w.ui.listWidget.clear()

def boolean_def(word):
    data = []
    b = 1
    for i in range(0, 16):
        if word & (b<<i) == 0:
            data.append("False")
        else:
            data.append("True")
    return data

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = Form()
    sys.exit(app.exec_())
