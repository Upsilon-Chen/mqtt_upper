button_style = """
QPushButton {
    background-color: gray;
    color: white;  /* 白色文字 */
    border: none;  /* 无边框 */
    padding: 10px 20px;  /* 内边距 */
    text-align: center;  /* 文字居中 */
    font-size: 16px;  /* 字体大小 */
    margin: 4px 2px;  /* 外边距 */
    border-radius: 12px;  /* 圆角 */
}

QPushButton:hover {
    background-color: white;  /* 鼠标悬停时背景变为白色 */
    color: black;  /* 鼠标悬停时文字变为黑色 */
    border: 2px solid black;  /* 鼠标悬停时边框 */
}
"""

label_style = """
QLabel {
    font-size: 18px;  /* 字体大小 */
    color: black;  /* 文字颜色 */
    text-align: center;
    margin: 5px;  /* 外边距 */
    color: #333;  /* 文字颜色 */
    background-color: #e0e0e0;  /* 背景颜色 */
    padding: 10px;  /* 内边距 */
    border-radius: 5px;  /* 圆角 */
    margin: 5px;  /* 外边距 */
}
"""

log_display_style = """
QTextEdit {
    text-align: center;
    font-size: 16px;  /* 字体大小 */
    color: #333;  /* 文字颜色 */
    background-color: #f9f9f9;  /* 背景颜色 */
    border: 1px solid #ccc;  /* 边框 */
    padding: 10px;  /* 内边距 */
    border-radius: 5px;  /* 圆角 */
    margin: 5px;  /* 外边距 */
}
"""

tabs_style = """
    QTabWidget::pane { 
        /* Tab widget frame with soft shadow effect */
        border-top: 2px solid #C2C7CB;
        position: absolute;
        top: -0.5em;
        background: #FFFFFF; /* Pure white for a clean look */
        border-radius: 6px; 
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); /* Subtle shadow for depth */
    }
    QTabWidget::tab-bar {
        alignment: center; /* Center align tab bar */
    }
    QTabBar::tab {
        height: 20px; /* Tab height */
        background: #F5F7FA; /* Light gray for tabs */
        border: 1px solid #E0E0E0; /* Subtle border */
        border-bottom: none; /* Seamless integration with pane */
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        min-width: 80px; /* Wider tabs for modern UI */
        padding: 8px 12px; /* Increase padding for better touch targets */
        color: #4A4A4A; /* Neutral text color */
        font-size: 14px; /* Slightly larger font size for readability */
    }
    QTabBar::tab:selected {
        background: #FFFFFF; /* Highlight selected tab */
        border-color: #C2C7CB;
        color: #000000; /* Darker text for the active tab */
        font-weight: bold; /* Emphasize selected tab */
    }
    QTabBar::tab:hover {
        background: #F0F0F0; /* Hover effect */
        color: #333333; /* Slightly darker text on hover */
    }
    QTabBar::tab:disabled {
        background: #EDEDED; /* Disabled tab appearance */
        color: #A0A0A0; /* Muted text color */
    }
"""