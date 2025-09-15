"""
Basic widgets for UI.
"""

import csv
import platform
from enum import Enum
from typing import cast, Any
from copy import copy
from tzlocal import get_localzone_name
from datetime import datetime
from importlib import metadata

from .qt import QtCore, QtGui, QtWidgets, Qt
from ..constant import Direction, Exchange, Offset, OrderType
from ..engine import MainEngine, Event, EventEngine
from ..event import (
    EVENT_QUOTE,
    EVENT_TICK,
    EVENT_TRADE,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_LOG
)
from ..object import (
    OrderRequest,
    SubscribeRequest,
    CancelRequest,
    ContractData,
    PositionData,
    OrderData,
    QuoteData,
    TickData
)
from ..utility import load_json, save_json, get_digits, ZoneInfo
from ..setting import SETTING_FILENAME, SETTINGS
from ..locale import _


COLOR_LONG = QtGui.QColor("red")
COLOR_SHORT = QtGui.QColor("green")
COLOR_BID = QtGui.QColor(255, 174, 201)
COLOR_ASK = QtGui.QColor(160, 255, 160)
COLOR_BLACK = QtGui.QColor("black")


class BaseCell(QtWidgets.QTableWidgetItem):
    """
    General cell used in tablewidgets.
    """

    def __init__(self, content: Any, data: Any) -> None:
        """"""
        super().__init__()

        self._text: str = ""
        self._data: Any = None

        self.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.set_content(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """
        Set text content.
        """
        self._text = str(content)
        self._data = data

        self.setText(self._text)

    def get_data(self) -> Any:
        """
        Get data object.
        """
        return self._data

    def __lt__(self, other: "BaseCell") -> bool:        # type: ignore
        """
        Sort by text content.
        """
        result: bool = self._text < other._text
        return result


class EnumCell(BaseCell):
    """
    Cell used for showing enum data.
    """

    def __init__(self, content: Enum, data: Any) -> None:
        """"""
        super().__init__(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """
        Set text using enum.constant.value.
        """
        if content:
            super().set_content(content.value, data)


class DirectionCell(EnumCell):
    """
    Cell used for showing direction data.
    """

    def __init__(self, content: Enum, data: Any) -> None:
        """"""
        super().__init__(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """
        Cell color is set according to direction.
        """
        super().set_content(content, data)

        if content is Direction.SHORT:
            self.setForeground(COLOR_SHORT)
        else:
            self.setForeground(COLOR_LONG)


class BidCell(BaseCell):
    """
    Cell used for showing bid price and volume.
    """

    def __init__(self, content: Any, data: Any) -> None:
        """"""
        super().__init__(content, data)

        self.setForeground(COLOR_BID)


class AskCell(BaseCell):
    """
    Cell used for showing ask price and volume.
    """

    def __init__(self, content: Any, data: Any) -> None:
        """"""
        super().__init__(content, data)

        self.setForeground(COLOR_ASK)


class PnlCell(BaseCell):
    """
    Cell used for showing pnl data.
    """

    def __init__(self, content: Any, data: Any) -> None:
        """"""
        super().__init__(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """
        Cell color is set based on whether pnl is
        positive or negative.
        """
        super().set_content(content, data)

        if str(content).startswith("-"):
            self.setForeground(COLOR_SHORT)
        else:
            self.setForeground(COLOR_LONG)


class TimeCell(BaseCell):
    """
    Cell used for showing time string from datetime object.
    """

    local_tz = ZoneInfo(get_localzone_name())

    def __init__(self, content: Any, data: Any) -> None:
        """"""
        super().__init__(content, data)

    def set_content(self, content: datetime | None, data: Any) -> None:
        """"""
        if content is None:
            return

        content = content.astimezone(self.local_tz)
        timestamp: str = content.strftime("%H:%M:%S")

        millisecond: int = int(content.microsecond / 1000)
        if millisecond:
            timestamp = f"{timestamp}.{millisecond}"
        else:
            timestamp = f"{timestamp}.000"

        self.setText(timestamp)
        self._data = data


class DateCell(BaseCell):
    """
    Cell used for showing date string from datetime object.
    """

    def __init__(self, content: Any, data: Any) -> None:
        """"""
        super().__init__(content, data)

    def set_content(self, content: Any, data: Any) -> None:
        """"""
        if content is None:
            return

        self.setText(content.strftime("%Y-%m-%d"))
        self._data = data


class MsgCell(BaseCell):
    """
    Cell used for showing msg data.
    """

    def __init__(self, content: str, data: Any) -> None:
        """"""
        super().__init__(content, data)
        self.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)


class BaseMonitor(QtWidgets.QTableWidget):
    """
    Monitor data update.
    """

    event_type: str = ""
    data_key: str = ""
    sorting: bool = False
    headers: dict = {}

    signal: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.cells: dict[str, dict] = {}

        self.init_ui()
        self.load_setting()
        self.register_event()

    def init_ui(self) -> None:
        """"""
        self.init_table()
        self.init_menu()

    def init_table(self) -> None:
        """
        Initialize table.
        """
        self.setColumnCount(len(self.headers))

        labels: list = [d["display"] for d in self.headers.values()]
        self.setHorizontalHeaderLabels(labels)

        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(self.sorting)

    def init_menu(self) -> None:
        """
        Create right click menu.
        """
        self.menu: QtWidgets.QMenu = QtWidgets.QMenu(self)

        resize_action: QtGui.QAction = QtGui.QAction(_("调整列宽"), self)
        resize_action.triggered.connect(self.resize_columns)
        self.menu.addAction(resize_action)

        save_action: QtGui.QAction = QtGui.QAction(_("保存数据"), self)
        save_action.triggered.connect(self.save_csv)
        self.menu.addAction(save_action)

    def register_event(self) -> None:
        """
        Register event handler into event engine.
        """
        if self.event_type:
            self.signal.connect(self.process_event)
            self.event_engine.register(self.event_type, self.signal.emit)

    def process_event(self, event: Event) -> None:
        """
        Process new data from event and update into table.
        """
        # Disable sorting to prevent unwanted error.
        if self.sorting:
            self.setSortingEnabled(False)

        # Update data into table.
        data = event.data

        if not self.data_key:
            self.insert_new_row(data)
        else:
            key: str = data.__getattribute__(self.data_key)

            if key in self.cells:
                self.update_old_row(data)
            else:
                self.insert_new_row(data)

        # Enable sorting
        if self.sorting:
            self.setSortingEnabled(True)

    def insert_new_row(self, data: Any) -> None:
        """
        Insert a new row at the top of table.
        """
        self.insertRow(0)

        row_cells: dict = {}
        for column, header in enumerate(self.headers.keys()):
            setting: dict = self.headers[header]

            content = data.__getattribute__(header)
            cell: QtWidgets.QTableWidgetItem = setting["cell"](content, data)
            self.setItem(0, column, cell)

            if setting["update"]:
                row_cells[header] = cell

        if self.data_key:
            key: str = data.__getattribute__(self.data_key)
            self.cells[key] = row_cells

    def update_old_row(self, data: Any) -> None:
        """
        Update an old row in table.
        """
        key: str = data.__getattribute__(self.data_key)
        row_cells = self.cells[key]

        for header, cell in row_cells.items():
            content = data.__getattribute__(header)
            cell.set_content(content, data)

    def resize_columns(self) -> None:
        """
        Resize all columns according to contents.
        """
        self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def save_csv(self) -> None:
        """
        Save table data into a csv file
        """
        path, __ = QtWidgets.QFileDialog.getSaveFileName(
            self, _("保存数据"), "", "CSV(*.csv)")

        if not path:
            return

        with open(path, "w") as f:
            writer = csv.writer(f, lineterminator="\n")

            headers: list = [d["display"] for d in self.headers.values()]
            writer.writerow(headers)

            for row in range(self.rowCount()):
                if self.isRowHidden(row):
                    continue

                row_data: list = []
                for column in range(self.columnCount()):
                    item: QtWidgets.QTableWidgetItem | None = self.item(row, column)
                    if item:
                        row_data.append(str(item.text()))
                    else:
                        row_data.append("")
                writer.writerow(row_data)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())

    def save_setting(self) -> None:
        """"""
        settings: QtCore.QSettings = QtCore.QSettings(self.__class__.__name__, "custom")
        settings.setValue("column_state", self.horizontalHeader().saveState())

    def load_setting(self) -> None:
        """"""
        settings: QtCore.QSettings = QtCore.QSettings(self.__class__.__name__, "custom")
        column_state = settings.value("column_state")

        if isinstance(column_state, QtCore.QByteArray):
            self.horizontalHeader().restoreState(column_state)
            self.horizontalHeader().setSortIndicator(-1, QtCore.Qt.SortOrder.AscendingOrder)


class TickMonitor(BaseMonitor):
    """
    Monitor for tick data.
    """

    event_type: str = EVENT_TICK
    data_key: str = "vt_symbol"
    sorting: bool = True

    headers: dict = {
        "symbol": {"display": _("代码"), "cell": BaseCell, "update": False},
        "exchange": {"display": _("交易所"), "cell": EnumCell, "update": False},
        "name": {"display": _("名称"), "cell": BaseCell, "update": True},
        "last_price": {"display": _("最新价"), "cell": BaseCell, "update": True},
        "volume": {"display": _("成交量"), "cell": BaseCell, "update": True},
        "open_price": {"display": _("开盘价"), "cell": BaseCell, "update": True},
        "high_price": {"display": _("最高价"), "cell": BaseCell, "update": True},
        "low_price": {"display": _("最低价"), "cell": BaseCell, "update": True},
        "bid_price_1": {"display": _("买1价"), "cell": BidCell, "update": True},
        "bid_volume_1": {"display": _("买1量"), "cell": BidCell, "update": True},
        "ask_price_1": {"display": _("卖1价"), "cell": AskCell, "update": True},
        "ask_volume_1": {"display": _("卖1量"), "cell": AskCell, "update": True},
        "datetime": {"display": _("时间"), "cell": TimeCell, "update": True},
        "gateway_name": {"display": _("接口"), "cell": BaseCell, "update": False},
    }


class LogMonitor(BaseMonitor):
    """
    Monitor for log data.
    """

    event_type: str = EVENT_LOG
    data_key: str = ""
    sorting: bool = False

    headers: dict = {
        "time": {"display": _("时间"), "cell": TimeCell, "update": False},
        "msg": {"display": _("信息"), "cell": MsgCell, "update": False},
        "gateway_name": {"display": _("接口"), "cell": BaseCell, "update": False},
    }


class TradeMonitor(BaseMonitor):
    """
    Monitor for trade data.
    """

    event_type: str = EVENT_TRADE
    data_key: str = ""
    sorting: bool = True

    headers: dict = {
        "tradeid": {"display": _("成交号"), "cell": BaseCell, "update": False},
        "orderid": {"display": _("委托号"), "cell": BaseCell, "update": False},
        "symbol": {"display": _("代码"), "cell": BaseCell, "update": False},
        "exchange": {"display": _("交易所"), "cell": EnumCell, "update": False},
        "direction": {"display": _("方向"), "cell": DirectionCell, "update": False},
        "offset": {"display": _("开平"), "cell": EnumCell, "update": False},
        "price": {"display": _("价格"), "cell": BaseCell, "update": False},
        "volume": {"display": _("数量"), "cell": BaseCell, "update": False},
        "datetime": {"display": _("时间"), "cell": TimeCell, "update": False},
        "gateway_name": {"display": _("接口"), "cell": BaseCell, "update": False},
    }


class OrderMonitor(BaseMonitor):
    """
    Monitor for order data.
    """

    event_type: str = EVENT_ORDER
    data_key: str = "vt_orderid"
    sorting: bool = True

    headers: dict = {
        "orderid": {"display": _("委托号"), "cell": BaseCell, "update": False},
        "reference": {"display": _("来源"), "cell": BaseCell, "update": False},
        "symbol": {"display": _("代码"), "cell": BaseCell, "update": False},
        "exchange": {"display": _("交易所"), "cell": EnumCell, "update": False},
        "type": {"display": _("类型"), "cell": EnumCell, "update": False},
        "direction": {"display": _("方向"), "cell": DirectionCell, "update": False},
        "offset": {"display": _("开平"), "cell": EnumCell, "update": False},
        "price": {"display": _("价格"), "cell": BaseCell, "update": False},
        "volume": {"display": _("总数量"), "cell": BaseCell, "update": True},
        "traded": {"display": _("已成交"), "cell": BaseCell, "update": True},
        "status": {"display": _("状态"), "cell": EnumCell, "update": True},
        "datetime": {"display": _("时间"), "cell": TimeCell, "update": True},
        "gateway_name": {"display": _("接口"), "cell": BaseCell, "update": False},
    }

    def init_ui(self) -> None:
        """
        Connect signal.
        """
        super().init_ui()

        self.setToolTip(_("双击单元格撤单"))
        self.itemDoubleClicked.connect(self.cancel_order)

    def cancel_order(self, cell: BaseCell) -> None:
        """
        Cancel order if cell double clicked.
        """
        order: OrderData = cell.get_data()
        req: CancelRequest = order.create_cancel_request()
        self.main_engine.cancel_order(req, order.gateway_name)


class PositionMonitor(BaseMonitor):
    """
    Monitor for position data.
    """

    event_type: str = EVENT_POSITION
    data_key: str = "vt_positionid"
    sorting: bool = True

    headers: dict = {
        "symbol": {"display": _("代码"), "cell": BaseCell, "update": False},
        "exchange": {"display": _("交易所"), "cell": EnumCell, "update": False},
        "direction": {"display": _("方向"), "cell": DirectionCell, "update": False},
        "volume": {"display": _("数量"), "cell": BaseCell, "update": True},
        "yd_volume": {"display": _("昨仓"), "cell": BaseCell, "update": True},
        "frozen": {"display": _("冻结"), "cell": BaseCell, "update": True},
        "price": {"display": _("均价"), "cell": BaseCell, "update": True},
        "pnl": {"display": _("盈亏"), "cell": PnlCell, "update": True},
        "gateway_name": {"display": _("接口"), "cell": BaseCell, "update": False},
    }


class AccountMonitor(BaseMonitor):
    """
    Monitor for account data.
    """

    event_type: str = EVENT_ACCOUNT
    data_key: str = "vt_accountid"
    sorting: bool = True

    headers: dict = {
        "accountid": {"display": _("账号"), "cell": BaseCell, "update": False},
        "balance": {"display": _("余额"), "cell": BaseCell, "update": True},
        "frozen": {"display": _("冻结"), "cell": BaseCell, "update": True},
        "available": {"display": _("可用"), "cell": BaseCell, "update": True},
        "gateway_name": {"display": _("接口"), "cell": BaseCell, "update": False},
    }


class QuoteMonitor(BaseMonitor):
    """
    Monitor for quote data.
    """

    event_type: str = EVENT_QUOTE
    data_key: str = "vt_quoteid"
    sorting: bool = True

    headers: dict = {
        "quoteid": {"display": _("报价号"), "cell": BaseCell, "update": False},
        "reference": {"display": _("来源"), "cell": BaseCell, "update": False},
        "symbol": {"display": _("代码"), "cell": BaseCell, "update": False},
        "exchange": {"display": _("交易所"), "cell": EnumCell, "update": False},
        "bid_offset": {"display": _("买开平"), "cell": EnumCell, "update": False},
        "bid_volume": {"display": _("买量"), "cell": BidCell, "update": False},
        "bid_price": {"display": _("买价"), "cell": BidCell, "update": False},
        "ask_price": {"display": _("卖价"), "cell": AskCell, "update": False},
        "ask_volume": {"display": _("卖量"), "cell": AskCell, "update": False},
        "ask_offset": {"display": _("卖开平"), "cell": EnumCell, "update": False},
        "status": {"display": _("状态"), "cell": EnumCell, "update": True},
        "datetime": {"display": _("时间"), "cell": TimeCell, "update": True},
        "gateway_name": {"display": _("接口"), "cell": BaseCell, "update": False},
    }

    def init_ui(self) -> None:
        """
        Connect signal.
        """
        super().init_ui()

        self.setToolTip(_("双击单元格撤销报价"))
        self.itemDoubleClicked.connect(self.cancel_quote)

    def cancel_quote(self, cell: BaseCell) -> None:
        """
        Cancel quote if cell double clicked.
        """
        quote: QuoteData = cell.get_data()
        req: CancelRequest = quote.create_cancel_request()
        self.main_engine.cancel_quote(req, quote.gateway_name)


class ConnectDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self, main_engine: MainEngine, gateway_name: str) -> None:
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.gateway_name: str = gateway_name
        self.filename: str = f"connect_{gateway_name.lower()}.json"

        self.widgets: dict[str, tuple[QtWidgets.QWidget, type]] = {}

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle(_("连接{}").format(self.gateway_name))

        # Default setting provides field name, field data type and field default value.
        default_setting: dict | None = self.main_engine.get_default_setting(self.gateway_name)

        # Saved setting provides field data used last time.
        loaded_setting: dict = load_json(self.filename)

        # Initialize line edits and form layout based on setting.
        form: QtWidgets.QFormLayout = QtWidgets.QFormLayout()

        if default_setting:
            for field_name, field_value in default_setting.items():
                field_type: type = type(field_value)

                if field_type is list:
                    combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
                    combo.addItems(field_value)

                    if field_name in loaded_setting:
                        saved_value = loaded_setting[field_name]
                        ix: int = combo.findText(saved_value)
                        combo.setCurrentIndex(ix)

                    form.addRow(f"{field_name} <{field_type.__name__}>", combo)
                    self.widgets[field_name] = (combo, field_type)
                else:
                    line: QtWidgets.QLineEdit = QtWidgets.QLineEdit(str(field_value))

                    if field_name in loaded_setting:
                        saved_value = loaded_setting[field_name]
                        line.setText(str(saved_value))

                    if _("密码") in field_name:
                        line.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

                    if field_type is int:
                        validator: QtGui.QIntValidator = QtGui.QIntValidator()
                        line.setValidator(validator)

                    form.addRow(f"{field_name} <{field_type.__name__}>", line)
                    self.widgets[field_name] = (line, field_type)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton(_("连接"))
        button.clicked.connect(self.connect_gateway)
        form.addRow(button)

        self.setLayout(form)

    def connect_gateway(self) -> None:
        """
        Get setting value from line edits and connect the gateway.
        """
        setting: dict = {}

        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            if field_type is list:
                combo: QtWidgets.QComboBox = cast(QtWidgets.QComboBox, widget)
                field_value = str(combo.currentText())
            else:
                line: QtWidgets.QLineEdit = cast(QtWidgets.QLineEdit, widget)
                try:
                    field_value = field_type(line.text())
                except ValueError:
                    field_value = field_type()
            setting[field_name] = field_value

        save_json(self.filename, setting)

        self.main_engine.connect(setting, self.gateway_name)
        self.accept()


class TradingWidget(QtWidgets.QWidget):
    """
    General manual trading widget.
    """

    signal_tick: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.vt_symbol: str = ""
        self.price_digits: int = 0

        self.init_ui()
        self.register_event()

    def init_ui(self) -> None:
        """"""
        self.setFixedWidth(300)

        # Trading function area
        exchanges: list[Exchange] = self.main_engine.get_all_exchanges()
        self.exchange_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.exchange_combo.addItems([exchange.value for exchange in exchanges])

        self.symbol_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.symbol_line.returnPressed.connect(self.set_vt_symbol)

        self.name_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.name_line.setReadOnly(True)

        self.direction_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.direction_combo.addItems(
            [Direction.LONG.value, Direction.SHORT.value])

        self.offset_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.offset_combo.addItems([offset.value for offset in Offset])

        self.order_type_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.order_type_combo.addItems(
            [order_type.value for order_type in OrderType])

        double_validator: QtGui.QDoubleValidator = QtGui.QDoubleValidator()
        double_validator.setBottom(0)

        self.price_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.price_line.setValidator(double_validator)

        self.volume_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.volume_line.setValidator(double_validator)

        self.gateway_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.gateway_combo.addItems(self.main_engine.get_all_gateway_names())

        self.price_check: QtWidgets.QCheckBox = QtWidgets.QCheckBox()
        self.price_check.setToolTip(_("设置价格随行情更新"))

        send_button: QtWidgets.QPushButton = QtWidgets.QPushButton(_("委托"))
        send_button.clicked.connect(self.send_order)

        cancel_button: QtWidgets.QPushButton = QtWidgets.QPushButton(_("全撤"))
        cancel_button.clicked.connect(self.cancel_all)

        grid: QtWidgets.QGridLayout = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel(_("交易所")), 0, 0)
        grid.addWidget(QtWidgets.QLabel(_("代码")), 1, 0)
        grid.addWidget(QtWidgets.QLabel(_("名称")), 2, 0)
        grid.addWidget(QtWidgets.QLabel(_("方向")), 3, 0)
        grid.addWidget(QtWidgets.QLabel(_("开平")), 4, 0)
        grid.addWidget(QtWidgets.QLabel(_("类型")), 5, 0)
        grid.addWidget(QtWidgets.QLabel(_("价格")), 6, 0)
        grid.addWidget(QtWidgets.QLabel(_("数量")), 7, 0)
        grid.addWidget(QtWidgets.QLabel(_("接口")), 8, 0)
        grid.addWidget(self.exchange_combo, 0, 1, 1, 2)
        grid.addWidget(self.symbol_line, 1, 1, 1, 2)
        grid.addWidget(self.name_line, 2, 1, 1, 2)
        grid.addWidget(self.direction_combo, 3, 1, 1, 2)
        grid.addWidget(self.offset_combo, 4, 1, 1, 2)
        grid.addWidget(self.order_type_combo, 5, 1, 1, 2)
        grid.addWidget(self.price_line, 6, 1, 1, 1)
        grid.addWidget(self.price_check, 6, 2, 1, 1)
        grid.addWidget(self.volume_line, 7, 1, 1, 2)
        grid.addWidget(self.gateway_combo, 8, 1, 1, 2)
        grid.addWidget(send_button, 9, 0, 1, 3)
        grid.addWidget(cancel_button, 10, 0, 1, 3)

        # Market depth display area
        bid_color: str = "rgb(255,174,201)"
        ask_color: str = "rgb(160,255,160)"

        self.bp1_label: QtWidgets.QLabel = self.create_label(bid_color)
        self.bp2_label: QtWidgets.QLabel = self.create_label(bid_color)
        self.bp3_label: QtWidgets.QLabel = self.create_label(bid_color)
        self.bp4_label: QtWidgets.QLabel = self.create_label(bid_color)
        self.bp5_label: QtWidgets.QLabel = self.create_label(bid_color)

        self.bv1_label: QtWidgets.QLabel = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.bv2_label: QtWidgets.QLabel = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.bv3_label: QtWidgets.QLabel = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.bv4_label: QtWidgets.QLabel = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.bv5_label: QtWidgets.QLabel = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self.ap1_label: QtWidgets.QLabel = self.create_label(ask_color)
        self.ap2_label: QtWidgets.QLabel = self.create_label(ask_color)
        self.ap3_label: QtWidgets.QLabel = self.create_label(ask_color)
        self.ap4_label: QtWidgets.QLabel = self.create_label(ask_color)
        self.ap5_label: QtWidgets.QLabel = self.create_label(ask_color)

        self.av1_label: QtWidgets.QLabel = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.av2_label: QtWidgets.QLabel = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.av3_label: QtWidgets.QLabel = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.av4_label: QtWidgets.QLabel = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.av5_label: QtWidgets.QLabel = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self.lp_label: QtWidgets.QLabel = self.create_label()
        self.return_label: QtWidgets.QLabel = self.create_label(alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        form: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        form.addRow(self.ap5_label, self.av5_label)
        form.addRow(self.ap4_label, self.av4_label)
        form.addRow(self.ap3_label, self.av3_label)
        form.addRow(self.ap2_label, self.av2_label)
        form.addRow(self.ap1_label, self.av1_label)
        form.addRow(self.lp_label, self.return_label)
        form.addRow(self.bp1_label, self.bv1_label)
        form.addRow(self.bp2_label, self.bv2_label)
        form.addRow(self.bp3_label, self.bv3_label)
        form.addRow(self.bp4_label, self.bv4_label)
        form.addRow(self.bp5_label, self.bv5_label)

        # Overall layout
        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(form)
        self.setLayout(vbox)

    def create_label(
        self,
        color: str = "",
        alignment: int = QtCore.Qt.AlignmentFlag.AlignLeft
    ) -> QtWidgets.QLabel:
        """
        Create label with certain font color.
        """
        label: QtWidgets.QLabel = QtWidgets.QLabel()
        if color:
            label.setStyleSheet(f"color:{color}")
        label.setAlignment(Qt.AlignmentFlag(alignment))
        return label

    def register_event(self) -> None:
        """"""
        self.signal_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)

    def process_tick_event(self, event: Event) -> None:
        """"""
        tick: TickData = event.data
        if tick.vt_symbol != self.vt_symbol:
            return

        price_digits: int = self.price_digits

        self.lp_label.setText(f"{tick.last_price:.{price_digits}f}")
        self.bp1_label.setText(f"{tick.bid_price_1:.{price_digits}f}")
        self.bv1_label.setText(str(tick.bid_volume_1))
        self.ap1_label.setText(f"{tick.ask_price_1:.{price_digits}f}")
        self.av1_label.setText(str(tick.ask_volume_1))

        if tick.pre_close:
            r: float = (tick.last_price / tick.pre_close - 1) * 100
            self.return_label.setText(f"{r:.2f}%")

        if tick.bid_price_2:
            self.bp2_label.setText(f"{tick.bid_price_2:.{price_digits}f}")
            self.bv2_label.setText(str(tick.bid_volume_2))
            self.ap2_label.setText(f"{tick.ask_price_2:.{price_digits}f}")
            self.av2_label.setText(str(tick.ask_volume_2))

            self.bp3_label.setText(f"{tick.bid_price_3:.{price_digits}f}")
            self.bv3_label.setText(str(tick.bid_volume_3))
            self.ap3_label.setText(f"{tick.ask_price_3:.{price_digits}f}")
            self.av3_label.setText(str(tick.ask_volume_3))

            self.bp4_label.setText(f"{tick.bid_price_4:.{price_digits}f}")
            self.bv4_label.setText(str(tick.bid_volume_4))
            self.ap4_label.setText(f"{tick.ask_price_4:.{price_digits}f}")
            self.av4_label.setText(str(tick.ask_volume_4))

            self.bp5_label.setText(f"{tick.bid_price_5:.{price_digits}f}")
            self.bv5_label.setText(str(tick.bid_volume_5))
            self.ap5_label.setText(f"{tick.ask_price_5:.{price_digits}f}")
            self.av5_label.setText(str(tick.ask_volume_5))

        if self.price_check.isChecked():
            self.price_line.setText(f"{tick.last_price:.{price_digits}f}")

    def set_vt_symbol(self) -> None:
        """
        Set the tick depth data to monitor by vt_symbol.
        """
        symbol: str = str(self.symbol_line.text())
        if not symbol:
            return

        # Generate vt_symbol from symbol and exchange
        exchange_value: str = str(self.exchange_combo.currentText())
        vt_symbol: str = f"{symbol}.{exchange_value}"

        if vt_symbol == self.vt_symbol:
            return
        self.vt_symbol = vt_symbol

        # Update name line widget and clear all labels
        contract: ContractData | None = self.main_engine.get_contract(vt_symbol)
        if not contract:
            self.name_line.setText("")
            gateway_name: str = self.gateway_combo.currentText()
        else:
            self.name_line.setText(contract.name)
            gateway_name = contract.gateway_name

            # Update gateway combo box.
            ix: int = self.gateway_combo.findText(gateway_name)
            self.gateway_combo.setCurrentIndex(ix)

            # Update price digits
            self.price_digits = get_digits(contract.pricetick)

        self.clear_label_text()
        self.volume_line.setText("")
        self.price_line.setText("")

        # Subscribe tick data
        req: SubscribeRequest = SubscribeRequest(
            symbol=symbol, exchange=Exchange(exchange_value)
        )

        self.main_engine.subscribe(req, gateway_name)

    def clear_label_text(self) -> None:
        """
        Clear text on all labels.
        """
        self.lp_label.setText("")
        self.return_label.setText("")

        self.bv1_label.setText("")
        self.bv2_label.setText("")
        self.bv3_label.setText("")
        self.bv4_label.setText("")
        self.bv5_label.setText("")

        self.av1_label.setText("")
        self.av2_label.setText("")
        self.av3_label.setText("")
        self.av4_label.setText("")
        self.av5_label.setText("")

        self.bp1_label.setText("")
        self.bp2_label.setText("")
        self.bp3_label.setText("")
        self.bp4_label.setText("")
        self.bp5_label.setText("")

        self.ap1_label.setText("")
        self.ap2_label.setText("")
        self.ap3_label.setText("")
        self.ap4_label.setText("")
        self.ap5_label.setText("")

    def send_order(self) -> None:
        """
        Send new order manually.
        """
        symbol: str = str(self.symbol_line.text())
        if not symbol:
            QtWidgets.QMessageBox.critical(self, _("委托失败"), _("请输入合约代码"))
            return

        volume_text: str = str(self.volume_line.text())
        if not volume_text:
            QtWidgets.QMessageBox.critical(self, _("委托失败"), _("请输入委托数量"))
            return
        volume: float = float(volume_text)

        price_text: str = str(self.price_line.text())
        if not price_text:
            price: float = 0
        else:
            price = float(price_text)

        req: OrderRequest = OrderRequest(
            symbol=symbol,
            exchange=Exchange(str(self.exchange_combo.currentText())),
            direction=Direction(str(self.direction_combo.currentText())),
            type=OrderType(str(self.order_type_combo.currentText())),
            volume=volume,
            price=price,
            offset=Offset(str(self.offset_combo.currentText())),
            reference="ManualTrading"
        )

        gateway_name: str = str(self.gateway_combo.currentText())

        self.main_engine.send_order(req, gateway_name)

    def cancel_all(self) -> None:
        """
        Cancel all active orders.
        """
        order_list: list[OrderData] = self.main_engine.get_all_active_orders()
        for order in order_list:
            req: CancelRequest = order.create_cancel_request()
            self.main_engine.cancel_order(req, order.gateway_name)

    def update_with_cell(self, cell: BaseCell) -> None:
        """"""
        data = cell.get_data()

        self.symbol_line.setText(data.symbol)
        self.exchange_combo.setCurrentIndex(
            self.exchange_combo.findText(data.exchange.value)
        )

        self.set_vt_symbol()

        if isinstance(data, PositionData):
            if data.direction == Direction.SHORT:
                direction: Direction = Direction.LONG
            elif data.direction == Direction.LONG:
                direction = Direction.SHORT
            else:       # Net position mode
                if data.volume > 0:
                    direction = Direction.SHORT
                else:
                    direction = Direction.LONG

            self.direction_combo.setCurrentIndex(
                self.direction_combo.findText(direction.value)
            )
            self.offset_combo.setCurrentIndex(
                self.offset_combo.findText(Offset.CLOSE.value)
            )
            self.volume_line.setText(str(abs(data.volume)))


