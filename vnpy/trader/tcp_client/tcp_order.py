"""
TCP Order Client - High-level interface for order operations
"""

from typing import Optional, Dict, Any, Callable
import threading
import time

from .tcp_client import TcpClient, TcpOrderResponse
from ..object import OrderRequest, OrderData
from ..constant import Direction, Exchange, OrderType, Offset


class TcpOrderClient:
    """
    High-level TCP order client with simplified interface
    Provides easy-to-use connect and make_order functions
    """
    
    def __init__(
        self, 
        host: str = "127.0.0.1", 
        port: int = 8888,
        auto_reconnect: bool = True,
        on_response_callback: Optional[Callable[[TcpOrderResponse], None]] = None
    ):
        """
        Initialize TCP order client
        
        Args:
            host: Server host address
            port: Server port number
            auto_reconnect: Whether to automatically reconnect on connection loss
            on_response_callback: Callback function for order responses
        """
        self.host = host
        self.port = port
        self.auto_reconnect = auto_reconnect
        self.on_response_callback = on_response_callback
        
        self.tcp_client: Optional[TcpClient] = None
        self.connected = False
        self._lock = threading.Lock()
        
        # Statistics
        self.orders_sent = 0
        self.orders_successful = 0
        self.orders_failed = 0
    
    def connect(self) -> bool:
        """
        Connect to TCP server
        
        Returns:
            True if connection successful, False otherwise
        """
        with self._lock:
            try:
                if self.tcp_client:
                    self.tcp_client.disconnect()
                
                self.tcp_client = TcpClient(self.host, self.port)
                success = self.tcp_client.connect()
                
                if success:
                    self.connected = True
                    print(f"TcpOrderClient connected to {self.host}:{self.port}")
                else:
                    self.connected = False
                    print(f"TcpOrderClient failed to connect to {self.host}:{self.port}")
                
                return success
                
            except Exception as e:
                print(f"TcpOrderClient connection error: {e}")
                self.connected = False
                return False
    
    def disconnect(self) -> None:
        """Disconnect from TCP server"""
        with self._lock:
            if self.tcp_client:
                self.tcp_client.disconnect()
                self.tcp_client = None
            self.connected = False
            print("TcpOrderClient disconnected")
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        with self._lock:
            return self.connected and self.tcp_client is not None and self.tcp_client.is_connected()
    
    def make_order(
        self,
        symbol: str,
        direction: Direction,
        volume: float,
        price: float,
        order_type: OrderType = OrderType.LIMIT,
        exchange: Exchange = Exchange.SSE,
        offset: Offset = Offset.NONE,
        reference: str = ""
    ) -> bool:
        """
        Send order to server (simplified interface)
        
        Args:
            symbol: Stock symbol (e.g., "600000")
            direction: Order direction (Direction.LONG for buy, Direction.SHORT for sell)
            volume: Order volume
            price: Order price
            order_type: Order type (default: LIMIT)
            exchange: Exchange (default: SSE)
            offset: Position offset (default: NONE)
            reference: Reference text
            
        Returns:
            True if order sent successfully, False otherwise
        """
        # Check connection
        if not self.is_connected():
            if self.auto_reconnect:
                print("Connection lost, attempting to reconnect...")
                if not self.connect():
                    print("Failed to reconnect")
                    return False
            else:
                print("Not connected to server")
                return False
        
        # Create order request
        order_req = OrderRequest(
            symbol=symbol,
            exchange=exchange,
            direction=direction,
            type=order_type,
            volume=volume,
            price=price,
            offset=offset,
            reference=reference or "TcpOrderClient"
        )
        
        # Send order
        try:
            with self._lock:
                response = self.tcp_client.make_order(order_req)
                self.orders_sent += 1
                
                if response and response.result_code == 0:
                    self.orders_successful += 1
                    print(f"Order successful: {symbol} {direction.value} {volume}@{price}")
                    
                    # Call response callback if provided
                    if self.on_response_callback:
                        try:
                            self.on_response_callback(response)
                        except Exception as e:
                            print(f"Error in response callback: {e}")
                    
                    return True
                else:
                    self.orders_failed += 1
                    error_msg = response.message if response else "No response"
                    print(f"Order failed: {symbol} - {error_msg}")
                    return False
                    
        except Exception as e:
            self.orders_failed += 1
            print(f"Order error: {e}")
            return False
    
    def make_order_from_request(self, order_req: OrderRequest) -> bool:
        """
        Send order using OrderRequest object
        
        Args:
            order_req: vnpy OrderRequest object
            
        Returns:
            True if order sent successfully, False otherwise
        """
        return self.make_order(
            symbol=order_req.symbol,
            direction=order_req.direction,
            volume=order_req.volume,
            price=order_req.price,
            order_type=order_req.type,
            exchange=order_req.exchange,
            offset=order_req.offset,
            reference=order_req.reference
        )
    
    def buy(self, symbol: str, volume: float, price: float, exchange: Exchange = Exchange.SSE) -> bool:
        """
        Convenience method to place buy order
        
        Args:
            symbol: Stock symbol
            volume: Order volume
            price: Order price
            exchange: Exchange
            
        Returns:
            True if order sent successfully
        """
        return self.make_order(symbol, Direction.LONG, volume, price, exchange=exchange)
    
    def sell(self, symbol: str, volume: float, price: float, exchange: Exchange = Exchange.SSE) -> bool:
        """
        Convenience method to place sell order
        
        Args:
            symbol: Stock symbol
            volume: Order volume
            price: Order price
            exchange: Exchange
            
        Returns:
            True if order sent successfully
        """
        return self.make_order(symbol, Direction.SHORT, volume, price, exchange=exchange)
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get order statistics
        
        Returns:
            Dictionary with order statistics
        """
        return {
            "orders_sent": self.orders_sent,
            "orders_successful": self.orders_successful,
            "orders_failed": self.orders_failed,
            "success_rate": (
                self.orders_successful / self.orders_sent * 100 
                if self.orders_sent > 0 else 0
            )
        }
    
    def reset_statistics(self) -> None:
        """Reset order statistics"""
        self.orders_sent = 0
        self.orders_successful = 0
        self.orders_failed = 0
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Convenience functions for direct usage
def create_tcp_client(host: str = "127.0.0.1", port: int = 8888) -> TcpOrderClient:
    """
    Create and return a TCP order client
    
    Args:
        host: Server host
        port: Server port
        
    Returns:
        TcpOrderClient instance
    """
    return TcpOrderClient(host, port)


def quick_connect_and_order(
    symbol: str,
    direction: Direction,
    volume: float,
    price: float,
    host: str = "127.0.0.1",
    port: int = 8888
) -> bool:
    """
    Quick function to connect and send a single order
    
    Args:
        symbol: Stock symbol
        direction: Order direction
        volume: Order volume
        price: Order price
        host: Server host
        port: Server port
        
    Returns:
        True if successful
    """
    with TcpOrderClient(host, port) as client:
        return client.make_order(symbol, direction, volume, price)