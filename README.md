# 基于MQTT的上位机控制系统

## 概述

该项目是一个基于 **PyQt5** 和 **paho-mqtt** 开发的图形界面上位机系统，用于控制和监控水下机器人。它通过 **MQTT** 接收下位机发送的传感器数据，发送控制指令，并将日志和设备状态保存到 **SQLite** 数据库中。

## 功能

1. **实时监控传感器数据**：
   - 显示温度、气压和深度数据。
2. **机器人运动控制**：
   - 使用界面按钮（`W`、`S`、`A`、`D`）或键盘快捷键发送移动指令（前进、后退、左转、右转）。
3. **数据日志记录**：
   - 将所有传感器数据和控制指令与时间戳记录到 SQLite 数据库。
4. **日志和数据查看**：
   - 支持查看和刷新存储的日志和历史数据。
5. **模拟传感器数据**：
   - 每 10 秒生成一次随机传感器数据并通过 MQTT 代理发布。

## 系统要求

- Python 3.7 或更高版本
- 依赖库：
  - PyQt5
  - paho-mqtt
  - sqlite3

## 安装与运行

### 1. 克隆代码库

```bash
git clone <你的仓库地址>
cd <项目目录>
```

### 2. 安装依赖

确保你已经安装了 Python，然后运行以下命令安装所需的依赖库：

```bash
pip install PyQt5 paho-mqtt
```

### 3. 配置 MQTT 代理

默认的 MQTT 代理设置如下：
- 地址：`localhost`
- 端口：`1883`

如果你的代理地址或端口不同，请在代码中修改以下变量：
```python
broker = "localhost"
port = 1883
```

### 4. 运行程序

在项目根目录下运行以下命令启动程序：

```bash
python mqtt_upper.py
```

> **注意**：运行前确保 MQTT 代理正在运行，且 `styles` 文件夹下的样式文件已配置完成。

## 使用说明

1. **传感器数据监控**：
   - 程序启动后，实时显示传感器数据（温度、气压、深度）。
2. **机器人运动控制**：
   - 点击界面上的 `W`（前进）、`S`（后退）、`A`（左转）、`D`（右转）按钮，或使用键盘对应按键发送移动指令。
3. **数据保存**：
   - 点击“保存数据”按钮，将当前显示的传感器数据存入数据库。
4. **日志和数据查看**：
   - 在“日志”选项卡中点击“刷新日志”查看所有日志记录。
   - 在“保存的数据”选项卡中点击“刷新”查看已保存的数据。

## 数据存储结构

程序使用 **SQLite** 数据库存储日志和数据。数据库文件为 `robot_data.db`，包含以下两张表：
1. `log` 表：
   - 存储控制指令和传感器日志。
   - 字段：`id`, `action`, `temperature`, `pressure`, `depth`, `timestamp`
2. `data` 表：
   - 存储保存的传感器数据。
   - 字段：`id`, `temperature`, `pressure`, `depth`, `timestamp`

## 注意事项

- 如果关闭程序，请确保程序正常退出以避免数据损坏。
- 如果在日志中发现异常连接问题，请检查 MQTT 代理是否正常运行。

## 常见问题

### 1. 如何更改 MQTT 主题？
在代码中找到以下变量并修改为你的主题名称：
```python
topic_sensor = "sensor/data"
topic_control = "control/movement"
```

### 2. 为什么界面无法正常启动？
请确保安装了 PyQt5，并且依赖的样式文件路径正确。

## 贡献

欢迎提交 Issue 和 Pull Request 改进本项目！