class ActiveOrderMonitor(OrderMonitor):
    """
    Monitor which shows active order only.
    """

    def process_event(self, event: Event) -> None:
        """
        Hides the row if order is not active.
        """
        super().process_event(event)

        order: OrderData = event.data
        row_cells: dict = self.cells[order.vt_orderid]
        row: int = self.row(row_cells["volume"])

        if order.is_active():
            self.showRow(row)
        else:
            self.hideRow(row)


class StockTradingWidget(QtWidgets.QWidget):
    """
    Stock trading widget based on trader.ui layout.
    """
    
    signal_tick: QtCore.Signal = QtCore.Signal(Event)
    signal_position: QtCore.Signal = QtCore.Signal(Event)
    signal_account: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__()
        
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        
        self.vt_symbol: str = ""
        self.price_digits: int = 2
        self.available_balance: float = 0
        self.position_volume: int = 0
        
        self.init_ui()
        self.register_event()
    
    def init_ui(self) -> None:
        """Initialize user interface."""
        self.setFixedSize(400, 380)  # 宽度减少到400，高度恢复到380
        self.setWindowTitle("股票交易")
        self.setWindowFlags(QtCore.Qt.WindowType.Window)  # 设置为独立窗口
        
        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.setGeometry(0, 0, 400, 380)  # 调整tab widget尺寸
        
        # Create trading tab
        self.trading_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(self.trading_tab, "交易")
        
        # Create algorithm tab (placeholder)
        self.algo_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(self.algo_tab, "算法")
        
        self.init_trading_tab()
    
    def init_trading_tab(self) -> None:
        """Initialize trading tab interface."""
        # Symbol input
        self.symbol_edit = QtWidgets.QLineEdit()
        self.symbol_edit.setGeometry(50, 10, 130, 21)
        self.symbol_edit.setText("128131    崇达转2")
        self.symbol_edit.returnPressed.connect(self.on_symbol_changed)
        
        # Order type combo
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.setGeometry(50, 40, 130, 24)
        self.type_combo.addItems(["限价", "其他"])
        
        # Price input
        self.price_spinbox = QtWidgets.QDoubleSpinBox()
        self.price_spinbox.setGeometry(50, 70, 130, 23)
        self.price_spinbox.setDecimals(3)
        self.price_spinbox.setMaximum(9999.999)
        self.price_spinbox.setSingleStep(0.001)
        self.price_spinbox.setValue(166.695)
        
        # Volume combo
        self.volume_combo = QtWidgets.QComboBox()
        self.volume_combo.setGeometry(50, 110, 91, 24)
        self.volume_combo.setEditable(True)
        
        # Position fraction radio buttons with better spacing
        self.radio_half = QtWidgets.QRadioButton("1/2")
        self.radio_half.setGeometry(10, 150, 50, 22)  # 增加宽度和高度
        self.radio_half.setStyleSheet("font-size: 12px;")
        self.radio_half.clicked.connect(lambda: self.on_fraction_selected(0.5))
        
        self.radio_third = QtWidgets.QRadioButton("1/3")
        self.radio_third.setGeometry(70, 150, 50, 22)
        self.radio_third.setStyleSheet("font-size: 12px;")
        self.radio_third.clicked.connect(lambda: self.on_fraction_selected(1.0/3))
        
        self.radio_quarter = QtWidgets.QRadioButton("1/4")
        self.radio_quarter.setGeometry(130, 150, 50, 22)
        self.radio_quarter.setStyleSheet("font-size: 12px;")
        self.radio_quarter.clicked.connect(lambda: self.on_fraction_selected(0.25))
        
        self.radio_fifth = QtWidgets.QRadioButton("1/5")
        self.radio_fifth.setGeometry(190, 150, 50, 22)
        self.radio_fifth.setStyleSheet("font-size: 12px;")
        self.radio_fifth.clicked.connect(lambda: self.on_fraction_selected(0.2))
        
        # High Touch order checkbox with better text
        self.high_touch_checkbox = QtWidgets.QCheckBox("High Touch单")  # 简化文字
        self.high_touch_checkbox.setGeometry(10, 180, 120, 22)  # 调整尺寸
        self.high_touch_checkbox.setStyleSheet("font-size: 12px;")
        
        # Auto cancel checkbox and spinbox
        self.auto_cancel_checkbox = QtWidgets.QCheckBox("秒后自动撤单")
        self.auto_cancel_checkbox.setGeometry(80, 210, 140, 22)  # 增加宽度
        self.auto_cancel_checkbox.setStyleSheet("font-size: 12px;")
        
        self.cancel_spinbox = QtWidgets.QSpinBox()
        self.cancel_spinbox.setGeometry(10, 210, 61, 23)
        self.cancel_spinbox.setValue(3)
        
        # Trading buttons - first row: 买入 和 卖出
        self.buy_button = QtWidgets.QPushButton("买入")
        self.buy_button.setGeometry(10, 250, 120, 35)  # 增加宽度以更好地利用空间
        self.buy_button.setStyleSheet("QPushButton { background-color: rgb(170, 0, 0); color: white; font-size: 12px; }")
        self.buy_button.clicked.connect(self.on_buy_clicked)
        
        self.sell_button = QtWidgets.QPushButton("卖出")
        self.sell_button.setGeometry(140, 250, 120, 35)  # 增加宽度并调整位置
        self.sell_button.setStyleSheet("QPushButton { background-color: rgb(0, 85, 0); color: white; font-size: 12px; }")
        self.sell_button.clicked.connect(self.on_sell_clicked)
        
        # Trading buttons - second row: 卖空 和 平空
        self.sell_short_button = QtWidgets.QPushButton("卖空")
        self.sell_short_button.setGeometry(10, 295, 120, 35)  # 放在买入按钮下方
        self.sell_short_button.setStyleSheet("QPushButton { background-color: rgb(0, 85, 0); color: white; font-size: 12px; }")
        self.sell_short_button.clicked.connect(self.on_sell_short_clicked)
        
        self.cover_button = QtWidgets.QPushButton("平空")
        self.cover_button.setGeometry(140, 295, 120, 35)  # 放在卖出按钮下方
        self.cover_button.setStyleSheet("QPushButton { background-color: rgb(170, 0, 0); color: white; font-size: 12px; }")
        self.cover_button.clicked.connect(self.on_cover_clicked)
        
        # Labels with optimized size and font
        label_symbol = QtWidgets.QLabel("代码")
        label_symbol.setGeometry(10, 10, 40, 18)  # 增加宽度和高度
        label_symbol.setStyleSheet("font-size: 12px;")  # 恢复到12px
        
        label_type = QtWidgets.QLabel("类型")
        label_type.setGeometry(10, 40, 40, 18)
        label_type.setStyleSheet("font-size: 12px;")
        
        label_price = QtWidgets.QLabel("价格")
        label_price.setGeometry(10, 70, 40, 18)
        label_price.setStyleSheet("font-size: 12px;")
        
        label_volume = QtWidgets.QLabel("数量")
        label_volume.setGeometry(10, 110, 40, 18)
        label_volume.setStyleSheet("color: rgb(85, 170, 127); font-size: 12px;")
        
        label_shares = QtWidgets.QLabel("股")
        label_shares.setGeometry(150, 110, 25, 18)
        label_shares.setStyleSheet("font-size: 12px;")
        
        label_max_sell = QtWidgets.QLabel("最大可卖:")
        label_max_sell.setGeometry(200, 10, 80, 18)  # 调整位置避免重叠
        label_max_sell.setStyleSheet("font-size: 12px;")
        
        label_max_buy = QtWidgets.QLabel("最大可买(参考):")
        label_max_buy.setGeometry(200, 50, 120, 18)  # 放在最大可卖下面
        label_max_buy.setStyleSheet("font-size: 12px;")
        
        # Position and balance display labels - 放在对应提示文字下面
        self.max_sell_label = QtWidgets.QLabel("6,020")
        self.max_sell_label.setGeometry(200, 30, 80, 18)  # 放在"最大可卖"下面
        self.max_sell_label.setStyleSheet("color: rgb(85, 170, 127); font-size: 12px; font-weight: bold;")
        
        self.max_buy_label = QtWidgets.QLabel("170,430")
        self.max_buy_label.setGeometry(200, 70, 120, 18)  # 放在"最大可买(参考)"下面
        self.max_buy_label.setStyleSheet("color: rgb(85, 170, 127); font-size: 12px; font-weight: bold;")
        
        # Add all widgets to trading tab
        widgets = [
            self.symbol_edit, self.type_combo, self.price_spinbox, self.volume_combo,
            self.radio_half, self.radio_third, self.radio_quarter, self.radio_fifth,
            self.high_touch_checkbox, self.auto_cancel_checkbox, self.cancel_spinbox,
            self.buy_button, self.sell_button, self.sell_short_button, self.cover_button,
            label_symbol, label_type, label_price, label_volume, label_shares,
            label_max_sell, label_max_buy, self.max_sell_label, self.max_buy_label
        ]
        
        for widget in widgets:
            widget.setParent(self.trading_tab)
    
    def register_event(self) -> None:
        """Register event handlers."""
        self.signal_tick.connect(self.process_tick_event)
        self.signal_position.connect(self.process_position_event)
        self.signal_account.connect(self.process_account_event)
        
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)
        self.event_engine.register(EVENT_POSITION, self.signal_position.emit)
        self.event_engine.register(EVENT_ACCOUNT, self.signal_account.emit)
    
    def process_tick_event(self, event: Event) -> None:
        """Process tick data event."""
        tick: TickData = event.data
        if tick.vt_symbol != self.vt_symbol:
            return
        
        # Update price if needed
        if self.price_spinbox.value() == 0:
            self.price_spinbox.setValue(tick.last_price)
    
    def process_position_event(self, event: Event) -> None:
        """Process position data event."""
        position: PositionData = event.data
        if position.vt_symbol != self.vt_symbol:
            return
        
        self.position_volume = int(position.volume)
        self.max_sell_label.setText(f"{self.position_volume:,}")
    
    def process_account_event(self, event: Event) -> None:
        """Process account data event."""
        # Update available balance and max buy calculation
        # This is a simplified implementation
        pass
    
    def on_symbol_changed(self) -> None:
        """Handle symbol input change."""
        symbol_text = self.symbol_edit.text().strip()
        if not symbol_text:
            return
        
        # Extract symbol code (first part before space)
        symbol = symbol_text.split()[0]
        self.vt_symbol = f"{symbol}.SSE"  # Assume SSE exchange for stocks
        
        # Subscribe to tick data
        req = SubscribeRequest(symbol=symbol, exchange=Exchange.SSE)
        gateway_names = self.main_engine.get_all_gateway_names()
        if gateway_names:
            self.main_engine.subscribe(req, gateway_names[0])
    
    def on_fraction_selected(self, fraction: float) -> None:
        """Handle position fraction selection."""
        if self.position_volume > 0:
            volume = int(self.position_volume * fraction)
            # Round to nearest 100 shares
            volume = (volume // 100) * 100
            self.volume_combo.setCurrentText(str(volume))
    
    def get_order_volume(self) -> int:
        """Get order volume from input."""
        volume_text = self.volume_combo.currentText().strip()
        if not volume_text:
            return 0
        try:
            return int(float(volume_text))
        except ValueError:
            return 0
    
    def send_order(self, direction: Direction) -> None:
        """Send order with specified direction."""
        symbol_text = self.symbol_edit.text().strip()
        if not symbol_text:
            QtWidgets.QMessageBox.warning(self, "错误", "请输入股票代码")
            return
        
        symbol = symbol_text.split()[0]
        volume = self.get_order_volume()
        if volume <= 0:
            QtWidgets.QMessageBox.warning(self, "错误", "请输入有效的交易数量")
            return
        
        price = self.price_spinbox.value()
        if price <= 0:
            QtWidgets.QMessageBox.warning(self, "错误", "请输入有效的价格")
            return
        
        # Create order request
        req = OrderRequest(
            symbol=symbol,
            exchange=Exchange.SSE,
            direction=direction,
            type=OrderType.LIMIT,
            volume=volume,
            price=price,
            offset=Offset.NONE,
            reference="StockTrading"
        )
        
        # Send order
        gateway_names = self.main_engine.get_all_gateway_names()
        if gateway_names:
            vt_orderid = self.main_engine.send_order(req, gateway_names[0])
            if vt_orderid:
                QtWidgets.QMessageBox.information(
                    self, "委托成功", f"订单已提交: {vt_orderid}"
                )
        else:
            QtWidgets.QMessageBox.warning(self, "错误", "没有可用的交易接口")
    
    def on_buy_clicked(self) -> None:
        """Handle buy button click."""
        self.send_order(Direction.LONG)
    
    def on_sell_clicked(self) -> None:
        """Handle sell button click."""
        self.send_order(Direction.SHORT)
    
    def on_sell_short_clicked(self) -> None:
        """Handle sell short button click."""
        self.send_order(Direction.SHORT)
    
    def on_cover_clicked(self) -> None:
        """Handle cover button click."""
        self.send_order(Direction.LONG)
    
    def update_with_cell(self, cell: BaseCell) -> None:
        """Update widget with data from a cell (e.g., from tick or position monitor)."""
        data = cell.get_data()
        
        if hasattr(data, 'symbol'):
            # Update symbol
            if hasattr(data, 'name'):
                symbol_text = f"{data.symbol}    {data.name}"
            else:
                symbol_text = data.symbol
            self.symbol_edit.setText(symbol_text)
            
            # Set vt_symbol for monitoring
            if hasattr(data, 'exchange'):
                self.vt_symbol = f"{data.symbol}.{data.exchange.value}"
            else:
                self.vt_symbol = f"{data.symbol}.SSE"
            
            # Subscribe to tick data
            req = SubscribeRequest(symbol=data.symbol, 
                                 exchange=getattr(data, 'exchange', Exchange.SSE))
            gateway_names = self.main_engine.get_all_gateway_names()
            if gateway_names:
                self.main_engine.subscribe(req, gateway_names[0])
        
        # If it's position data, update position-related fields
        if isinstance(data, PositionData):
            self.position_volume = int(data.volume)
            self.max_sell_label.setText(f"{self.position_volume:,}")
        
        # If it's tick data, update price
        if isinstance(data, TickData):
            self.price_spinbox.setValue(data.last_price)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Find and remove this widget from main window's widgets dict
        if hasattr(self, '_widget_name'):
            # Get the main window instance (parent widgets until we find MainWindow)
            parent = self.parent()
            while parent:
                if hasattr(parent, 'widgets') and hasattr(parent, 'main_engine'):
                    # Found the main window
                    if self._widget_name in parent.widgets:
                        del parent.widgets[self._widget_name]
                    break
                parent = parent.parent()
        
        # Call parent closeEvent
        super().closeEvent(event)


class ContractManager(QtWidgets.QWidget):
    """
    Query contract data available to trade in system.
    """

    headers: dict[str, str] = {
        "vt_symbol": _("本地代码"),
        "symbol": _("代码"),
        "exchange": _("交易所"),
        "name": _("名称"),
        "product": _("合约分类"),
        "size": _("合约乘数"),
        "pricetick": _("价格跳动"),
        "min_volume": _("最小委托量"),
        "option_portfolio": _("期权产品"),
        "option_expiry": _("期权到期日"),
        "option_strike": _("期权行权价"),
        "option_type": _("期权类型"),
        "gateway_name": _("交易接口"),
    }

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle(_("合约查询"))
        self.resize(1000, 600)

        self.filter_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.filter_line.setPlaceholderText(_("输入合约代码或者交易所，留空则查询所有合约"))

        self.button_show: QtWidgets.QPushButton = QtWidgets.QPushButton(_("查询"))
        self.button_show.clicked.connect(self.show_contracts)

        labels: list = []
        for name, display in self.headers.items():
            label: str = f"{display}\n{name}"
            labels.append(label)

        self.contract_table: QtWidgets.QTableWidget = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(len(self.headers))
        self.contract_table.setHorizontalHeaderLabels(labels)
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.EditTrigger.NoEditTriggers)
        self.contract_table.setAlternatingRowColors(True)

        hbox: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filter_line)
        hbox.addWidget(self.button_show)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.contract_table)

        self.setLayout(vbox)

    def show_contracts(self) -> None:
        """
        Show contracts by symbol
        """
        flt: str = str(self.filter_line.text())

        all_contracts: list[ContractData] = self.main_engine.get_all_contracts()
        if flt:
            contracts: list[ContractData] = [
                contract for contract in all_contracts if flt in contract.vt_symbol
            ]
        else:
            contracts = all_contracts

        self.contract_table.clearContents()
        self.contract_table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            for column, name in enumerate(self.headers.keys()):
                value: Any = getattr(contract, name)

                if value in {None, 0}:
                    value = ""

                cell: BaseCell
                if isinstance(value, Enum):
                    cell = EnumCell(value, contract)
                elif isinstance(value, datetime):
                    cell = DateCell(value, contract)
                else:
                    cell = BaseCell(value, contract)
                self.contract_table.setItem(row, column, cell)

        self.contract_table.resizeColumnsToContents()


