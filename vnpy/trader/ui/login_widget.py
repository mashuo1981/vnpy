"""
Login Widget for vnpy trading system
Based on login.ui design
"""

from typing import Dict, Any, Optional
import json
import os

try:
    from .qt import QtCore, QtGui, QtWidgets
except ImportError:
    # For testing purposes, use direct PySide6 imports
    from PySide6 import QtCore, QtGui, QtWidgets


class LoginWidget(QtWidgets.QFrame):
    """
    Login widget based on login.ui
    Provides user authentication interface
    """
    
    # Signal emitted when login is successful
    login_successful = QtCore.Signal(dict)
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """Initialize login widget"""
        super().__init__(parent)
        
        self.setObjectName("Frame_login")
        self.setWindowTitle("Login")
        self.setFixedSize(400, 300)
        
        # Store user credentials
        self.user_data: Dict[str, Any] = {}
        
        # Setup UI components
        self.init_ui()
        self.load_settings()
        
    def init_ui(self) -> None:
        """Initialize the user interface based on login.ui"""
        
        # Username input field
        self.lineEdit_name = QtWidgets.QLineEdit(self)
        self.lineEdit_name.setGeometry(QtCore.QRect(170, 140, 113, 24))
        self.lineEdit_name.setObjectName("lineEdit_name")
        self.lineEdit_name.setPlaceholderText("请输入用户名")
        
        # Password input field
        self.lineEdit_password = QtWidgets.QLineEdit(self)
        self.lineEdit_password.setGeometry(QtCore.QRect(170, 170, 113, 24))
        self.lineEdit_password.setObjectName("lineEdit_password")
        self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.lineEdit_password.setPlaceholderText("请输入密码")
        
        # Restore interface checkbox
        self.checkBox_restore = QtWidgets.QCheckBox(self)
        self.checkBox_restore.setGeometry(QtCore.QRect(170, 210, 111, 24))
        self.checkBox_restore.setObjectName("checkBox_restore")
        self.checkBox_restore.setText("恢复上次界面")
        self.checkBox_restore.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        
        # Login button
        self.pushButton_login = QtWidgets.QPushButton(self)
        self.pushButton_login.setGeometry(QtCore.QRect(100, 240, 181, 31))
        self.pushButton_login.setObjectName("pushButton_login")
        self.pushButton_login.setText("登录")
        self.pushButton_login.setDefault(True)  # Make it the default button
        
        # Username label
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(100, 140, 41, 20))
        self.label.setObjectName("label")
        self.label.setText("用户名")
        
        # Password label
        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setGeometry(QtCore.QRect(110, 170, 41, 20))
        self.label_2.setObjectName("label_2")
        self.label_2.setText("密码")
        
        # Connect signals
        self.pushButton_login.clicked.connect(self.on_login_clicked)
        self.lineEdit_password.returnPressed.connect(self.on_login_clicked)
        self.lineEdit_name.returnPressed.connect(self.focus_password)
        
        # Set window properties
        self.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        
    def focus_password(self) -> None:
        """Move focus to password field when Enter is pressed in username field"""
        self.lineEdit_password.setFocus()
        
    def on_login_clicked(self) -> None:
        """Handle login button click"""
        username = self.lineEdit_name.text().strip()
        password = self.lineEdit_password.text()
        restore_interface = self.checkBox_restore.isChecked()
        
        # Validate input
        if not username:
            QtWidgets.QMessageBox.warning(self, "登录错误", "请输入用户名")
            self.lineEdit_name.setFocus()
            return
            
        if not password:
            QtWidgets.QMessageBox.warning(self, "登录错误", "请输入密码")
            self.lineEdit_password.setFocus()
            return
        
        # Here you can add actual authentication logic
        # For now, we'll accept any non-empty credentials
        if self.authenticate_user(username, password):
            # Prepare user data
            self.user_data = {
                "username": username,
                "password": password,
                "restore_interface": restore_interface
            }
            
            # Save settings
            self.save_settings()
            
            # Emit login successful signal
            self.login_successful.emit(self.user_data)
            
            # Show success message
            QtWidgets.QMessageBox.information(self, "登录成功", f"欢迎用户 {username}！")
            
            # Close or hide the widget
            if self.parent():
                self.close()
            else:
                self.hide()
        else:
            QtWidgets.QMessageBox.critical(self, "登录失败", "用户名或密码错误，请重试")
            self.lineEdit_password.clear()
            self.lineEdit_password.setFocus()
            
    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate user credentials
        Override this method to implement actual authentication logic
        """
        # Simple demo authentication - accept any non-empty credentials
        # In production, this should connect to a real authentication system
        return len(username) >= 3 and len(password) >= 6
        
    def get_settings_file(self) -> str:
        """Get settings file path"""
        home_dir = os.path.expanduser("~")
        vnpy_dir = os.path.join(home_dir, ".vnpy")
        return os.path.join(vnpy_dir, "login_settings.json")
        
    def save_settings(self) -> None:
        """Save login settings (excluding password for security)"""
        try:
            settings_dir = os.path.dirname(self.get_settings_file())
            os.makedirs(settings_dir, exist_ok=True)
            
            settings = {
                "username": self.lineEdit_name.text().strip(),
                "restore_interface": self.checkBox_restore.isChecked()
                # Note: Password is not saved for security reasons
            }
            
            with open(self.get_settings_file(), "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Failed to save login settings: {e}")
            
    def load_settings(self) -> None:
        """Load saved login settings"""
        try:
            settings_file = self.get_settings_file()
            if not os.path.exists(settings_file):
                return
                
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                
            # Restore username
            if "username" in settings:
                self.lineEdit_name.setText(settings["username"])
                
            # Restore interface checkbox
            if "restore_interface" in settings:
                self.checkBox_restore.setChecked(settings["restore_interface"])
                
        except Exception as e:
            print(f"Failed to load login settings: {e}")
            
    def clear_fields(self) -> None:
        """Clear all input fields"""
        self.lineEdit_name.clear()
        self.lineEdit_password.clear()
        self.checkBox_restore.setChecked(False)
        
    def set_focus_to_first_empty(self) -> None:
        """Set focus to the first empty field"""
        if not self.lineEdit_name.text().strip():
            self.lineEdit_name.setFocus()
        else:
            self.lineEdit_password.setFocus()
            
    def get_user_data(self) -> Dict[str, Any]:
        """Get current user data"""
        return self.user_data.copy()
        
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Handle show event"""
        super().showEvent(event)
        # Set appropriate focus when window is shown
        self.set_focus_to_first_empty()


