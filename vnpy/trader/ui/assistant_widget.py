"""
Trading Assistant Widget Implementation
"""

from typing import Optional
from .qt import QtCore, QtGui, QtWidgets

from ..engine import MainEngine, Event, EventEngine
from ..event import EVENT_TICK
from ..object import OrderRequest, TickData
from ..constant import Direction, Exchange, OrderType, Offset
from ..locale import _


class TradingAssistantWidget(QtWidgets.QWidget):
    """
    Trading Assistant Widget based on assistant.ui layout.
    Provides quick trading functionality for multiple stocks.
    """
    
    signal_tick: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """Initialize the trading assistant widget."""
        super().__init__()
        
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        
        # Store stock information
        self.stock_info = {
            "buy_1": {"symbol": "", "name": "浦发银行"},
            "buy_2": {"symbol": "", "name": "万科A"},
            "sell_1": {"symbol": "", "name": "浦发银行"},
            "sell_2": {"symbol": "", "name": "万科A"}
        }
        
        self.init_ui()
        self.register_event()

    def init_ui(self) -> None:
        """Initialize user interface."""
        self.setFixedSize(1210, 175)  # 高度从200调整为175，实际上缩小了一些因为原来有多余空间
        self.setWindowTitle("交易助手")
        self.setWindowOpacity(1.0)
        
        # Create main layout
        self.init_buy_section()
        self.init_sell_section()
        
        # Show the widget
        self.show()

    def init_buy_section(self) -> None:
        """Initialize buy (进货) section."""
        # Buy header frame - 放大宽度
        self.frame_buy_header = QtWidgets.QFrame(self)
        self.frame_buy_header.setGeometry(0, 10, 600, 35)  # 高度从30调整为35
        self.frame_buy_header.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        
        # Buy label
        self.label_buy = QtWidgets.QLabel("进货", self.frame_buy_header)
        self.label_buy.setGeometry(10, 2, 75, 30)  # Y位置从0调整为2，增加顶部间距
        font = QtGui.QFont()
        font.setPointSize(16)  # 字体大小从20调整为16
        font.setBold(True)
        self.label_buy.setFont(font)
        self.label_buy.setStyleSheet("color: rgb(255, 0, 0);")
        
        # Buy add button
        self.pushButton_buy_add = QtWidgets.QPushButton("增加", self.frame_buy_header)
        self.pushButton_buy_add.setGeometry(520, 2, 70, 30)  # Y位置从0调整为2，与标签对齐
        font = QtGui.QFont()
        font.setPointSize(9)  # 字体稍小
        font.setBold(True)
        self.pushButton_buy_add.setFont(font)
        self.pushButton_buy_add.clicked.connect(self.on_buy_add_clicked)
        
        # Buy main frame - 增加高度避免边框被覆盖
        self.frame_buy_main = QtWidgets.QFrame(self)
        self.frame_buy_main.setGeometry(0, 50, 600, 120)  # Y位置从45调整为50，适应更高的header
        self.frame_buy_main.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        
        # Buy content frame
        self.frame_buy_content = QtWidgets.QFrame(self.frame_buy_main)
        self.frame_buy_content.setGeometry(10, 10, 580, 100)  # 宽度从575调整为580
        self.frame_buy_content.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        
        # Buy input controls
        self.init_buy_controls()

    def init_buy_controls(self) -> None:
        """Initialize buy section controls."""
        # Headers - 调整标题控件宽度以显示完整文字，并居中对齐到编辑框
        QtWidgets.QLabel("代码", self.frame_buy_content).setGeometry(25, 5, 45, 18)  # 保持原位置
        QtWidgets.QLabel("价格", self.frame_buy_content).setGeometry(175, 5, 45, 18)  # X位置调整为175，居中对齐价格编辑框
        QtWidgets.QLabel("股数", self.frame_buy_content).setGeometry(255, 5, 45, 18)  # X位置调整为255，居中对齐股数编辑框
        
        # Row 1 controls - 适中输入框
        self.lineEdit_buy_symbol_1 = QtWidgets.QLineEdit(self.frame_buy_content)
        self.lineEdit_buy_symbol_1.setGeometry(10, 27, 75, 22)  # Y位置从22调整为27
        self.lineEdit_buy_symbol_1.setText("600000")  # 设置默认股票代码
        
        self.label_buy_name_1 = QtWidgets.QLabel("浦发银行", self.frame_buy_content)
        self.label_buy_name_1.setGeometry(85, 27, 70, 22)  # X位置从95调整为85，宽度从60调整为70
        
        self.lineEdit_buy_price_1 = QtWidgets.QLineEdit(self.frame_buy_content)
        self.lineEdit_buy_price_1.setGeometry(160, 27, 75, 22)  # Y位置从22调整为27
        self.lineEdit_buy_price_1.setText("120.8")  # 设置默认价格
        
        self.lineEdit_buy_qty_1 = QtWidgets.QLineEdit(self.frame_buy_content)
        self.lineEdit_buy_qty_1.setGeometry(240, 27, 75, 22)  # Y位置从22调整为27
        self.lineEdit_buy_qty_1.setText("5000")  # 设置默认股数
        
        # Row 2 controls - 适中输入框
        self.lineEdit_buy_symbol_2 = QtWidgets.QLineEdit(self.frame_buy_content)
        self.lineEdit_buy_symbol_2.setGeometry(10, 55, 75, 22)  # Y位置从50调整为55
        self.lineEdit_buy_symbol_2.setText("000002")  # 设置默认股票代码
        
        self.label_buy_name_2 = QtWidgets.QLabel("万科A", self.frame_buy_content)
        self.label_buy_name_2.setGeometry(85, 55, 70, 22)  # X位置从95调整为85，宽度从60调整为70
        
        self.lineEdit_buy_price_2 = QtWidgets.QLineEdit(self.frame_buy_content)
        self.lineEdit_buy_price_2.setGeometry(160, 55, 75, 22)  # Y位置从50调整为55
        self.lineEdit_buy_price_2.setText("20.88")  # 设置默认价格
        
        self.lineEdit_buy_qty_2 = QtWidgets.QLineEdit(self.frame_buy_content)
        self.lineEdit_buy_qty_2.setGeometry(240, 55, 75, 22)  # Y位置从50调整为55
        self.lineEdit_buy_qty_2.setText("28920")  # 设置默认股数
        
        # SpinBox - 适中尺寸
        self.spinBox_buy = QtWidgets.QSpinBox(self.frame_buy_content)
        self.spinBox_buy.setGeometry(325, 40, 85, 23)  # Y位置从35调整为40
        self.spinBox_buy.setValue(1)
        
        # Time selection group - 调整位置避免与spinBox重叠
        self.groupBox_buy_time = QtWidgets.QGroupBox("时间", self.frame_buy_content)
        self.groupBox_buy_time.setGeometry(420, 5, 80, 75)  # Y位置从0调整为5
        
        self.radioButton_buy_time_1 = QtWidgets.QRadioButton("1", self.groupBox_buy_time)
        self.radioButton_buy_time_1.setGeometry(8, 22, 30, 22)  # Y位置保持22（相对于groupBox）
        
        self.radioButton_buy_time_2 = QtWidgets.QRadioButton("2", self.groupBox_buy_time)
        self.radioButton_buy_time_2.setGeometry(42, 22, 30, 22)  # Y位置保持22（相对于groupBox）
        self.radioButton_buy_time_2.setChecked(True)
        
        self.radioButton_buy_time_3 = QtWidgets.QRadioButton("3", self.groupBox_buy_time)
        self.radioButton_buy_time_3.setGeometry(8, 45, 30, 22)  # Y位置保持45（相对于groupBox）
        
        self.radioButton_buy_time_5 = QtWidgets.QRadioButton("5", self.groupBox_buy_time)
        self.radioButton_buy_time_5.setGeometry(42, 45, 30, 22)  # Y位置保持45（相对于groupBox）
        
        # Buy order button - 调整位置
        self.pushButton_buy_order = QtWidgets.QPushButton("下单", self.frame_buy_content)
        self.pushButton_buy_order.setGeometry(510, 27, 60, 45)  # Y位置从22调整为27
        font = QtGui.QFont()
        font.setBold(True)
        self.pushButton_buy_order.setFont(font)
        self.pushButton_buy_order.clicked.connect(self.on_buy_order_clicked)

    def init_sell_section(self) -> None:
        """Initialize sell (出货) section."""
        # Sell header frame - 调整位置和尺寸
        self.frame_sell_header = QtWidgets.QFrame(self)
        self.frame_sell_header.setGeometry(605, 10, 600, 35)  # 高度从30调整为35
        self.frame_sell_header.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.frame_sell_header.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        
        # Sell label
        self.label_sell = QtWidgets.QLabel("出货", self.frame_sell_header)
        self.label_sell.setGeometry(10, 2, 75, 30)  # Y位置从0调整为2，增加顶部间距
        font = QtGui.QFont()
        font.setPointSize(16)  # 字体大小调整为16
        font.setBold(True)
        self.label_sell.setFont(font)
        self.label_sell.setStyleSheet("color: rgb(85, 0, 255);")
        
        # Sell add button
        self.pushButton_sell_add = QtWidgets.QPushButton("增加", self.frame_sell_header)
        self.pushButton_sell_add.setGeometry(520, 2, 70, 30)  # Y位置从0调整为2，与标签对齐
        font = QtGui.QFont()
        font.setPointSize(9)  # 字体稍小
        font.setBold(True)
        self.pushButton_sell_add.setFont(font)
        self.pushButton_sell_add.clicked.connect(self.on_sell_add_clicked)
        
        # Sell main frame - 增加高度避免边框被覆盖
        self.frame_sell_main = QtWidgets.QFrame(self)
        self.frame_sell_main.setGeometry(605, 50, 600, 120)  # Y位置从45调整为50，适应更高的header
        self.frame_sell_main.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        
        # Sell content frame
        self.frame_sell_content = QtWidgets.QFrame(self.frame_sell_main)
        self.frame_sell_content.setGeometry(10, 10, 580, 100)  # 宽度从575调整为580
        self.frame_sell_content.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        
        # Sell input controls
        self.init_sell_controls()

    def init_sell_controls(self) -> None:
        """Initialize sell section controls."""
        # Headers - 调整标题控件宽度以显示完整文字，并居中对齐到编辑框（与买入区域保持一致）
        QtWidgets.QLabel("代码", self.frame_sell_content).setGeometry(25, 5, 45, 18)  # 保持原位置
        QtWidgets.QLabel("价格", self.frame_sell_content).setGeometry(175, 5, 45, 18)  # X位置调整为175，居中对齐价格编辑框
        QtWidgets.QLabel("股数", self.frame_sell_content).setGeometry(255, 5, 45, 18)  # X位置调整为255，居中对齐股数编辑框
        
        # Row 1 controls - 适中输入框（与买入区域保持一致）
        self.lineEdit_sell_symbol_1 = QtWidgets.QLineEdit(self.frame_sell_content)
        self.lineEdit_sell_symbol_1.setGeometry(10, 27, 75, 22)  # Y位置从22调整为27
        self.lineEdit_sell_symbol_1.setText("600000")  # 设置默认股票代码
        
        self.label_sell_name_1 = QtWidgets.QLabel("浦发银行", self.frame_sell_content)
        self.label_sell_name_1.setGeometry(85, 27, 70, 22)  # X位置从95调整为85，宽度从60调整为70
        
        self.lineEdit_sell_price_1 = QtWidgets.QLineEdit(self.frame_sell_content)
        self.lineEdit_sell_price_1.setGeometry(160, 27, 75, 22)  # Y位置从22调整为27
        self.lineEdit_sell_price_1.setText("120.8")  # 设置默认价格
        
        self.lineEdit_sell_qty_1 = QtWidgets.QLineEdit(self.frame_sell_content)
        self.lineEdit_sell_qty_1.setGeometry(240, 27, 75, 22)  # Y位置从22调整为27
        self.lineEdit_sell_qty_1.setText("5000")  # 设置默认股数
        
        # Row 2 controls - 适中输入框（与买入区域保持一致）
        self.lineEdit_sell_symbol_2 = QtWidgets.QLineEdit(self.frame_sell_content)
        self.lineEdit_sell_symbol_2.setGeometry(10, 55, 75, 22)  # Y位置从50调整为55
        self.lineEdit_sell_symbol_2.setText("000002")  # 设置默认股票代码
        
        self.label_sell_name_2 = QtWidgets.QLabel("万科A", self.frame_sell_content)
        self.label_sell_name_2.setGeometry(85, 55, 70, 22)  # X位置从95调整为85，宽度从60调整为70
        
        self.lineEdit_sell_price_2 = QtWidgets.QLineEdit(self.frame_sell_content)
        self.lineEdit_sell_price_2.setGeometry(160, 55, 75, 22)  # Y位置从50调整为55
        self.lineEdit_sell_price_2.setText("20.88")  # 设置默认价格
        
        self.lineEdit_sell_qty_2 = QtWidgets.QLineEdit(self.frame_sell_content)
        self.lineEdit_sell_qty_2.setGeometry(240, 55, 75, 22)  # Y位置从50调整为55
        self.lineEdit_sell_qty_2.setText("28920")  # 设置默认股数
        
        # SpinBox - 适中数量选择器
        self.spinBox_sell = QtWidgets.QSpinBox(self.frame_sell_content)
        self.spinBox_sell.setGeometry(325, 40, 85, 23)  # Y位置从35调整为40
        self.spinBox_sell.setValue(1)
        
        # Time selection group - 调整位置避免与spinBox重叠
        self.groupBox_sell_time = QtWidgets.QGroupBox("时间", self.frame_sell_content)
        self.groupBox_sell_time.setGeometry(420, 5, 80, 75)  # Y位置从0调整为5
        
        self.radioButton_sell_time_1 = QtWidgets.QRadioButton("1", self.groupBox_sell_time)
        self.radioButton_sell_time_1.setGeometry(8, 22, 30, 22)  # Y位置保持22（相对于groupBox）
        
        self.radioButton_sell_time_2 = QtWidgets.QRadioButton("2", self.groupBox_sell_time)
        self.radioButton_sell_time_2.setGeometry(42, 22, 30, 22)  # Y位置保持22（相对于groupBox）
        self.radioButton_sell_time_2.setChecked(True)
        
        self.radioButton_sell_time_3 = QtWidgets.QRadioButton("3", self.groupBox_sell_time)
        self.radioButton_sell_time_3.setGeometry(8, 45, 30, 22)  # Y位置保持45（相对于groupBox）
        
        self.radioButton_sell_time_5 = QtWidgets.QRadioButton("5", self.groupBox_sell_time)
        self.radioButton_sell_time_5.setGeometry(42, 45, 30, 22)  # Y位置保持45（相对于groupBox）
        
        # Sell order button - 调整位置
        self.pushButton_sell_order = QtWidgets.QPushButton("下单", self.frame_sell_content)
        self.pushButton_sell_order.setGeometry(510, 27, 60, 45)  # Y位置从22调整为27
        font = QtGui.QFont()
        font.setBold(True)
        self.pushButton_sell_order.setFont(font)
        self.pushButton_sell_order.clicked.connect(self.on_sell_order_clicked)

    def register_event(self) -> None:
        """Register event handlers."""
        self.signal_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)

    def process_tick_event(self, event: Event) -> None:
        """Process tick data event to update prices."""
        tick: TickData = event.data
        
        # Update buy section prices
        if tick.symbol == self.lineEdit_buy_symbol_1.text():
            self.lineEdit_buy_price_1.setText(str(tick.last_price))
        elif tick.symbol == self.lineEdit_buy_symbol_2.text():
            self.lineEdit_buy_price_2.setText(str(tick.last_price))
            
        # Update sell section prices
        if tick.symbol == self.lineEdit_sell_symbol_1.text():
            self.lineEdit_sell_price_1.setText(str(tick.last_price))
        elif tick.symbol == self.lineEdit_sell_symbol_2.text():
            self.lineEdit_sell_price_2.setText(str(tick.last_price))

    def get_selected_time_interval(self, section: str) -> int:
        """Get selected time interval for the given section."""
        if section == "buy":
            if self.radioButton_buy_time_1.isChecked():
                return 1
            elif self.radioButton_buy_time_2.isChecked():
                return 2
            elif self.radioButton_buy_time_3.isChecked():
                return 3
            elif self.radioButton_buy_time_5.isChecked():
                return 5
        elif section == "sell":
            if self.radioButton_sell_time_1.isChecked():
                return 1
            elif self.radioButton_sell_time_2.isChecked():
                return 2
            elif self.radioButton_sell_time_3.isChecked():
                return 3
            elif self.radioButton_sell_time_5.isChecked():
                return 5
        return 2  # Default

    def send_order(self, symbol: str, price: float, quantity: int, direction: Direction) -> None:
        """Send order to the trading system."""
        if not symbol or price <= 0 or quantity <= 0:
            QtWidgets.QMessageBox.warning(self, "错误", "请输入有效的交易参数")
            return
            
        # Create order request
        req = OrderRequest(
            symbol=symbol,
            exchange=Exchange.SSE,  # Assume SSE exchange
            direction=direction,
            type=OrderType.LIMIT,
            volume=quantity,
            price=price,
            offset=Offset.NONE,
            reference="TradingAssistant"
        )
        
        # Send order
        gateway_names = self.main_engine.get_all_gateway_names()
        if gateway_names:
            vt_orderid = self.main_engine.send_order(req, gateway_names[0])
            if vt_orderid:
                direction_text = "买入" if direction == Direction.LONG else "卖出"
                QtWidgets.QMessageBox.information(
                    self, "委托成功", 
                    f"{direction_text}订单已提交\n"
                    f"股票: {symbol}\n"
                    f"价格: {price}\n"
                    f"数量: {quantity}\n"
                    f"订单号: {vt_orderid}"
                )
        else:
            QtWidgets.QMessageBox.warning(self, "错误", "没有可用的交易接口")

    def on_buy_add_clicked(self) -> None:
        """Handle buy add button click."""
        QtWidgets.QMessageBox.information(self, "功能", "买入增加功能")

    def on_sell_add_clicked(self) -> None:
        """Handle sell add button click."""
        QtWidgets.QMessageBox.information(self, "功能", "卖出增加功能")

    def on_buy_order_clicked(self) -> None:
        """Handle buy order button click."""
        # Get selected time interval
        time_interval = self.get_selected_time_interval("buy")
        
        # Process buy orders based on spinbox value
        spinbox_value = self.spinBox_buy.value()
        
        if spinbox_value >= 1:
            # Process first buy order
            symbol = self.lineEdit_buy_symbol_1.text().strip()
            try:
                price = float(self.lineEdit_buy_price_1.text() or "0")
                quantity = int(self.lineEdit_buy_qty_1.text() or "0")
                if symbol and price > 0 and quantity > 0:
                    self.send_order(symbol, price, quantity, Direction.LONG)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "错误", "第一行买入参数格式错误")
                
        if spinbox_value >= 2:
            # Process second buy order
            symbol = self.lineEdit_buy_symbol_2.text().strip()
            try:
                price = float(self.lineEdit_buy_price_2.text() or "0")
                quantity = int(self.lineEdit_buy_qty_2.text() or "0")
                if symbol and price > 0 and quantity > 0:
                    self.send_order(symbol, price, quantity, Direction.LONG)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "错误", "第二行买入参数格式错误")

    def on_sell_order_clicked(self) -> None:
        """Handle sell order button click."""
        # Get selected time interval
        time_interval = self.get_selected_time_interval("sell")
        
        # Process sell orders based on spinbox value
        spinbox_value = self.spinBox_sell.value()
        
        if spinbox_value >= 1:
            # Process first sell order
            symbol = self.lineEdit_sell_symbol_1.text().strip()
            try:
                price = float(self.lineEdit_sell_price_1.text() or "0")
                quantity = int(self.lineEdit_sell_qty_1.text() or "0")
                if symbol and price > 0 and quantity > 0:
                    self.send_order(symbol, price, quantity, Direction.SHORT)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "错误", "第一行卖出参数格式错误")
                
        if spinbox_value >= 2:
            # Process second sell order
            symbol = self.lineEdit_sell_symbol_2.text().strip()
            try:
                price = float(self.lineEdit_sell_price_2.text() or "0")
                quantity = int(self.lineEdit_sell_qty_2.text() or "0")
                if symbol and price > 0 and quantity > 0:
                    self.send_order(symbol, price, quantity, Direction.SHORT)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "错误", "第二行卖出参数格式错误")

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Unregister event handlers
        if hasattr(self, 'event_engine') and self.event_engine:
            try:
                self.event_engine.unregister(EVENT_TICK, self.signal_tick.emit)
            except:
                pass
        
        # Clean up resources if needed
        super().closeEvent(event)