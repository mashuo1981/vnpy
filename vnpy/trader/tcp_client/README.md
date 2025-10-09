# TCP客户端功能说明

这个模块基于`tcp_client_demo.cpp`实现了Python版本的TCP客户端功能，为vnpy交易平台提供直接的TCP订单发送能力。

## 功能特性

- **完整的TCP连接管理**: 支持连接、断开、自动重连
- **订单发送功能**: 支持买入、卖出订单
- **结构体兼容**: 与C++版本的数据结构完全兼容
- **UI集成**: 已集成到交易助手界面中
- **统计功能**: 实时统计订单发送成功率
- **错误处理**: 完善的异常处理和错误提示

## 模块结构

```
tcp_client/
├── __init__.py          # 模块导入
├── tcp_client.py        # 核心TCP客户端实现
├── tcp_order.py         # 高级订单客户端接口
├── example.py           # 使用示例
├── test_tcp_client.py   # 测试脚本
└── tcp_client_demo.cpp  # C++参考实现
```

## 核心类说明

### TcpClient
基础TCP客户端类，提供底层TCP连接和数据传输功能。

```python
from vnpy.trader.tcp_client import TcpClient

client = TcpClient("127.0.0.1", 8888)
if client.connect():
    response = client.make_order(order_request)
    client.disconnect()
```

### TcpOrderClient  
高级订单客户端类，提供简化的订单发送接口。

```python
from vnpy.trader.tcp_client import TcpOrderClient
from vnpy.trader.constant import Direction

with TcpOrderClient("127.0.0.1", 8888) as client:
    # 买入订单
    client.buy("600000", 100, 10.50)
    # 卖出订单  
    client.sell("000001", 200, 15.30)
```

## 快速开始

### 1. 基本使用

```python
from vnpy.trader.tcp_client import TcpOrderClient
from vnpy.trader.constant import Direction

# 创建客户端
client = TcpOrderClient("127.0.0.1", 8888)

# 连接服务器
if client.connect():
    # 发送买入订单
    success = client.make_order(
        symbol="600000",
        direction=Direction.LONG,
        volume=100,
        price=10.50
    )
    
    # 获取统计信息
    stats = client.get_statistics()
    print(f"订单统计: {stats}")
    
    # 断开连接
    client.disconnect()
```

### 2. 使用上下文管理器

```python
from vnpy.trader.tcp_client import TcpOrderClient

with TcpOrderClient("127.0.0.1", 8888) as client:
    client.buy("600000", 100, 10.50)
    client.sell("000001", 200, 15.30)
# 自动断开连接
```

### 3. 便捷函数

```python
from vnpy.trader.tcp_client import quick_connect_and_order
from vnpy.trader.constant import Direction

# 单行发送订单
success = quick_connect_and_order(
    symbol="600000",
    direction=Direction.LONG,
    volume=100,
    price=10.50
)
```

# TCP客户端功能说明

这个模块基于`tcp_client_demo.cpp`实现了Python版本的TCP客户端功能，为vnpy交易平台提供直接的TCP订单发送能力。

## 功能特性

- **一键下单**: 点击下单按钮即可自动连接服务器并发送订单
- **自动连接管理**: 每次下单时自动建立和关闭连接
- **完整的订单发送功能**: 支持买入、卖出订单
- **结构体兼容**: 与C++版本的数据结构完全兼容
- **智能回退**: TCP失败时自动回退到网关方式
- **灵活配置**: 通过配置文件轻松调整连接参数
- **详细日志**: 实时显示订单发送状态

## 模块结构

```
tcp_client/
├── __init__.py              # 模块导入
├── tcp_client.py            # 核心TCP客户端实现
├── tcp_order.py             # 高级订单客户端接口
├── config.py                # 配置管理
├── README.md                # 说明文档
└── tcp_client_demo.cpp      # C++参考实现
```

## 快速开始

### 1. 默认配置使用

无需任何配置，直接使用交易助手界面：