class LoginDialog(QtWidgets.QDialog):
    """
    Login dialog wrapper for modal login
    """
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """Initialize login dialog"""
        super().__init__(parent)
        
        self.setWindowTitle("vnpy登录")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        # Remove window frame buttons except close
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog |
            QtCore.Qt.WindowType.WindowTitleHint |
            QtCore.Qt.WindowType.WindowCloseButtonHint
        )
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add login widget
        self.login_widget = LoginWidget()
        layout.addWidget(self.login_widget)
        
        # Connect signals
        self.login_widget.login_successful.connect(self.on_login_successful)
        
        # Store user data
        self.user_data: Dict[str, Any] = {}
        
    def on_login_successful(self, user_data: Dict[str, Any]) -> None:
        """Handle successful login"""
        self.user_data = user_data
        self.accept()  # Close dialog with success
        
    def get_user_data(self) -> Dict[str, Any]:
        """Get user data after successful login"""
        return self.user_data.copy()
        
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle close event"""
        # Clear password field when closing
        self.login_widget.lineEdit_password.clear()
        super().closeEvent(event)


def show_login_dialog(parent: Optional[QtWidgets.QWidget] = None) -> Dict[str, Any]:
    """
    Show login dialog and return user data if successful.
    
    Args:
        parent: Parent widget
        
    Returns:
        User data dictionary if login successful, empty dict if cancelled
    """
    dialog = LoginDialog(parent)
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dialog.get_user_data()
    return {}


def create_login_widget(parent: Optional[QtWidgets.QWidget] = None) -> LoginWidget:
    """
    Create and return a login widget instance.
    
    Args:
        parent: Parent widget
        
    Returns:
        LoginWidget instance
    """
    return LoginWidget(parent)


if __name__ == "__main__":
    """Test the login widget"""
    import sys
    
    app = QtWidgets.QApplication(sys.argv)
    
    # Test login dialog
    def test_login():
        user_data = show_login_dialog()
        if user_data:
            print(f"Login successful!")
            print(f"Username: {user_data['username']}")
            print(f"Restore interface: {user_data['restore_interface']}")
        else:
            print("Login cancelled")
        app.quit()
    
    # Show login dialog
    QtCore.QTimer.singleShot(100, test_login)
    
    sys.exit(app.exec())