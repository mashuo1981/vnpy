"""
TCP Client implementation for vnpy trader
Based on tcp_client_demo.cpp
"""

import socket
import struct
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import IntEnum

from ..object import OrderRequest, OrderData
from ..constant import Direction, Exchange, OrderType, Offset


class TcpMessageType(IntEnum):
    """TCP message types matching C++ enum"""
    ORDER_REQUEST = 1
    CANCEL_REQUEST = 2
    QUERY_REQUEST = 3


@dataclass
class FixOrder:
    """
    FIX Order structure matching C++ fix_Order struct
    Total size should match C++ version
    """
    m_ord_id: str = ""              # 64 bytes - ClOrdID
    m_ex_destion: str = ""          # 64 bytes - SecurityExchange  
    m_symbol: str = ""              # 64 bytes - Symbol
    m_side: str = ""                # 1 byte - Side
    m_qty: float = 0.0              # 4 bytes - OrderQty
    m_price: float = 0.0            # 4 bytes - Price
    m_ordtype: str = ""             # 1 byte - OrdType
    m_text: str = ""                # 64 bytes - Text
    m_time_in_force: str = ""       # 1 byte - TimeInForce
    m_account: str = ""             # 64 bytes - Account
    m_handl_inst: str = ""          # 1 byte - HandlInst
    m_curreny: str = ""             # 64 bytes - Currency
    m_transact_time: bytes = b""    # 24 bytes - TransactTime
    m_client_id: str = ""           # 64 bytes - ClientID
    m_secuity_type: str = ""        # 64 bytes - SecurityType
    m_maturity_month_year: str = "" # 64 bytes - MaturityMonthYear
    m_put_or_call: str = ""         # 64 bytes - PutOrCall
    m_strike_price: str = ""        # 64 bytes - StrikePrice
    m_opt_attribute: str = ""       # 64 bytes - OptAttribute
    m_security_id: str = ""         # 64 bytes - SecurityID
    m_id_source: str = ""           # 64 bytes - IDSource
    m_max_floor: str = ""           # 64 bytes - MaxFloor
    m_locate_reqd: str = ""         # 64 bytes - LocateReqd
    m_forex_req: str = ""           # 64 bytes - ForexReq
    m_settlmnt_typ: str = ""        # 64 bytes - SettlmntTyp
    m_fut_sett_date: str = ""       # 64 bytes - FutSettDate

    def to_bytes(self) -> bytes:
        """Convert FixOrder to bytes for network transmission"""
        # Pack all fields according to C++ struct layout
        data = b""
        
        # String fields (64 bytes each, null-terminated)
        data += self.m_ord_id.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_ex_destion.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_symbol.encode('utf-8')[:63].ljust(64, b'\x00')
        
        # Single char fields
        data += self.m_side.encode('utf-8')[:1].ljust(1, b'\x00')
        
        # Float fields (4 bytes each, little-endian)
        data += struct.pack('<f', self.m_qty)
        data += struct.pack('<f', self.m_price)
        
        # Single char fields
        data += self.m_ordtype.encode('utf-8')[:1].ljust(1, b'\x00')
        
        # String fields continued
        data += self.m_text.encode('utf-8')[:63].ljust(64, b'\x00')
        
        # Single char fields
        data += self.m_time_in_force.encode('utf-8')[:1].ljust(1, b'\x00')
        
        # String fields continued
        data += self.m_account.encode('utf-8')[:63].ljust(64, b'\x00')
        
        # Single char fields
        data += self.m_handl_inst.encode('utf-8')[:1].ljust(1, b'\x00')
        
        # String fields continued
        data += self.m_curreny.encode('utf-8')[:63].ljust(64, b'\x00')
        
        # TransactTime (24 bytes) - simplified as timestamp + padding
        if self.m_transact_time:
            data += self.m_transact_time[:24].ljust(24, b'\x00')
        else:
            # Create timestamp (8 bytes int64 + 4 bytes int + 12 bytes padding)
            timestamp = int(time.time())
            data += struct.pack('<q', timestamp)  # 8 bytes int64
            data += struct.pack('<i', 6)          # 4 bytes precision
            data += b'\x00' * 12                  # 12 bytes padding
        
        # Remaining string fields (64 bytes each)
        data += self.m_client_id.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_secuity_type.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_maturity_month_year.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_put_or_call.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_strike_price.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_opt_attribute.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_security_id.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_id_source.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_max_floor.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_locate_reqd.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_forex_req.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_settlmnt_typ.encode('utf-8')[:63].ljust(64, b'\x00')
        data += self.m_fut_sett_date.encode('utf-8')[:63].ljust(64, b'\x00')
        
        return data


