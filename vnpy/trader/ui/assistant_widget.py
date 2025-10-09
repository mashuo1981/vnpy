"""
Trading Assistant Widget Implementation
"""

import time
from typing import Optional, List, Dict, Any, Callable
from .qt import QtCore, QtGui, QtWidgets

from ..engine import MainEngine, Event, EventEngine
from ..event import EVENT_TICK
from ..object import OrderRequest, TickData
from ..constant import Direction, Exchange, OrderType, Offset
from ..locale import _
from ..tcp_client import TcpOrderClient
from ..tcp_client.config import get_tcp_config


class TradingSectionWidget(QtWidgets.QWidget):
    """
    Reusable trading section widget that can be used for buy or sell operations.
    Contains stock symbol, price, quantity inputs and time selection controls.
    No header/title section - only the trading controls.
    """
    
    def __init__(
        self, 
        parent: QtWidgets.QWidget,
        section_type: str = "sell",  # "buy" or "sell"
        default_stocks: list = None,
        on_order_callback: Optional[Callable] = None
    ) -> None:
        """
        Initialize trading section widget.
        
        Args:
            parent: Parent widget
            section_type: "buy" or "sell"
            default_stocks: List of default stock data [{"symbol": "600000", "name": "浦发银行", "price": "120.8", "qty": "5000"}, ...]
            on_order_callback: Callback function for order button click
        """
        super().__init__(parent)
        
        self.section_type = section_type
        self.on_order_callback = on_order_callback
        
        # Default stock data
        if default_stocks is None:
            self.default_stocks = [
                {"symbol": "600000", "name": "浦发银行", "price": "120.8", "qty": "5000"},
                {"symbol": "000002", "name": "万科A", "price": "20.88", "qty": "28920"}
            ]
        else:
            self.default_stocks = default_stocks
        
        # Initialize UI components
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initialize user interface."""
        self.setFixedSize(600, 120)  # 减少高度，因为移除了头部
        
        # Create main content frame directly
        self.init_content()
    
    def init_content(self) -> None:
        """Initialize content section."""
        # Main frame (now starts from top)
        self.frame_main = QtWidgets.QFrame(self)
        self.frame_main.setGeometry(0, 0, 600, 120)  # 从顶部开始
        self.frame_main.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        
        # Content frame
        self.frame_content = QtWidgets.QFrame(self.frame_main)
        self.frame_content.setGeometry(10, 10, 580, 100)
        self.frame_content.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        
        # Initialize controls
        self.init_controls()
    
    def init_controls(self) -> None:
        """Initialize input controls."""
        # Headers
        QtWidgets.QLabel("代码", self.frame_content).setGeometry(25, 5, 45, 18)
        QtWidgets.QLabel("价格", self.frame_content).setGeometry(175, 5, 45, 18)
        QtWidgets.QLabel("股数", self.frame_content).setGeometry(255, 5, 45, 18)
        
        # Create input controls for each row
        self.stock_controls = []
        for i, stock_data in enumerate(self.default_stocks[:2]):  # Limit to 2 rows
            y_pos = 27 + (i * 28)  # Row spacing
            
            controls = {}
            
            # Symbol input
            controls['symbol'] = QtWidgets.QLineEdit(self.frame_content)
            controls['symbol'].setGeometry(10, y_pos, 75, 22)
            controls['symbol'].setText(stock_data.get("symbol", ""))
            
            # Name label
            controls['name'] = QtWidgets.QLabel(stock_data.get("name", ""), self.frame_content)
            controls['name'].setGeometry(85, y_pos, 70, 22)
            
            # Price input
            controls['price'] = QtWidgets.QLineEdit(self.frame_content)
            controls['price'].setGeometry(160, y_pos, 75, 22)
            controls['price'].setText(stock_data.get("price", ""))
            
            # Quantity input
            controls['qty'] = QtWidgets.QLineEdit(self.frame_content)
            controls['qty'].setGeometry(240, y_pos, 75, 22)
            controls['qty'].setText(stock_data.get("qty", ""))
            
            self.stock_controls.append(controls)
        
        # SpinBox for row selection
        self.spinBox = QtWidgets.QSpinBox(self.frame_content)
        self.spinBox.setGeometry(325, 40, 85, 23)
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(len(self.stock_controls))
        self.spinBox.setValue(1)
        
        # Time selection group
        self.groupBox_time = QtWidgets.QGroupBox("时间", self.frame_content)
        self.groupBox_time.setGeometry(420, 5, 80, 75)
        
        # Time radio buttons
        self.radioButton_time_1 = QtWidgets.QRadioButton("1", self.groupBox_time)
        self.radioButton_time_1.setGeometry(8, 22, 30, 22)
        
        self.radioButton_time_2 = QtWidgets.QRadioButton("2", self.groupBox_time)
        self.radioButton_time_2.setGeometry(42, 22, 30, 22)
        self.radioButton_time_2.setChecked(True)  # Default selection
        
        self.radioButton_time_3 = QtWidgets.QRadioButton("3", self.groupBox_time)
        self.radioButton_time_3.setGeometry(8, 45, 30, 22)
        
        self.radioButton_time_5 = QtWidgets.QRadioButton("5", self.groupBox_time)
        self.radioButton_time_5.setGeometry(42, 45, 30, 22)
        
        # Order button
        self.pushButton_order = QtWidgets.QPushButton("下单", self.frame_content)
        self.pushButton_order.setGeometry(510, 27, 60, 45)
        font = QtGui.QFont()
        font.setBold(True)
        self.pushButton_order.setFont(font)
        self.pushButton_order.clicked.connect(self.on_order_clicked)
    
    def get_selected_time_interval(self) -> int:
        """Get selected time interval."""
        if self.radioButton_time_1.isChecked():
            return 1
        elif self.radioButton_time_2.isChecked():
            return 2
        elif self.radioButton_time_3.isChecked():
            return 3
        elif self.radioButton_time_5.isChecked():
            return 5
        return 2  # Default
    
    def get_spinbox_value(self) -> int:
        """Get spinbox value (number of rows to process)."""
        return self.spinBox.value()
    
    def get_stock_data(self, row_index: int) -> Dict[str, Any]:
        """
        Get stock data for specified row.
        
        Args:
            row_index: Row index (0-based)
            
        Returns:
            Dictionary containing symbol, price, quantity data
        """
        if 0 <= row_index < len(self.stock_controls):
            controls = self.stock_controls[row_index]
            return {
                'symbol': controls['symbol'].text().strip(),
                'price': controls['price'].text().strip(),
                'quantity': controls['qty'].text().strip(),
                'name': controls['name'].text()
            }
        return {}
    
    def update_price(self, symbol: str, price: str) -> None:
        """Update price for matching symbol."""
        for controls in self.stock_controls:
            if controls['symbol'].text() == symbol:
                controls['price'].setText(price)
                break
    
    def on_order_clicked(self) -> None:
        """Handle order button click."""
        if self.on_order_callback:
            time_interval = self.get_selected_time_interval()
            
            # 始终处理区域内的所有股票（忽略SpinBox值）
            stock_data_list = []
            for i in range(len(self.stock_controls)):  # 处理所有行
                stock_data = self.get_stock_data(i)
                if stock_data['symbol'] and stock_data['price'] and stock_data['quantity']:
                    try:
                        stock_data['price'] = float(stock_data['price'])
                        stock_data['quantity'] = int(stock_data['quantity'])
                        stock_data_list.append(stock_data)
                    except ValueError:
                        continue
            
            self.on_order_callback(self, stock_data_list, time_interval)


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
        
        # Store trading sections
        self.buy_sections: List[TradingSectionWidget] = []
        self.sell_sections: List[TradingSectionWidget] = []
        
        # Load TCP configuration
        tcp_config = get_tcp_config()
        self.tcp_host = tcp_config["host"]
        self.tcp_port = tcp_config["port"]
        self.enable_tcp_orders = tcp_config["enable_tcp_orders"]
        
        self.init_ui()
        self.register_event()

    def init_ui(self) -> None:
        """Initialize user interface."""
        self.setFixedSize(1210, 470)  # 恢复原始高度
        self.setWindowTitle("交易助手")
        self.setWindowOpacity(1.0)
        
        # Create buy section
        self.init_buy_section()
        
        # Create sell section header (unified for all 3 sections)
        self.init_sell_header()
        
        # Create 3 sell sections
        self.init_sell_sections()
        
        # Show the widget
        self.show()

    def init_buy_section(self) -> None:
        """Initialize buy (进货) section."""
        # Buy header frame (恢复原始位置)
        self.frame_buy_header = QtWidgets.QFrame(self)
        self.frame_buy_header.setGeometry(0, 10, 600, 35)
        self.frame_buy_header.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        
        # Buy label
        self.label_buy = QtWidgets.QLabel("进货", self.frame_buy_header)
        self.label_buy.setGeometry(10, 2, 75, 30)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label_buy.setFont(font)
        self.label_buy.setStyleSheet("color: rgb(255, 0, 0);")
        
        # Buy add button
        self.pushButton_buy_add = QtWidgets.QPushButton("增加", self.frame_buy_header)
        self.pushButton_buy_add.setGeometry(520, 2, 70, 30)
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.pushButton_buy_add.setFont(font)
        self.pushButton_buy_add.clicked.connect(self.on_buy_add_clicked)
        
        # Initialize buy sections using TradingSectionWidget
        self.init_buy_sections()

    def init_buy_sections(self) -> None:
        """Initialize 3 buy sections using TradingSectionWidget."""
        # Define default stock data for each buy section
        buy_section_configs = [
            {
                "stocks": [
                    {"symbol": "600000", "name": "浦发银行", "price": "120.8", "qty": "5000"},
                    {"symbol": "000002", "name": "万科A", "price": "20.88", "qty": "28920"}
                ]
            },
            {
                "stocks": [
                    {"symbol": "000001", "name": "平安银行", "price": "15.50", "qty": "10000"},
                    {"symbol": "600036", "name": "招商银行", "price": "42.30", "qty": "2000"}
                ]
            },
            {
                "stocks": [
                    {"symbol": "002594", "name": "比亚迪", "price": "245.80", "qty": "500"},
                    {"symbol": "300015", "name": "爱尔眼科", "price": "89.90", "qty": "1500"}
                ]
            }
        ]
        
        # Create buy sections
        for i, config in enumerate(buy_section_configs):
            y_position = 50 + (i * 135)  # 恢复原始位置
            
            buy_section = TradingSectionWidget(
                parent=self,
                section_type="buy",
                default_stocks=config["stocks"],
                on_order_callback=self.on_buy_order_callback
            )
            
            # Position the section on the left side
            buy_section.setGeometry(0, y_position, 600, 120)
            buy_section.show()
            
            self.buy_sections.append(buy_section)



    def init_sell_header(self) -> None:
        """Initialize unified sell section header."""
        # Sell header frame (恢复原始位置)
        self.frame_sell_header = QtWidgets.QFrame(self)
        self.frame_sell_header.setGeometry(605, 10, 600, 35)
        self.frame_sell_header.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.frame_sell_header.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        
        # Sell label
        self.label_sell = QtWidgets.QLabel("出货", self.frame_sell_header)
        self.label_sell.setGeometry(10, 2, 75, 30)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label_sell.setFont(font)
        self.label_sell.setStyleSheet("color: rgb(85, 0, 255);")
        
        # Sell add button
        self.pushButton_sell_add = QtWidgets.QPushButton("增加", self.frame_sell_header)
        self.pushButton_sell_add.setGeometry(520, 2, 70, 30)
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.pushButton_sell_add.setFont(font)
        self.pushButton_sell_add.clicked.connect(self.on_sell_add_clicked)

    def init_sell_sections(self) -> None:
        """Initialize 3 sell sections."""
        # Define default stock data for each section
        sell_section_configs = [
            {
                "stocks": [
                    {"symbol": "600000", "name": "浦发银行", "price": "120.8", "qty": "5000"},
                    {"symbol": "000002", "name": "万科A", "price": "20.88", "qty": "28920"}
                ]
            },
            {
                "stocks": [
                    {"symbol": "000001", "name": "平安银行", "price": "15.50", "qty": "10000"},
                    {"symbol": "600036", "name": "招商银行", "price": "42.30", "qty": "2000"}
                ]
            },
            {
                "stocks": [
                    {"symbol": "000858", "name": "五 粮 液", "price": "180.60", "qty": "1000"},
                    {"symbol": "600519", "name": "贵州茅台", "price": "1650.00", "qty": "100"}
                ]
            }
        ]
        
        # Create sell sections
        for i, config in enumerate(sell_section_configs):
            y_position = 50 + (i * 135)  # 恢复原始位置
            
            sell_section = TradingSectionWidget(
                parent=self,
                section_type="sell",
                default_stocks=config["stocks"],
                on_order_callback=self.on_sell_order_callback
            )
            
            # Position the section on the right side
            sell_section.setGeometry(605, y_position, 600, 120)
            sell_section.show()
            
            self.sell_sections.append(sell_section)

    def on_buy_order_callback(
        self, 
        section: TradingSectionWidget, 
        stock_data_list: List[Dict[str, Any]], 
        time_interval: int
    ) -> None:
        """Handle buy order button callback."""
        section_index = self.buy_sections.index(section) + 1
        
        # 批量处理订单并收集结果
        successful_orders = []
        failed_orders = []
        
        for stock_data in stock_data_list:
            try:
                order_id = self.send_order_silent(
                    symbol=stock_data['symbol'],
                    price=stock_data['price'],
                    quantity=stock_data['quantity'],
                    direction=Direction.LONG
                )
                if order_id:
                    successful_orders.append({
                        'name': stock_data['name'],
                        'symbol': stock_data['symbol'],
                        'price': stock_data['price'],
                        'quantity': stock_data['quantity'],
                        'order_id': order_id
                    })
            except Exception as e:
                failed_orders.append({
                    'name': stock_data['name'],
                    'error': str(e)
                })
        
        # 显示批量结果
        self.show_batch_order_result("买入", section_index, successful_orders, failed_orders)

    def on_sell_add_clicked(self) -> None:
        """Handle sell add button click."""
        QtWidgets.QMessageBox.information(self, "功能", "卖出增加功能")
    
    def on_sell_order_callback(
        self, 
        section: TradingSectionWidget, 
        stock_data_list: List[Dict[str, Any]], 
        time_interval: int
    ) -> None:
        """Handle sell order button callback."""
        section_index = self.sell_sections.index(section) + 1
        
        # 批量处理订单并收集结果
        successful_orders = []
        failed_orders = []
        
        for stock_data in stock_data_list:
            try:
                order_id = self.send_order_silent(
                    symbol=stock_data['symbol'],
                    price=stock_data['price'],
                    quantity=stock_data['quantity'],
                    direction=Direction.SHORT
                )
                if order_id:
                    successful_orders.append({
                        'name': stock_data['name'],
                        'symbol': stock_data['symbol'],
                        'price': stock_data['price'],
                        'quantity': stock_data['quantity'],
                        'order_id': order_id
                    })
            except Exception as e:
                failed_orders.append({
                    'name': stock_data['name'],
                    'error': str(e)
                })
        
        # 显示批量结果
        self.show_batch_order_result("卖出", section_index, successful_orders, failed_orders)

    def register_event(self) -> None:
        """Register event handlers."""
        self.signal_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)

    def process_tick_event(self, event: Event) -> None:
        """Process tick data event to update prices."""
        tick: TickData = event.data
        
        # Update all buy sections prices
        for buy_section in self.buy_sections:
            buy_section.update_price(tick.symbol, str(tick.last_price))
            
        # Update all sell sections prices
        for sell_section in self.sell_sections:
            sell_section.update_price(tick.symbol, str(tick.last_price))



    def send_order(self, symbol: str, price: float, quantity: int, direction: Direction) -> None:
        """Send order to the trading system (with popup)."""
        order_id = self.send_order_silent(symbol, price, quantity, direction)
        if order_id:
            direction_text = "买入" if direction == Direction.LONG else "卖出"
            QtWidgets.QMessageBox.information(
                self, "委托成功", 
                f"{direction_text}订单已提交\n"
                f"股票: {symbol}\n"
                f"价格: {price}\n"
                f"数量: {quantity}\n"
                f"订单号: {order_id}"
            )
    
    def send_order_silent(self, symbol: str, price: float, quantity: int, direction: Direction) -> Optional[str]:
        """Send order to the trading system (without popup)."""
        if not symbol or price <= 0 or quantity <= 0:
            return None
        
        # Check if TCP orders are enabled
        if self.enable_tcp_orders:
            try:
                direction_text = "买入" if direction == Direction.LONG else "卖出"
                print(f"正在通过TCP发送{direction_text}订单: {symbol} {quantity}股 @ {price}元")
                
                # Create TCP client and send order directly
                with TcpOrderClient(self.tcp_host, self.tcp_port) as tcp_client:
                    success = tcp_client.make_order(
                        symbol=symbol,
                        direction=direction,
                        volume=quantity,
                        price=price,
                        exchange=Exchange.SSE  # Default to SSE
                    )
                    
                    if success:
                        order_id = f"TCP_{symbol}_{int(time.time())}"
                        print(f"✓ TCP订单发送成功: {order_id}")
                        return order_id
                    else:
                        print(f"✗ TCP订单发送失败: {symbol}")
                        return None
                        
            except Exception as e:
                print(f"✗ TCP订单异常: {e}")
                print("回退到网关方式发送订单...")
                # Fall back to gateway method if TCP fails
                pass
        
        # Use traditional gateway method (fallback or when TCP disabled)
        try:
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
                    print(f"✓ 网关订单发送成功: {vt_orderid}")
                return vt_orderid
            else:
                print("✗ 无可用网关")
                return None
        except Exception as e:
            print(f"✗ 网关订单发送失败: {e}")
            return None
    
    def show_batch_order_result(self, order_type: str, section_index: int, successful_orders: List[Dict], failed_orders: List[Dict]) -> None:
        """Show batch order results in a single message box."""
        message_parts = []
        
        if successful_orders:
            message_parts.append(f"=== {order_type}成功 ({len(successful_orders)}笔) ===")
            for order in successful_orders:
                message_parts.append(
                    f"✓ {order['name']} ({order['symbol']})\n"
                    f"   价格: {order['price']} | 数量: {order['quantity']}\n"
                    f"   订单号: {order['order_id']}"
                )
        
        if failed_orders:
            message_parts.append(f"\n=== {order_type}失败 ({len(failed_orders)}笔) ===")
            for order in failed_orders:
                message_parts.append(f"✗ {order['name']}: {order['error']}")
        
        if successful_orders or failed_orders:
            title = f"{order_type}区域{section_index} - 批量委托结果"
            message = "\n".join(message_parts)
            QtWidgets.QMessageBox.information(self, title, message)

    def on_buy_add_clicked(self) -> None:
        """Handle buy add button click."""
        QtWidgets.QMessageBox.information(self, "功能", "买入增加功能")



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