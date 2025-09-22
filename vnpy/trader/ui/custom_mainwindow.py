"""
Implements custom main window of the trading platform.
"""

import json
import os
import vnpy
from vnpy.event import EventEngine

from .qt import QtCore, QtGui, QtWidgets
from .widget import (
    StockTradingWidget,
    Level2Widget,
    TradingAssistantWidget,
)
from ..engine import MainEngine
from ..utility import get_icon_path, TRADER_DIR
from ..locale import _


class CustomMainWindow(QtWidgets.QMainWindow):
    """
    Custom main window of the trading platform.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.widgets: dict[str, QtWidgets.QWidget] = {}
        self.drag_position = None

        self.init_ui()
        self.load_window_states()

    def init_ui(self) -> None:
        """"""
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.statusBar().hide()
        self.menuBar().hide()
        
        self.init_toolbar()
        
        self.setFixedHeight(60)
        self.setMinimumWidth(500)
        # self.resize(600, 60)

    def init_toolbar(self) -> None:
        """"""
        self.toolbar: QtWidgets.QToolBar = QtWidgets.QToolBar(self)
        self.toolbar.setObjectName(_("工具栏"))
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        self.toolbar.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.toolbar.setIconSize(QtCore.QSize(32, 32))
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        # 股票交易按钮
        stock_button = QtWidgets.QToolButton()
        stock_button.setText("股票交易")
        stock_button.setIcon(QtGui.QIcon(get_icon_path(__file__, "contract.ico")))
        stock_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        stock_button.clicked.connect(self.open_stock_trading_widget)
        self.toolbar.addWidget(stock_button)

        self.toolbar.addSeparator()

        # 交易助手按钮
        assistant_button = QtWidgets.QToolButton()
        assistant_button.setText("交易助手")
        assistant_button.setIcon(QtGui.QIcon(get_icon_path(__file__, "forum.ico")))
        assistant_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        assistant_button.clicked.connect(self.open_trading_assistant_widget)
        self.toolbar.addWidget(assistant_button)

        self.toolbar.addSeparator()

        # Level2按钮
        level2_button = QtWidgets.QToolButton()
        level2_button.setText("Level2")
        level2_button.setIcon(QtGui.QIcon(get_icon_path(__file__, "database.ico")))
        level2_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        level2_button.clicked.connect(self.open_level2_widget)
        self.toolbar.addWidget(level2_button)

        self.toolbar.addSeparator()

        # 退出按钮
        exit_button = QtWidgets.QToolButton()
        exit_button.setText("退出")
        exit_button.setIcon(QtGui.QIcon(get_icon_path(__file__, "exit.ico")))
        exit_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        exit_button.clicked.connect(self.close)
        self.toolbar.addWidget(exit_button)

        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # 最小化按钮
        self.minimize_button = QtWidgets.QPushButton("−", self)
        self.minimize_button.setFixedSize(25, 25)
        self.minimize_button.setToolTip("最小化")
        self.minimize_button.clicked.connect(self.showMinimized)
        self.minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: 2px solid #808080;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
                color: #404040;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
                border-color: #606060;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
                border-color: #404040;
            }
        """)

    def resizeEvent(self, event) -> None:
        """重写resize事件，确保最小化按钮始终在右上角"""
        super().resizeEvent(event)
        if hasattr(self, 'minimize_button'):
            self.minimize_button.move(self.width() - 30, 5)

    def mousePressEvent(self, event) -> None:
        """鼠标按下事件，记录拖拽起始位置"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """鼠标移动事件，实现窗口拖拽"""
        if (event.buttons() == QtCore.Qt.MouseButton.LeftButton and 
            self.drag_position is not None):
            self.move(event.globalPosition().toPoint() - self.drag_position)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """鼠标释放事件，清除拖拽状态"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.drag_position = None
        super().mouseReleaseEvent(event)

    def get_window_states_file(self) -> str:
        """获取窗口状态保存文件路径"""
        return os.path.join(TRADER_DIR, "window_states.json")

    def save_window_states(self) -> None:
        """保存所有窗口的状态"""
        states = {}
        
        # 保存主窗口位置
        states["main_window"] = {
            "x": self.x(),
            "y": self.y(),
            "width": self.width(),
            "height": self.height()
        }
        
        # 保存子窗口状态
        for name, widget in self.widgets.items():
            if widget.isVisible():
                states[name] = {
                    "x": widget.x(),
                    "y": widget.y(),
                    "width": widget.width(),
                    "height": widget.height(),
                    "window_title": widget.windowTitle(),
                    "widget_type": widget.__class__.__name__
                }
        
        try:
            with open(self.get_window_states_file(), 'w', encoding='utf-8') as f:
                json.dump(states, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存窗口状态失败: {e}")

    def load_window_states(self) -> None:
        """加载并恢复所有窗口的状态"""
        states_file = self.get_window_states_file()
        if not os.path.exists(states_file):
            # 如果没有保存的状态，使用默认位置
            self.resize(600, 60)
            return
            
        try:
            with open(states_file, 'r', encoding='utf-8') as f:
                states = json.load(f)
            
            # 恢复主窗口位置
            if "main_window" in states:
                main_state = states["main_window"]
                self.resize(main_state["width"], main_state["height"])
                self.move(main_state["x"], main_state["y"])
            else:
                self.resize(600, 60)
            
            # 恢复子窗口
            for name, state in states.items():
                if name != "main_window" and "widget_type" in state:
                    widget_type = state["widget_type"]
                    if widget_type == "StockTradingWidget":
                        self.restore_stock_trading_widget(name, state)
                    elif widget_type == "TradingAssistantWidget":
                        self.restore_trading_assistant_widget(name, state)
                    elif widget_type == "Level2Widget":
                        self.restore_level2_widget(name, state)
                        
        except Exception as e:
            print(f"加载窗口状态失败: {e}")
            self.resize(600, 60)

    def restore_stock_trading_widget(self, name: str, state: dict) -> None:
        """恢复股票交易窗口"""
        widget = StockTradingWidget(self.main_engine, self.event_engine)
        widget.setWindowTitle(state["window_title"])
        widget.resize(state["width"], state["height"])
        widget.move(state["x"], state["y"])
        self.widgets[name] = widget
        widget.show()

    def restore_trading_assistant_widget(self, name: str, state: dict) -> None:
        """恢复交易助手窗口"""
        widget = TradingAssistantWidget(self.main_engine, self.event_engine)
        widget.setWindowTitle(state["window_title"])
        widget.resize(state["width"], state["height"])
        widget.move(state["x"], state["y"])
        self.widgets[name] = widget
        widget.show()

    def restore_level2_widget(self, name: str, state: dict) -> None:
        """恢复Level2窗口"""
        widget = Level2Widget(self.main_engine, self.event_engine)
        widget.setWindowTitle(state["window_title"])
        widget.resize(state["width"], state["height"])
        widget.move(state["x"], state["y"])
        self.widgets[name] = widget
        widget.show()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Call main engine close function before exit.
        """
        # 首先询问是否要退出
        exit_reply = QtWidgets.QMessageBox.question(
            self,
            _("退出"),
            _("确认退出？"),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if exit_reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # 询问是否保存当前布局
            save_reply = QtWidgets.QMessageBox.question(
                self,
                _("保存布局"),
                _("是否保存当前窗口布局？\n下次启动时将恢复相同的窗口位置。"),
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes,
            )
            
            # 根据用户选择决定是否保存窗口状态
            if save_reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.save_window_states()
            
            for widget in self.widgets.values():
                widget.close()

            self.main_engine.close()
            event.accept()
        else:
            event.ignore()

    def open_stock_trading_widget(self) -> None:
        """
        Open a new stock trading widget instance.
        """
        import time
        timestamp = str(int(time.time() * 1000))
        name = f"stock_trading_{timestamp}"
        
        widget = StockTradingWidget(self.main_engine, self.event_engine)
        widget.setWindowTitle(f"股票交易 - {timestamp[-6:]}")
        
        # 连接关闭事件，在窗口关闭时从字典中移除
        def on_widget_close():
            if name in self.widgets:
                del self.widgets[name]
        widget.destroyed.connect(on_widget_close)
        
        self.widgets[name] = widget
        widget.show()

    def open_trading_assistant_widget(self) -> None:
        """
        Open a new trading assistant widget instance.
        """
        import time
        timestamp = str(int(time.time() * 1000))
        name = f"trading_assistant_{timestamp}"
        
        widget = TradingAssistantWidget(self.main_engine, self.event_engine)
        widget.setWindowTitle(f"交易助手 - {timestamp[-6:]}")
        
        # 连接关闭事件，在窗口关闭时从字典中移除
        def on_widget_close():
            if name in self.widgets:
                del self.widgets[name]
        widget.destroyed.connect(on_widget_close)
        
        self.widgets[name] = widget
        widget.show()

    def open_level2_widget(self) -> None:
        """
        Open a new Level-2 market data widget instance.
        """
        import time
        timestamp = str(int(time.time() * 1000))
        name = f"level2_{timestamp}"
        
        widget = Level2Widget(self.main_engine, self.event_engine)
        widget.setWindowTitle(f"Level-2 十档行情 - {timestamp[-6:]}")
        
        # 连接关闭事件，在窗口关闭时从字典中移除
        def on_widget_close():
            if name in self.widgets:
                del self.widgets[name]
        widget.destroyed.connect(on_widget_close)
        
        self.widgets[name] = widget
        widget.show()