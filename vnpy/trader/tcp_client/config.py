"""
TCP Client Configuration
Configure TCP client settings for the trading assistant
"""

# TCP Server Configuration
TCP_HOST = "127.0.0.1"
TCP_PORT = 8888

# Order Settings
ENABLE_TCP_ORDERS = True  # Set to True to use TCP client, False to use gateway
DEFAULT_EXCHANGE = "SSE"  # Default exchange for orders

# Connection Settings
CONNECTION_TIMEOUT = 5  # Connection timeout in seconds
AUTO_RETRY = True  # Auto retry on connection failure
MAX_RETRY_ATTEMPTS = 3  # Maximum retry attempts

# Debug Settings
DEBUG_MODE = False  # Enable debug logging
SHOW_TCP_MESSAGES = True  # Show TCP order messages in console

def get_tcp_config():
    """Get TCP configuration as dictionary"""
    return {
        "host": TCP_HOST,
        "port": TCP_PORT,
        "enable_tcp_orders": ENABLE_TCP_ORDERS,
        "default_exchange": DEFAULT_EXCHANGE,
        "connection_timeout": CONNECTION_TIMEOUT,
        "auto_retry": AUTO_RETRY,
        "max_retry_attempts": MAX_RETRY_ATTEMPTS,
        "debug_mode": DEBUG_MODE,
        "show_tcp_messages": SHOW_TCP_MESSAGES
    }

def update_tcp_config(**kwargs):
    """Update TCP configuration"""
    global TCP_HOST, TCP_PORT, ENABLE_TCP_ORDERS, DEFAULT_EXCHANGE
    global CONNECTION_TIMEOUT, AUTO_RETRY, MAX_RETRY_ATTEMPTS
    global DEBUG_MODE, SHOW_TCP_MESSAGES
    
    if "host" in kwargs:
        TCP_HOST = kwargs["host"]
    if "port" in kwargs:
        TCP_PORT = kwargs["port"]
    if "enable_tcp_orders" in kwargs:
        ENABLE_TCP_ORDERS = kwargs["enable_tcp_orders"]
    if "default_exchange" in kwargs:
        DEFAULT_EXCHANGE = kwargs["default_exchange"]
    if "connection_timeout" in kwargs:
        CONNECTION_TIMEOUT = kwargs["connection_timeout"]
    if "auto_retry" in kwargs:
        AUTO_RETRY = kwargs["auto_retry"]
    if "max_retry_attempts" in kwargs:
        MAX_RETRY_ATTEMPTS = kwargs["max_retry_attempts"]
    if "debug_mode" in kwargs:
        DEBUG_MODE = kwargs["debug_mode"]
    if "show_tcp_messages" in kwargs:
        SHOW_TCP_MESSAGES = kwargs["show_tcp_messages"]