class AboutDialog(QtWidgets.QDialog):
    """
    Information about the trading platform.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle(_("关于VeighNa Trader"))

        from ... import __version__ as vnpy_version

        text: str = f"""
            By Traders, For Traders.

            Created by VeighNa Technology


            License：MIT
            Website：www.vnpy.com
            Github：www.github.com/vnpy/vnpy


            VeighNa - {vnpy_version}
            Python - {platform.python_version()}
            PySide6 - {metadata.version("pyside6")}
            NumPy - {metadata.version("numpy")}
            pandas - {metadata.version("pandas")}
            """

        label: QtWidgets.QLabel = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(500)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)
        self.setLayout(vbox)


class GlobalDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self) -> None:
        """"""
        super().__init__()

        self.widgets: dict[str, tuple[QtWidgets.QLineEdit, type]] = {}

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle(_("全局配置"))
        self.setMinimumWidth(800)

        settings: dict = copy(SETTINGS)
        settings.update(load_json(SETTING_FILENAME))

        # Initialize line edits and form layout based on setting.
        form: QtWidgets.QFormLayout = QtWidgets.QFormLayout()

        for field_name, field_value in settings.items():
            field_type: type = type(field_value)
            widget: QtWidgets.QLineEdit = QtWidgets.QLineEdit(str(field_value))

            form.addRow(f"{field_name} <{field_type.__name__}>", widget)
            self.widgets[field_name] = (widget, field_type)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton(_("确定"))
        button.clicked.connect(self.update_setting)
        form.addRow(button)

        scroll_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        scroll_widget.setLayout(form)

        scroll_area: QtWidgets.QScrollArea = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(scroll_area)
        self.setLayout(vbox)

    def update_setting(self) -> None:
        """
        Get setting value from line edits and update global setting file.
        """
        settings: dict = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            value_text: str = widget.text()

            if field_type is bool:
                if value_text == "True":
                    field_value: bool = True
                else:
                    field_value = False
            else:
                field_value = field_type(value_text)

            settings[field_name] = field_value

        QtWidgets.QMessageBox.information(
            self,
            _("注意"),
            _("全局配置的修改需要重启后才会生效！"),
            QtWidgets.QMessageBox.StandardButton.Ok
        )

        save_json(SETTING_FILENAME, settings)
        self.accept()


class Level2Widget(QtWidgets.QFrame):
    """
    Level-2 market data widget based on level2.ui layout.
    Shows 10-level bid/ask depth data.
    """
    
    signal_tick: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__()
        
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        
        self.vt_symbol: str = ""
        self.symbol_name: str = ""
        
        self.init_ui()
        self.register_event()
    
    def init_ui(self) -> None:
        """Initialize user interface."""
        self.setFixedSize(800, 500)  # 进一步增大窗口尺寸
        self.setWindowTitle("Level-2 十档行情")
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        
        # 确保继承主应用的样式
        app = QtWidgets.QApplication.instance()
        if app:
            self.setStyleSheet(app.styleSheet())
        
        self.init_top_labels()
        self.init_bid_table()
        self.init_ask_table()
        self.init_info_table()
    
    def init_top_labels(self) -> None:
        """Initialize top information labels."""
        # 最高价
        label_high = QtWidgets.QLabel("最高", self)
        label_high.setGeometry(10, 0, 40, 18)
        
        self.label_high_price = QtWidgets.QLabel("4.11", self)
        self.label_high_price.setGeometry(10, 20, 40, 18)
        self.label_high_price.setStyleSheet("color: rgb(255, 0, 0);")
        
        # 最低价
        label_low = QtWidgets.QLabel("最低", self)
        label_low.setGeometry(60, 0, 40, 18)
        
        self.label_low_price = QtWidgets.QLabel("4.06", self)
        self.label_low_price.setGeometry(60, 20, 40, 18)
        self.label_low_price.setStyleSheet("color: rgb(0, 170, 0);")
        
        # 涨幅
        label_change = QtWidgets.QLabel("涨幅", self)
        label_change.setGeometry(110, 0, 50, 18)
        
        self.label_change_pct = QtWidgets.QLabel("0.49%", self)
        self.label_change_pct.setGeometry(110, 20, 50, 18)
        self.label_change_pct.setStyleSheet("color: rgb(255, 0, 0);")
        
        # 涨停价
        label_limit_up = QtWidgets.QLabel("涨停", self)
        label_limit_up.setGeometry(170, 0, 40, 18)
        
        self.label_limit_up_price = QtWidgets.QLabel("4.49", self)
        self.label_limit_up_price.setGeometry(170, 20, 40, 18)
        self.label_limit_up_price.setStyleSheet("color: rgb(255, 0, 0);")
        
        # 跌停价
        label_limit_down = QtWidgets.QLabel("跌停", self)
        label_limit_down.setGeometry(220, 0, 40, 18)
        
        self.label_limit_down_price = QtWidgets.QLabel("3.67", self)
        self.label_limit_down_price.setGeometry(220, 20, 40, 18)
        self.label_limit_down_price.setStyleSheet("color: rgb(0, 170, 0);")
        
        # 开盘价
        label_open = QtWidgets.QLabel("开盘", self)
        label_open.setGeometry(270, 0, 40, 18)
        
        self.label_open_price = QtWidgets.QLabel("4.07", self)
        self.label_open_price.setGeometry(270, 20, 40, 18)
        self.label_open_price.setStyleSheet("color: rgb(0, 170, 0);")
        
        # 昨收价
        label_pre_close = QtWidgets.QLabel("昨收", self)
        label_pre_close.setGeometry(320, 0, 40, 18)
        
        self.label_pre_close_price = QtWidgets.QLabel("4.08", self)
        self.label_pre_close_price.setGeometry(320, 20, 40, 18)
        
        # 可买股票
        label_buyable = QtWidgets.QLabel("可买股票", self)
        label_buyable.setGeometry(370, 0, 80, 18)
        label_buyable.setStyleSheet("color: rgb(255, 170, 0);")
        
        self.label_buyable_volume = QtWidgets.QLabel("2000", self)
        self.label_buyable_volume.setGeometry(370, 20, 80, 18)
        self.label_buyable_volume.setStyleSheet("color: rgb(255, 170, 0);")
    
    def init_bid_table(self) -> None:
        """Initialize bid (buy) table."""
        self.bid_table = QtWidgets.QTableWidget(self)
        self.bid_table.setGeometry(10, 60, 180, 400)  # 进一步调整位置和大小
        self.bid_table.setWordWrap(True)
        self.bid_table.setCornerButtonEnabled(True)
        
        # Hide row numbers
        self.bid_table.verticalHeader().setVisible(False)
        
        # Set up columns
        self.bid_table.setColumnCount(2)
        self.bid_table.setHorizontalHeaderLabels(["买价", "买量"])
        
        # Set up rows (10 levels)
        self.bid_table.setRowCount(10)
        
        # Populate with sample data and set colors based on pre_close price from label
        try:
            sample_pre_close = float(self.label_pre_close_price.text())
        except (ValueError, AttributeError):
            sample_pre_close = 4.08  # Fallback value
        
        for i in range(10):
            # Buy price
            price_value = float(f"4.{10-i:02d}")
            price_item = QtWidgets.QTableWidgetItem(f"4.{10-i:02d}")
            price_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            
            # Set color based on comparison with sample pre_close
            if price_value < sample_pre_close:
                price_item.setForeground(QtGui.QColor(0, 170, 0))  # Green
            elif price_value > sample_pre_close:
                price_item.setForeground(QtGui.QColor(255, 0, 0))  # Red
            else:
                price_item.setForeground(QtGui.QColor(255, 255, 255))  # White
            
            self.bid_table.setItem(i, 0, price_item)
            
            # Buy volume
            volume_item = QtWidgets.QTableWidgetItem(f"{(i+1)*100}")
            volume_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.bid_table.setItem(i, 1, volume_item)
        
        # Resize columns to fit content and set proper widths
        self.bid_table.resizeColumnsToContents()
        self.bid_table.setColumnWidth(0, 80)  # 买价列宽度
        self.bid_table.setColumnWidth(1, 90)  # 买量列宽度
        
        # Set row height for better visibility
        for row in range(10):
            self.bid_table.setRowHeight(row, 30)
    
    def init_ask_table(self) -> None:
        """Initialize ask (sell) table."""
        self.ask_table = QtWidgets.QTableWidget(self)
        self.ask_table.setGeometry(200, 60, 180, 400)  # 进一步调整位置和大小
        
        # Hide row numbers
        self.ask_table.verticalHeader().setVisible(False)
        
        # Set up columns
        self.ask_table.setColumnCount(2)
        self.ask_table.setHorizontalHeaderLabels(["卖价", "卖量"])
        
        # Set up rows (10 levels)
        self.ask_table.setRowCount(10)
        
        # Populate with sample data and set colors based on pre_close price from label
        try:
            sample_pre_close = float(self.label_pre_close_price.text())
        except (ValueError, AttributeError):
            sample_pre_close = 4.08  # Fallback value
        
        for i in range(10):
            # Sell price
            price_value = float(f"4.{11+i:02d}")
            price_item = QtWidgets.QTableWidgetItem(f"4.{11+i:02d}")
            price_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            
            # Set color based on comparison with sample pre_close
            if price_value < sample_pre_close:
                price_item.setForeground(QtGui.QColor(0, 170, 0))  # Green
            elif price_value > sample_pre_close:
                price_item.setForeground(QtGui.QColor(255, 0, 0))  # Red
            else:
                price_item.setForeground(QtGui.QColor(255, 255, 255))  # White
            
            self.ask_table.setItem(i, 0, price_item)
            
            # Sell volume
            volume_item = QtWidgets.QTableWidgetItem(f"{(10-i)*100}")
            volume_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ask_table.setItem(i, 1, volume_item)
        
        # Resize columns to fit content and set proper widths
        self.ask_table.resizeColumnsToContents()
        self.ask_table.setColumnWidth(0, 80)  # 卖价列宽度
        self.ask_table.setColumnWidth(1, 90)  # 卖量列宽度
        
        # Set row height for better visibility
        for row in range(10):
            self.ask_table.setRowHeight(row, 30)
    
    def init_info_table(self) -> None:
        """Initialize trading details table."""
        self.info_table = QtWidgets.QTableWidget(self)
        self.info_table.setGeometry(390, 60, 380, 400)  # 进一步调整位置和大小
        
        # Hide row numbers
        self.info_table.verticalHeader().setVisible(False)
        
        # Set table properties for better row highlighting
        self.info_table.setAlternatingRowColors(False)  # Disable alternating colors
        self.info_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.info_table.setShowGrid(False)  # Hide grid lines for seamless background
        
        # Set up columns for trading details
        self.info_table.setColumnCount(2)
        self.info_table.setHorizontalHeaderLabels(["价格", "数量"])
        
        # Set up rows for trading details (show recent 20 transactions)
        self.info_table.setRowCount(20)
        
        # Populate with sample trading details data
        sample_trades = [
            ("4.09", "1,200"),
            ("4.08", "800"),
            ("4.09", "1,500"),
            ("4.08", "900"),
            ("4.07", "1,100"),
            ("4.08", "700"),
            ("4.09", "1,300"),
            ("4.08", "600"),
            ("4.07", "1,000"),
            ("4.08", "850"),
            ("4.09", "1,400"),
            ("4.08", "950"),
            ("4.07", "750"),
            ("4.08", "1,250"),
            ("4.09", "680"),
            ("4.08", "1,020"),
            ("4.07", "890"),
            ("4.08", "1,150"),
            ("4.09", "720"),
            ("4.08", "980")
        ]
        
        for i, (price_str, volume_str) in enumerate(sample_trades):
            # Parse volume to check if it's over 1000
            volume_clean = volume_str.replace(',', '')  # Remove comma separators
            try:
                volume_value = int(volume_clean)
            except ValueError:
                volume_value = 0
            
            # Price with color coding
            price_item = QtWidgets.QTableWidgetItem(price_str)
            price_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            
            # Volume
            volume_item = QtWidgets.QTableWidgetItem(volume_str)
            volume_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            
            # Set items first
            self.info_table.setItem(i, 0, price_item)
            self.info_table.setItem(i, 1, volume_item)
            
            # Set color and background based on comparison with pre_close price and volume
            try:
                price_value = float(price_str)
                pre_close_value = float(self.label_pre_close_price.text())
                
                if volume_value >= 1000:  # Changed from > 1000 to >= 1000
                    # High volume: use CSS style for entire row background
                    if price_value > pre_close_value:
                        # Red background for entire row when price above pre_close
                        self.set_row_style(i, "background-color: rgb(200, 0, 0); color: white;")
                    elif price_value < pre_close_value:
                        # Green background for entire row when price below pre_close
                        self.set_row_style(i, "background-color: rgb(0, 150, 0); color: white;")
                    else:
                        # Equal to pre_close, use white background with black text
                        self.set_row_style(i, "background-color: white; color: black;")
                else:
                    # Normal volume: only set text color without background
                    if price_value < pre_close_value:
                        price_item.setForeground(QtGui.QColor(0, 170, 0))  # Green text
                        volume_item.setForeground(QtGui.QColor(255, 255, 255))  # White text for volume
                    elif price_value > pre_close_value:
                        price_item.setForeground(QtGui.QColor(255, 0, 0))  # Red text
                        volume_item.setForeground(QtGui.QColor(255, 255, 255))  # White text for volume
                    else:
                        price_item.setForeground(QtGui.QColor(255, 255, 255))  # White text
                        volume_item.setForeground(QtGui.QColor(255, 255, 255))  # White text for volume
                    
            except (ValueError, AttributeError):
                # Default colors if parsing fails
                price_item.setForeground(QtGui.QColor(255, 255, 255))  # Default white
                volume_item.setForeground(QtGui.QColor(255, 255, 255))  # Default white
        
        # Resize columns to fit content and set proper widths
        self.info_table.resizeColumnsToContents()
        self.info_table.setColumnWidth(0, 120)  # 价格列宽度
        self.info_table.setColumnWidth(1, 180)  # 数量列宽度
        
        # Set row height for better visibility
        for row in range(20):
            self.info_table.setRowHeight(row, 20)
    
    def set_row_style(self, row: int, style: str) -> None:
        """Set CSS style for entire row to achieve seamless row background color."""
        for col in range(self.info_table.columnCount()):
            item = self.info_table.item(row, col)
            if item:
                item.setData(QtCore.Qt.ItemDataRole.BackgroundRole, None)  # Clear default background
                # Create a widget to hold the item with custom styling
                widget = QtWidgets.QWidget()
                widget.setStyleSheet(style)
                layout = QtWidgets.QVBoxLayout(widget)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)
                
                # Create a label with the item text
                label = QtWidgets.QLabel(item.text())
                label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet(style)
                layout.addWidget(label)
                
                # Set the widget as the cell widget
                self.info_table.setCellWidget(row, col, widget)
    
    def register_event(self) -> None:
        """Register event handlers."""
        self.signal_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)
    
    def process_tick_event(self, event: Event) -> None:
        """Process tick data event."""
        tick: TickData = event.data
        if not self.vt_symbol or tick.vt_symbol != self.vt_symbol:
            return
        
        # Update price information
        if tick.last_price:
            # Update current price in info table
            current_price_item = self.info_table.item(0, 1)
            if current_price_item:
                current_price_item.setText(f"{tick.last_price:.2f}")
        
        # Update bid/ask levels
        self.update_bid_ask_levels(tick)
        
        # Update daily statistics
        if tick.high_price:
            self.label_high_price.setText(f"{tick.high_price:.2f}")
        if tick.low_price:
            self.label_low_price.setText(f"{tick.low_price:.2f}")
        if tick.open_price:
            self.label_open_price.setText(f"{tick.open_price:.2f}")
        if tick.pre_close:
            self.label_pre_close_price.setText(f"{tick.pre_close:.2f}")
            
        # Calculate and update change percentage
        if tick.last_price and tick.pre_close:
            change_pct = (tick.last_price - tick.pre_close) / tick.pre_close * 100
            self.label_change_pct.setText(f"{change_pct:+.2f}%")
            
            # Set color based on change
            if change_pct > 0:
                self.label_change_pct.setStyleSheet("color: rgb(255, 0, 0);")
            elif change_pct < 0:
                self.label_change_pct.setStyleSheet("color: rgb(0, 170, 0);")
            else:
                self.label_change_pct.setStyleSheet("color: rgb(255, 255, 255);")
    
    def update_bid_ask_levels(self, tick: TickData) -> None:
        """Update bid and ask level data with color coding based on pre_close price."""
        pre_close = tick.pre_close if tick.pre_close else 0
        
        # Update bid levels
        bid_prices = [tick.bid_price_1, tick.bid_price_2, tick.bid_price_3, tick.bid_price_4, tick.bid_price_5]
        bid_volumes = [tick.bid_volume_1, tick.bid_volume_2, tick.bid_volume_3, tick.bid_volume_4, tick.bid_volume_5]
        
        for i, (price, volume) in enumerate(zip(bid_prices, bid_volumes)):
            if price and volume:
                price_item = self.bid_table.item(4-i, 0)  # Reverse order for bid (highest first)
                volume_item = self.bid_table.item(4-i, 1)
                if price_item and volume_item:
                    price_item.setText(f"{price:.2f}")
                    volume_item.setText(f"{int(volume):,}")
                    
                    # Set color based on comparison with pre_close price
                    if pre_close > 0:
                        if price < pre_close:
                            # Green for prices below pre_close
                            price_item.setForeground(QtGui.QColor(0, 170, 0))
                        elif price > pre_close:
                            # Red for prices above pre_close
                            price_item.setForeground(QtGui.QColor(255, 0, 0))
                        else:
                            # White for prices equal to pre_close
                            price_item.setForeground(QtGui.QColor(255, 255, 255))
        
        # Update ask levels
        ask_prices = [tick.ask_price_1, tick.ask_price_2, tick.ask_price_3, tick.ask_price_4, tick.ask_price_5]
        ask_volumes = [tick.ask_volume_1, tick.ask_volume_2, tick.ask_volume_3, tick.ask_volume_4, tick.ask_volume_5]
        
        for i, (price, volume) in enumerate(zip(ask_prices, ask_volumes)):
            if price and volume:
                price_item = self.ask_table.item(i, 0)
                volume_item = self.ask_table.item(i, 1)
                if price_item and volume_item:
                    price_item.setText(f"{price:.2f}")
                    volume_item.setText(f"{int(volume):,}")
                    
                    # Set color based on comparison with pre_close price
                    if pre_close > 0:
                        if price < pre_close:
                            # Green for prices below pre_close
                            price_item.setForeground(QtGui.QColor(0, 170, 0))
                        elif price > pre_close:
                            # Red for prices above pre_close
                            price_item.setForeground(QtGui.QColor(255, 0, 0))
                        else:
                            # White for prices equal to pre_close
                            price_item.setForeground(QtGui.QColor(255, 255, 255))
    
    def set_symbol(self, vt_symbol: str, symbol_name: str = "") -> None:
        """Set the symbol to monitor."""
        self.vt_symbol = vt_symbol
        self.symbol_name = symbol_name
        
        # Update window title
        if symbol_name:
            self.setWindowTitle(f"Level-2 十档行情 - {symbol_name} - {vt_symbol}")
        else:
            self.setWindowTitle(f"Level-2 十档行情 - {vt_symbol}")
        
        # Subscribe to tick data
        symbol = vt_symbol.split('.')[0]
        exchange_str = vt_symbol.split('.')[1] if '.' in vt_symbol else 'SSE'
        
        try:
            exchange = Exchange(exchange_str)
        except ValueError:
            exchange = Exchange.SSE
        
        req = SubscribeRequest(symbol=symbol, exchange=exchange)
        gateway_names = self.main_engine.get_all_gateway_names()
        if gateway_names:
            self.main_engine.subscribe(req, gateway_names[0])
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Find and remove this widget from main window's widgets dict
        if hasattr(self, '_widget_name'):
            # Get the main window instance
            parent = self.parent()
            while parent:
                if hasattr(parent, 'widgets') and hasattr(parent, 'main_engine'):
                    # Found the main window
                    if self._widget_name in parent.widgets:
                        del parent.widgets[self._widget_name]
                    break
                parent = parent.parent()
        
        # Call parent closeEvent
        super().closeEvent(event)
