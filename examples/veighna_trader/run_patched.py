#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复talib导入问题的启动脚本
"""

import os
import sys

def patch_talib_import():
    """修复talib导入问题"""
    
    # 创建一个假的talib模块来避免导入错误
    class FakeTalib:
        def __getattr__(self, name):
            def dummy_func(*args, **kwargs):
                print(f"警告: talib.{name} 功能在打包版本中不可用")
                return None
            return dummy_func
    
    # 将假的talib模块注入到sys.modules中
    sys.modules['talib'] = FakeTalib()
    sys.modules['talib.stream'] = FakeTalib()
    sys.modules['talib.abstract'] = FakeTalib()
    
    print("OK talib导入问题已修复")

def fix_stdio():
    """修复stdio问题"""
    
    if getattr(sys, 'frozen', False):
        # 在打包环境中
        if sys.stdin is None:
            sys.stdin = open(os.devnull, 'r')
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w')
    
    print("OK stdio问题已修复")

def main():
    """主函数"""
    
    try:
        print("正在修复兼容性问题...")
        
        # 修复stdio问题
        fix_stdio()
        
        # 修复talib导入问题
        patch_talib_import()
        
        # 设置环境变量
        os.environ.setdefault('VNPY_LOG_CONSOLE', 'false')
        os.environ.setdefault('VNPY_LOG_FILE', 'false')
        os.environ['QT_LOGGING_RULES'] = 'qt.qpa.windows.debug=false'
        
        print("正在启动VeighNa交易平台...")
        
        # 导入核心模块
        from vnpy.event import EventEngine
        from vnpy.trader.engine import MainEngine
        from vnpy.trader.ui import CustomMainWindow, create_qapp
        
        print("OK 核心模块导入成功")
        
        # 创建应用
        qapp = create_qapp()
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        
        print("OK 引擎创建成功")
        
        # 创建主窗口
        main_window = CustomMainWindow(main_engine, event_engine)
        main_window.show()
        
        print("OK 界面启动成功")
        print("SUCCESS VeighNa交易平台已启动!")
        
        # 运行应用
        qapp.exec()
        
    except Exception as e:
        print(f"ERROR 启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 在打包环境中不使用input()
        if not getattr(sys, 'frozen', False):
            input("按回车键退出...")

if __name__ == "__main__":
    main()