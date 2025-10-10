# Login Widget 说明文档

## 📋 概述

根据 `login.ui` 文件创建了完整的登录组件，包含用户认证界面和相关功能。

## 📁 文件结构

```
vnpy/trader/ui/
├── login_widget.py           # 主要登录组件
└── test_login_widget.py      # 测试示例文件
```

## 🎯 主要组件

### 1. LoginWidget 类
- 基于 `login.ui` 设计的主要登录界面
- 包含用户名、密码输入和界面恢复选项
- 支持设置保存和加载功能

### 2. LoginDialog 类  
- 模态对话框包装器
- 适用于需要阻塞式登录的场景

### 3. 便捷函数
- `show_login_dialog()` - 快速显示登录对话框
- `create_login_widget()` - 创建登录组件实例

## ✨ 功能特性

### 🔐 安全特性
- ✅ 密码字段自动隐藏
- ✅ 密码不保存到配置文件
- ✅ 输入验证和错误提示

### 💾 设置管理
- ✅ 自动保存用户名
- ✅ 记住界面恢复偏好
- ✅ 配置文件存储：`~/.vnpy/login_settings.json`

### 🎨 用户体验
- ✅ 智能焦点设置
- ✅ Enter键快速登录
- ✅ 友好的错误和成功提示
- ✅ Qt信号机制支持

## 🚀 使用方法

### 作为独立组件
```python
from vnpy.trader.ui.login_widget import LoginWidget

widget = LoginWidget()
widget.login_successful.connect(lambda data: print(f"User: {data}"))
widget.show()
```

### 作为模态对话框
```python
from vnpy.trader.ui.login_widget import show_login_dialog

user_data = show_login_dialog()
if user_data:
    print(f"Login successful: {user_data['username']}")
    print(f"Restore interface: {user_data['restore_interface']}")
```

### 自定义认证逻辑
```python
class CustomLoginWidget(LoginWidget):
    def authenticate_user(self, username: str, password: str) -> bool:
        # 实现自定义认证逻辑
        return your_auth_function(username, password)
```

## 📊 返回数据格式

成功登录后返回的用户数据：
```python
{
    "username": "user123",           # 用户名
    "password": "password123",       # 密码（使用后应立即清除）
    "restore_interface": True        # 是否恢复界面
}
```

## 🧪 测试

运行测试文件验证功能：
```bash
python test_login_widget.py dialog    # 测试对话框模式
python test_login_widget.py widget    # 测试独立组件
python test_login_widget.py custom    # 测试自定义认证
```

## 🔧 UI布局（基于login.ui）

- **窗口大小**: 400x300 像素
- **用户名输入**: 位置 (170, 140)，大小 113x24
- **密码输入**: 位置 (170, 170)，大小 113x24  
- **恢复选项**: 位置 (170, 210)，大小 111x24
- **登录按钮**: 位置 (100, 240)，大小 181x31
- **标签**: "用户名" 和 "密码" 标签正确定位

## 🎨 界面特色

- 🎯 完全遵循 `login.ui` 设计规范
- 📱 响应式输入验证
- 🔄 智能焦点管理
- 💫 流畅的用户交互体验

登录组件已完成，可直接集成到vnpy交易系统中使用！