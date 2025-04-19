import sys
import random
import time
from PyQt5 import QtWidgets, QtCore, QtGui
import paho.mqtt.client as mqtt
import threading
import sqlite3
from styles.styles import button_style, label_style, log_display_style

# MQTT Broker 设置
broker = "172.6.0.240"
port = 1883
topic_sensor = "sensor/data"
topic_control = "control/movement"

# 数据库文件
db_file = 'robot_data.db'

class UpperComputer(QtWidgets.QWidget):
    update_sensor_labels_signal = QtCore.pyqtSignal(str, str, str)
    update_log_display_signal = QtCore.pyqtSignal(str)

    def __init__(self, offline_mode=False):
        super().__init__()
        self.offline_mode = offline_mode
        self.client = None  # 初始化 client 属性
        self.control_client = None  # 初始化 control_client 属性
        self.initUI()
        if not self.offline_mode:
            self.initMQTT()
            self.subscribe_control_signals()
        self.initDatabase()
        
        # 启动传感器数据发布线程
        self.sensor_thread = threading.Thread(target=self.publish_sensor_data)
        self.sensor_thread.daemon = True
        self.sensor_thread.start()

        # 连接信号和槽
        self.update_sensor_labels_signal.connect(self.update_sensor_labels)
        self.update_log_display_signal.connect(self.update_log_display)

    # 初始化界面
    def initUI(self):
        self.setWindowTitle('MQTT 上位机控制')
        self.setGeometry(100, 100, 1600, 900) # 设置窗口大小
        self.setStyleSheet("QWidget { background-color: #f0f0f0; }")  # 设置背景颜色
        # 使用布局管理器
        layout = QtWidgets.QVBoxLayout(self)

        # 选项卡
        self.tabs = QtWidgets.QTabWidget()
        self.control_tab = QtWidgets.QWidget()
        self.log_tab = QtWidgets.QWidget()

        self.tabs.addTab(self.control_tab, "控制")
        self.tabs.addTab(self.log_tab, "日志")

        # 控制选项卡布局
        control_layout = QtWidgets.QVBoxLayout(self.control_tab)

        # 显示传感器数据的标签
        self.temp_label = QtWidgets.QLabel('温度: --')
        self.pressure_label = QtWidgets.QLabel('气压: --')
        self.depth_label = QtWidgets.QLabel('深度: --')

        self.temp_label.setStyleSheet(label_style)
        self.pressure_label.setStyleSheet(label_style)
        self.depth_label.setStyleSheet(label_style)

        control_layout.addWidget(self.temp_label)
        control_layout.addWidget(self.pressure_label)
        control_layout.addWidget(self.depth_label)

        # 控制按钮
        self.forward_button = QtWidgets.QPushButton('W')
        self.backward_button = QtWidgets.QPushButton('S')
        self.left_button = QtWidgets.QPushButton('A')
        self.right_button = QtWidgets.QPushButton('D')

        self.forward_button.setStyleSheet(button_style)
        self.backward_button.setStyleSheet(button_style)
        self.left_button.setStyleSheet(button_style)
        self.right_button.setStyleSheet(button_style)

        # 使用 QGridLayout 布局按钮
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.addWidget(self.forward_button, 0, 1)
        grid_layout.addWidget(self.left_button, 1, 0)
        grid_layout.addWidget(self.backward_button, 1, 1)
        grid_layout.addWidget(self.right_button, 1, 2)

        control_layout.addLayout(grid_layout)

        # 按钮事件绑定
        self.forward_button.clicked.connect(lambda: self.send_control_signal("forward"))
        self.backward_button.clicked.connect(lambda: self.send_control_signal("backward"))
        self.left_button.clicked.connect(lambda: self.send_control_signal("left"))
        self.right_button.clicked.connect(lambda: self.send_control_signal("right"))

        # 日志显示框
        self.log_display = QtWidgets.QTextEdit(self)
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet(log_display_style)
        control_layout.addWidget(self.log_display)

        # 提交状态按钮
        self.submit_status_button = QtWidgets.QPushButton('提交状态')
        self.submit_status_button.setStyleSheet(button_style)
        self.submit_status_button.clicked.connect(self.submit_status)
        control_layout.addWidget(self.submit_status_button)

        # 日志选项卡布局
        log_layout = QtWidgets.QVBoxLayout(self.log_tab)

        # 数据库日志显示框
        self.db_log_display = QtWidgets.QTextEdit(self)
        self.db_log_display.setReadOnly(True)
        self.db_log_display.setStyleSheet(log_display_style)
        log_layout.addWidget(self.db_log_display)

        # 刷新日志按钮
        self.refresh_log_button = QtWidgets.QPushButton('刷新日志')
        self.refresh_log_button.setStyleSheet(button_style)
        self.refresh_log_button.clicked.connect(self.refresh_log)
        log_layout.addWidget(self.refresh_log_button)

        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_W:
            self.forward_button.click()
        elif event.key() == QtCore.Qt.Key_S:
            self.backward_button.click()
        elif event.key() == QtCore.Qt.Key_A:
            self.left_button.click()
        elif event.key() == QtCore.Qt.Key_D:
            self.right_button.click()

    # MQTT初始化
    def initMQTT(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.loop_start()

    # MQTT连接成功
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        self.client.subscribe(topic_sensor)

    # MQTT接收到消息
    def on_message(self, client, userdata, msg):
        data = msg.payload.decode()
        print(f"Received message: {data} on topic {msg.topic}")

        if msg.topic == topic_sensor:
            temp, pressure, depth = self.parse_sensor_data(data)
            self.update_sensor_labels_signal.emit(temp, pressure, depth)
            self.log_data(temp, pressure, depth)

    # 解析传感器数据
    def parse_sensor_data(self, data):
        parts = data.split(', ')
        temp = parts[0].split(': ')[1]
        pressure = parts[1].split(': ')[1]
        depth = parts[2].split(': ')[1]
        return temp, pressure, depth

    # 更新界面上的传感器数据
    @QtCore.pyqtSlot(str, str, str)
    def update_sensor_labels(self, temp, pressure, depth):
        self.temp_label.setText(f"温度: {temp} °C")
        self.pressure_label.setText(f"气压: {pressure} kPa")
        self.depth_label.setText(f"深度: {depth} m")

    # 发送控制信号
    def send_control_signal(self, direction):
        if not self.offline_mode:  # 检查是否为离线模式
            if hasattr(self, 'client') and self.client:  # 确保 client 已初始化
                self.client.publish(topic_control, direction)
                print(f"Sent control signal: {direction}")
                self.log_control(direction)
            else:
                print("MQTT client is not initialized.")
        else:
            print("System is in offline mode, cannot send MQTT control signals.")
            self.log_control(direction)

    # 初始化数据库
    # dwafasfwafhuwaifhwaif
    def initDatabase(self):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        # 创建日志表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                temperature REAL,
                pressure REAL,
                depth REAL,
                timestamp TEXT
            )
        ''')
        # 创建状态表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT,
                timestamp TEXT
            )
        ''')
        self.conn.commit()

    # 记录传感器数据到数据库并更新日志显示
    def log_data(self, temp, pressure, depth):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO log (action, temperature, pressure, depth, timestamp) VALUES (?, ?, ?, ?, ?)
        ''', ("Sensor Data", temp, pressure, depth, timestamp))
        self.conn.commit()
        self.update_log_display_signal.emit(f"传感器数据 - 温度: {temp}, 气压: {pressure}, 深度: {depth} - {timestamp}")

    # 记录控制命令到数据库并更新日志显示
    def log_control(self, action):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO log (action, temperature, pressure, depth, timestamp) VALUES (?, NULL, NULL, NULL, ?)
        ''', (f"Control: {action}", timestamp))
        self.conn.commit()
        self.update_log_display_signal.emit(f"控制指令 - {action} - {timestamp}")

    # 提交状态到数据库
    def submit_status(self):
        status = "Some status"  # 这里可以根据实际情况获取状态
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO status (status, timestamp) VALUES (?, ?)
        ''', (status, timestamp))
        self.conn.commit()
        self.update_log_display_signal.emit(f"提交状态 - {status} - {timestamp}")

    # 更新日志显示框
    @QtCore.pyqtSlot(str)
    def update_log_display(self, log_entry):
        self.log_display.append(log_entry)

    # 刷新日志显示
    def refresh_log(self):
        self.db_log_display.clear()
        self.cursor.execute('SELECT * FROM log ORDER BY timestamp DESC')
        rows = self.cursor.fetchall()
        for row in rows:
            log_entry = f"{row[5]} - {row[1]} - 温度: {row[2]}, 气压: {row[3]}, 深度: {row[4]}"
            self.db_log_display.append(log_entry)

    # 发布模拟传感器数据
    def publish_sensor_data(self):
        while True:
            try:
                # 模拟生成传感器数据
                temperature = round(random.uniform(15.0, 30.0), 2)
                pressure = round(random.uniform(95.0, 105.0), 2)
                depth = round(random.uniform(0.0, 10.0), 2)
                
                # 如果不在离线模式，发布到MQTT代理
                if not self.offline_mode:
                    payload = f"Temperature: {temperature} °C, Pressure: {pressure} kPa, Depth: {depth} m"
                    self.client.publish(topic_sensor, payload)
                    print(f"Published: {payload}")
                else:
                    # 离线模式下直接更新界面并记录数据
                    self.update_sensor_labels_signal.emit(str(temperature), str(pressure), str(depth))
                    self.log_data_thread_safe(temperature, pressure, depth)

                time.sleep(10)
            except Exception as e:
                print(f"Error in publish_sensor_data: {e}")

    # 线程安全的日志数据记录
    def log_data_thread_safe(self, temp, pressure, depth):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        # 在新的线程中创建数据库连接
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO log (action, temperature, pressure, depth, timestamp) VALUES (?, ?, ?, ?, ?)
            ''', ("Sensor Data", temp, pressure, depth, timestamp))
            conn.commit()
        self.update_log_display_signal.emit(f"传感器数据 - 温度: {temp}, 气压: {pressure}, 深度: {depth} - {timestamp}")

    # 订阅控制信号
    def subscribe_control_signals(self):
        self.control_client = mqtt.Client()
        self.control_client.on_message = self.on_message_control
        self.control_client.connect(broker, port)
        self.control_client.subscribe(topic_control)
        self.control_client.loop_start()

    # 处理控制信号消息
    def on_message_control(self, client, userdata, msg):
        direction = msg.payload.decode()
        print(f"Received control signal: {direction}")

    def closeEvent(self, event):
        self.conn.close()
        if self.client:
            self.client.loop_stop()
        if self.control_client:
            self.control_client.loop_stop()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = UpperComputer(offline_mode=True)
    sys.exit(app.exec_())