@dataclass 
class TcpMessageHeader:
    """TCP message header"""
    msg_type: TcpMessageType
    msg_length: int
    
    def to_bytes(self) -> bytes:
        """Convert header to bytes"""
        return struct.pack('<II', self.msg_type.value, self.msg_length)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'TcpMessageHeader':
        """Create header from bytes"""
        msg_type, msg_length = struct.unpack('<II', data)
        return cls(TcpMessageType(msg_type), msg_length)


@dataclass
class TcpOrderRequest:
    """TCP order request combining header and order"""
    header: TcpMessageHeader
    order: FixOrder
    
    def to_bytes(self) -> bytes:
        """Convert entire request to bytes"""
        order_bytes = self.order.to_bytes()
        self.header.msg_length = len(order_bytes)
        return self.header.to_bytes() + order_bytes


@dataclass
class TcpOrderResponse:
    """TCP order response"""
    result_code: int
    message: str
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'TcpOrderResponse':
        """Create response from bytes"""
        if len(data) < 4:
            return cls(-1, "Invalid response data")
        
        result_code = struct.unpack('<i', data[:4])[0]
        message = data[4:].decode('utf-8', errors='ignore').rstrip('\x00')
        return cls(result_code, message)


class TcpClient:
    """
    TCP Client for connecting to trading server
    Based on tcp_client_demo.cpp implementation
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        """
        Initialize TCP client
        
        Args:
            host: Server host address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to TCP server
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Set socket options
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Connect to server
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            print(f"Connected to TCP server at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"Failed to connect to TCP server: {e}")
            self.connected = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def disconnect(self) -> None:
        """Disconnect from TCP server"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False
        print("Disconnected from TCP server")
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.connected and self.socket is not None
    
    def make_order(self, order_req: OrderRequest) -> Optional[TcpOrderResponse]:
        """
        Send order request to server
        
        Args:
            order_req: vnpy OrderRequest object
            
        Returns:
            TcpOrderResponse if successful, None if failed
        """
        if not self.is_connected():
            print("Not connected to TCP server")
            return None
        
        try:
            # Convert vnpy OrderRequest to FixOrder
            fix_order = self._convert_order_request(order_req)
            
            # Create TCP request
            header = TcpMessageHeader(TcpMessageType.ORDER_REQUEST, 0)
            tcp_request = TcpOrderRequest(header, fix_order)
            
            # Send request
            request_bytes = tcp_request.to_bytes()
            bytes_sent = self.socket.send(request_bytes)
            
            print(f"Order request sent ({bytes_sent} bytes)")
            print(f"Order ID: {fix_order.m_ord_id}")
            print(f"Symbol: {fix_order.m_symbol}")
            print(f"Side: {fix_order.m_side}")
            print(f"Quantity: {fix_order.m_qty}")
            print(f"Price: {fix_order.m_price}")
            
            # Receive response
            response_data = self.socket.recv(4096)
            if response_data:
                response = TcpOrderResponse.from_bytes(response_data)
                print(f"Server response: Code={response.result_code}, Message={response.message}")
                return response
            else:
                print("No response from server")
                return None
                
        except Exception as e:
            print(f"Failed to send order: {e}")
            return None
    
    def _convert_order_request(self, order_req: OrderRequest) -> FixOrder:
        """
        Convert vnpy OrderRequest to FixOrder
        
        Args:
            order_req: vnpy OrderRequest object
            
        Returns:
            FixOrder object
        """
        fix_order = FixOrder()
        
        # Basic order information
        fix_order.m_ord_id = f"{order_req.symbol}_{int(time.time())}"
        fix_order.m_symbol = order_req.symbol
        fix_order.m_qty = float(order_req.volume)
        fix_order.m_price = float(order_req.price)
        
        # Convert direction
        if order_req.direction == Direction.LONG:
            fix_order.m_side = '1'  # Buy
        else:
            fix_order.m_side = '2'  # Sell
        
        # Convert order type
        if order_req.type == OrderType.LIMIT:
            fix_order.m_ordtype = '2'  # Limit
        elif order_req.type == OrderType.MARKET:
            fix_order.m_ordtype = '1'  # Market
        else:
            fix_order.m_ordtype = '2'  # Default to Limit
        
        # Exchange mapping
        if order_req.exchange == Exchange.SSE:
            fix_order.m_ex_destion = "SH"
        elif order_req.exchange == Exchange.SZSE:
            fix_order.m_ex_destion = "SZ"
        else:
            fix_order.m_ex_destion = "SH"  # Default
        
        # Additional fields
        fix_order.m_text = order_req.reference or "vnpy_tcp_client"
        fix_order.m_time_in_force = '0'  # Day order
        fix_order.m_account = "VNPY_ACCOUNT"
        fix_order.m_handl_inst = '1'
        fix_order.m_curreny = "CNY"
        fix_order.m_client_id = "VNPY_CLIENT"
        fix_order.m_secuity_type = "CS"  # Common Stock
        
        return fix_order
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()