1. 启动交易助手
2. 输入股票代码、价格、数量
3. 点击"下单"按钮
4. 系统自动连接TCP服务器(127.0.0.1:8888)并发送订单

### 2. 自定义配置

修改TCP连接参数：

```python
from vnpy.trader.tcp_client import update_tcp_config

# 配置生产环境服务器
update_tcp_config(
    host="192.168.1.100",
    port=9999,
    enable_tcp_orders=True
)
```

### 3. 禁用TCP(使用网关)

```python
from vnpy.trader.tcp_client import update_tcp_config

# 禁用TCP，使用传统网关方式
update_tcp_config(enable_tcp_orders=False)
```

## 配置参数

### 基本配置
- **TCP_HOST**: 服务器地址 (默认: "127.0.0.1")
- **TCP_PORT**: 服务器端口 (默认: 8888)
- **ENABLE_TCP_ORDERS**: 是否启用TCP订单 (默认: True)

### 高级配置
- **CONNECTION_TIMEOUT**: 连接超时时间(秒) (默认: 5)
- **AUTO_RETRY**: 是否自动重试 (默认: True)
- **MAX_RETRY_ATTEMPTS**: 最大重试次数 (默认: 3)
- **DEBUG_MODE**: 调试模式 (默认: False)
- **SHOW_TCP_MESSAGES**: 显示TCP消息 (默认: True)

## 工作流程

### 简化的下单流程

1. **用户操作**: 在交易助手界面点击"下单"按钮
2. **自动连接**: 系统自动连接到配置的TCP服务器
3. **发送订单**: 将订单数据发送到服务器
4. **接收响应**: 等待服务器响应
5. **自动断开**: 订单完成后自动关闭连接
6. **显示结果**: 在界面显示订单结果

### 错误处理流程

1. **TCP连接失败**: 自动回退到网关方式
2. **订单发送失败**: 显示错误信息
3. **服务器无响应**: 超时处理并报告错误

## 交易助手UI集成

### 无需额外操作

- ✅ 保持原有界面，无额外控制面板
- ✅ 原有的下单按钮直接支持TCP
- ✅ 自动处理连接和断开
- ✅ 实时显示订单状态

### 状态显示

- 控制台显示详细的订单发送日志
- 成功订单显示: `✓ TCP订单发送成功`
- 失败订单显示: `✗ TCP订单发送失败`
- 自动回退显示: `回退到网关方式发送订单...`

## 高级使用

### 程序化配置

```python
# 在你的代码中配置
from vnpy.trader.tcp_client import update_tcp_config

def setup_production():
    """生产环境配置"""
    update_tcp_config(
        host="192.168.1.100",
        port=9999,
        enable_tcp_orders=True,
        connection_timeout=10,
        debug_mode=False
    )

def setup_development():
    """开发环境配置"""
    update_tcp_config(
        host="127.0.0.1", 
        port=8888,
        enable_tcp_orders=True,
        debug_mode=True,
        show_tcp_messages=True
    )
```

### 直接API调用

```python
from vnpy.trader.tcp_client import TcpOrderClient
from vnpy.trader.constant import Direction

# 直接发送订单(不通过UI)
with TcpOrderClient("127.0.0.1", 8888) as client:
    success = client.buy("600000", 100, 10.50)
    print(f"订单结果: {success}")
```

## 数据结构兼容性

### 完全兼容C++版本

- **FixOrder结构体**: 1392字节，与C++版本完全匹配
- **消息头格式**: 8字节固定头部
- **字节序**: 小端序(Little-endian)
- **字符编码**: UTF-8编码，空字符填充

### 协议格式

```
TCP消息格式:
┌─────────────────┬─────────────────┬─────────────────┐
│   消息类型(4B)   │   消息长度(4B)   │   订单数据      │
├─────────────────┼─────────────────┼─────────────────┤
│ TcpMessageType │    uint32_t     │   FixOrder      │
└─────────────────┴─────────────────┴─────────────────┘
```

## 性能优化

