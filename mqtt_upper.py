import sys
import random
import time
from PyQt5 import QtWidgets, QtCore, QtGui
import paho.mqtt.client as mqtt
import threading
import sqlite3
from styles.styles import button_style, label_style, log_display_style ,tabs_style

# MQTT Broker 设置
broker = "localhost"
port = 1883
topic_sensor = "sensor/data"
topic_control = "control/movement"

# 数据库文件
db_file = 'robot_data.db'

class UpperComputer(QtWidgets.QWidget):
    update_sensor_labels_signal = QtCore.pyqtSignal(str, str, str)
    update_log_display_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.elf = True
        self.client = None  # 初始化 client 属性
        self.control_client = None  # 初始化 control_client 属性
        self.latest_data = None  # 用于存储最近一次的所有数据
        self.initUI()
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
        self.setGeometry(100, 100, 600, 700)
        self.setStyleSheet("QWidget { background-color: #f0f0f0; }")  # 设置背景颜色
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        # 创建选项卡控件
        self.tabs = QtWidgets.QTabWidget()
        self.control_tab = QtWidgets.QWidget()
        self.log_tab = QtWidgets.QWidget()
        self.save_tab = QtWidgets.QWidget()

        self.tabs.setStyleSheet("QTabWidget { background-color: #f0f0f0; }")  # 设置选项卡背景颜色

        # 添加选项卡 
        self.tabs.addTab(self.control_tab, "控制")
        self.tabs.addTab(self.log_tab, "日志")
        self.tabs.addTab(self.save_tab, "保存的数据")

        self.tabs.setStyleSheet(tabs_style)

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

        # 设置按钮样式
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

        # 提交数据按钮
        self.submit_data_button = QtWidgets.QPushButton('保存数据')
        self.submit_data_button.setStyleSheet(button_style)
        self.submit_data_button.clicked.connect(self.submit_data)
        control_layout.addWidget(self.submit_data_button)

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

        # 保存数据选项卡布局
        save_layout = QtWidgets.QVBoxLayout(self.save_tab)

        # 数据库保存数据显示框
        self.db_save_display = QtWidgets.QTextEdit(self)
        self.db_save_display.setReadOnly(True)
        self.db_save_display.setStyleSheet(log_display_style)
        save_layout.addWidget(self.db_save_display)

        # 刷新保存数据按钮
        self.refresh_save_button = QtWidgets.QPushButton('刷新')
        self.refresh_save_button.setStyleSheet(button_style)
        self.refresh_save_button.clicked.connect(self.refresh_save)
        save_layout.addWidget(self.refresh_save_button)

        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        self.show()

    # 捕捉键盘事件
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

        # 解析传感器数据并显示在界面上
        if msg.topic == topic_sensor:
            if self.elf:
                self.update_log_display_signal.emit(f"成功连接到 MQTT 代理 { broker } 端口 {port} ")
                self.update_log_display_signal.emit(f"成功连接到数据库 {db_file}")
                self.elf = False
            temp, pressure, depth = self.parse_sensor_data(data)
            self.update_sensor_labels_signal.emit(temp, pressure, depth)
            self.log_data(temp, pressure, depth)

    # 解析传感器数据
    def parse_sensor_data(self, data):
        parts = data.split(',')
        temp = parts[0].split(': ')[1]
        pressure = parts[1].split(': ')[1]
        depth = parts[2].split(': ')[1]
        return temp, pressure, depth

    # 更新界面上的传感器数据
    @QtCore.pyqtSlot(str, str, str)
    def update_sensor_labels(self, temp, pressure, depth):
        self.temp_label.setText(f"温度: {temp} ")
        self.pressure_label.setText(f"气压: {pressure} ")
        self.depth_label.setText(f"深度: {depth} ")

    # 发送控制信号
    def send_control_signal(self, direction):
        self.client.publish(topic_control, direction)
        print(f"Sent control signal: {direction}")
        self.log_control(direction)

    # 初始化数据库
    def initDatabase(self):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
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
        # 创建数据表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature REAL,
                pressure REAL,
                depth REAL,
                timestamp TEXT
            )
        ''')
        self.conn.commit()

    # 记录传感器数据到数据库并更新日志显示
    @QtCore.pyqtSlot(str, str, str)
    def log_data(self, temp, pressure, depth):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO log (action, temperature, pressure, depth, timestamp) VALUES (?, ?, ?, ?, ?)
        ''', ("Sensor Data", temp, pressure, depth, timestamp))
        self.conn.commit()
        self.latest_data = (temp, pressure, depth, timestamp)  # 更新最近一次的所有数据
        self.update_log_display_signal.emit(f"传感器数据 - 温度: {temp}, 气压: {pressure}, 深度: {depth} - {timestamp}")

    # 记录控制命令到数据库并更新日志显示
    @QtCore.pyqtSlot(str)
    def log_control(self, action):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO log (action, timestamp) VALUES (?, ?)
        ''', (f"Control: {action}", timestamp))
        self.conn.commit()
        self.update_log_display_signal.emit(f"控制指令 - {action} - {timestamp}")

    # 提交数据到数据库
    def submit_data(self):
        if self.latest_data:
            temp, pressure, depth, timestamp = self.latest_data
            self.cursor.execute('''
                INSERT INTO data (temperature, pressure, depth, timestamp) VALUES (?, ?, ?, ?)
            ''', (temp, pressure, depth, timestamp))
            self.conn.commit()
            self.update_log_display_signal.emit(f"保存数据 - 温度: {temp}, 气压: {pressure}, 深度: {depth} - {timestamp}")
        else:
            self.update_log_display_signal.emit("没有可保存的数据")

    # 更新日志显示框
    @QtCore.pyqtSlot(str)
    def update_log_display(self, log_entry):
        self.log_display.append(log_entry)
        # 将光标移动到文本的末尾
        self.log_display.moveCursor(QtGui.QTextCursor.End)

    # 刷新日志显示
    def refresh_log(self):
        self.db_log_display.clear()
        self.cursor.execute('SELECT * FROM log ORDER BY timestamp ASC')  # 按时间戳升序排列
        rows = self.cursor.fetchall()
        for row in rows:
            log_entry = f"{row[5]} - {row[1]} - 温度: {row[2]}, 气压: {row[3]}, 深度: {row[4]}"
            self.db_log_display.append(log_entry)
        # 将光标移动到文本的末尾
        self.db_log_display.moveCursor(QtGui.QTextCursor.End)

    # 刷新保存的数据显示
    def refresh_save(self):
        self.db_save_display.clear()
        self.cursor.execute('SELECT * FROM data ORDER BY timestamp ASC')  # 按时间戳升序排列
        rows = self.cursor.fetchall()
        for row in rows:
            save_entry = f"{row[4]} - 温度: {row[1]}, 气压: {row[2]}, 深度: {row[3]}"
            self.db_save_display.append(save_entry)
        # 将光标移动到文本的末尾
        self.db_save_display.moveCursor(QtGui.QTextCursor.End)

    # 发布模拟传感器数据
    def publish_sensor_data(self):
        while True:
            try:
                # 模拟生成传感器数据
                temperature = round(random.uniform(15.0, 30.0), 2)
                pressure = round(random.uniform(95.0, 105.0), 2)
                depth = round(random.uniform(0.0, 10.0), 2)
                
                # 发布到MQTT代理
                payload = f"Temperature: {temperature} °C, Pressure: {pressure} kPa, Depth: {depth} m"
                self.update_sensor_labels_signal.emit(str(temperature), str(pressure), str(depth))
                # self.log_data_thread_safe(temperature, pressure, depth)
                self.client.publish(topic_sensor, payload)
                print(f"Published: {payload}")

                time.sleep(10)
            except Exception as e:
                print(f"Error in publish_sensor_data: {e}")

    # 线程安全的日志数据记录
    def log_data_thread_safe(self, temp, pressure, depth):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO log (action, temperature, pressure, depth, timestamp) VALUES (?, ?, ?, ?, ?)
            ''', ("Sensor Data", temp, pressure, depth, timestamp))
            conn.commit()
        # 更新 latest_data 以便后续提交数据
        self.latest_data = (temp, pressure, depth, timestamp)
        self.update_log_display_signal.emit(f"传感器数据 - 温度: {temp} °C, 气压: {pressure} kPa, 深度: {depth} m - {timestamp}")

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
    ex = UpperComputer()
    sys.exit(app.exec_())