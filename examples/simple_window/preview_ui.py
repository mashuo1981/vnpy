import sys
from PySide6 import QtWidgets, QtCore
from PySide6.QtUiTools import QUiLoader
import qdarkstyle

def preview_ui(ui_file_path):
    app = QtWidgets.QApplication(sys.argv)
    
    # 应用 qdarkstyle
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside6"))
    
    # 加载UI文件
    loader = QUiLoader()
    file = QtCore.QFile(ui_file_path)
    file.open(QtCore.QFile.ReadOnly)
    window = loader.load(file)
    file.close()
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ui_file = sys.argv[1]
    else:
        ui_file = "trader.ui"  # 默认文件名
    preview_ui(ui_file)