### 连接策略
- **按需连接**: 仅在发送订单时建立连接
- **快速断开**: 订单完成后立即断开，释放资源
- **上下文管理**: 使用Python上下文管理器确保资源清理

### 错误恢复
- **智能回退**: TCP失败时自动使用网关
- **详细日志**: 便于问题诊断和调试
- **异常处理**: 全面的异常捕获和处理

## 测试功能

可以通过以下方式测试TCP客户端功能：

```python
from vnpy.trader.tcp_client import TcpOrderClient
from vnpy.trader.constant import Direction

# 基本连接测试
with TcpOrderClient("127.0.0.1", 8888) as client:
    success = client.buy("600000", 100, 10.50)
    print(f"测试结果: {success}")
```

## 注意事项

### 服务器要求
- 确保TCP订单服务器运行在指定端口
- 服务器必须支持C++版本的协议格式
- 建议使用稳定的网络连接

### 安全考虑
- 仅在可信网络环境中使用
- 考虑加密传输敏感订单信息
- 定期检查服务器连接状态

### 最佳实践
- 在生产环境中测试连接稳定性
- 根据网络条件调整超时参数
- 定期监控订单发送成功率

## 故障排除

### 常见问题

**问题**: 连接失败
**解决**: 检查服务器地址和端口，确认服务器运行状态

**问题**: 订单发送失败
**解决**: 检查订单参数，查看控制台错误信息

**问题**: 没有回退到网关
**解决**: 检查网关配置，确认网关可用性

## 数据结构兼容性

Python实现完全兼容C++版本的数据结构：

### FixOrder结构体
- 总大小与C++版本匹配
- 字段布局完全一致
- 字节对齐严格遵循C++标准

### TCP协议格式
- 消息头: 消息类型(4字节) + 消息长度(4字节)
- 消息体: FixOrder结构体数据
- 响应格式: 结果码(4字节) + 消息文本(256字节)

## 配置参数

### 连接参数
- **host**: 服务器主机地址 (默认: "127.0.0.1")
- **port**: 服务器端口号 (默认: 8888)
- **auto_reconnect**: 自动重连 (默认: True)

### 订单参数
- **symbol**: 股票代码 (如: "600000")
- **direction**: 交易方向 (Direction.LONG/SHORT)
- **volume**: 交易数量
- **price**: 交易价格
- **order_type**: 订单类型 (默认: LIMIT)
- **exchange**: 交易所 (默认: SSE)

## 错误处理

### 连接错误
- 连接超时或失败会返回False
- 支持自动重连机制
- 显示详细错误信息

### 订单错误
- 参数验证 (价格、数量必须大于0)
- 网络异常处理
- 服务器响应解析

## 测试功能

运行测试脚本验证功能：

```bash
cd vnpy/trader/tcp_client
python test_tcp_client.py
```

测试包括:
- 基本连接测试
- 订单发送测试  
- 错误处理测试
- 便捷函数测试

## 性能特性

- **高效的二进制协议**: 直接发送结构体数据
- **最小化网络开销**: 紧凑的数据格式
- **连接复用**: 支持多个订单使用同一连接
- **异步处理**: 不阻塞UI线程

## 注意事项

1. **服务器要求**: 需要兼容的TCP订单服务器运行在指定端口
2. **网络安全**: 确保网络连接安全，避免明文传输敏感信息
3. **错误重试**: 网络异常时建议实现适当的重试机制
4. **资源管理**: 及时关闭不需要的连接以释放资源

## 扩展功能

### 响应回调
```python
def on_response(response):
    print(f"订单响应: {response.result_code} - {response.message}")

client = TcpOrderClient(on_response_callback=on_response)
```

### 自定义配置
```python
client = TcpOrderClient(
    host="192.168.1.100",
    port=9999,
    auto_reconnect=True
)
```

### 批量订单
```python
orders = [
    ("600000", Direction.LONG, 100, 10.50),
    ("000001", Direction.SHORT, 200, 15.30),
]

with TcpOrderClient() as client:
    for symbol, direction, volume, price in orders:
        client.make_order(symbol, direction, volume, price)
```