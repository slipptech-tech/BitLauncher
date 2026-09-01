import sys
import os
import json
import requests
import psutil
import shutil
import minecraft_launcher_lib
import subprocess

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QPixmap, QImage
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSlider, QStackedWidget,
    QFrame, QScrollArea, QCheckBox, QMessageBox, QProgressBar, QFileDialog,
    QRadioButton, QListWidget, QListWidgetItem, QDialog, QTextEdit
)

# Cross-platform paths (Windows / Linux)
def get_resource_dir():
    # Works both from source and from a PyInstaller build.
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

def get_app_data_dir():
    if sys.platform.startswith("linux"):
        base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
    elif os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.join(os.path.expanduser("~"), ".local", "share")
    path = os.path.join(base, "BitLauncher")
    os.makedirs(path, exist_ok=True)
    return path

RESOURCE_DIR = get_resource_dir()
APP_DATA_DIR = get_app_data_dir()
PNG_DIR = os.path.join(RESOURCE_DIR, "launch_png")
DEFAULT_GAME_DIR = os.path.join(APP_DATA_DIR, ".minecraft")
CONFIG_FILE = os.path.join(APP_DATA_DIR, "launcher_config.json")

def open_folder(path):
    os.makedirs(path, exist_ok=True)
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform.startswith("linux"):
        subprocess.Popen(["xdg-open", path])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        raise RuntimeError(f"Unsupported operating system: {sys.platform}")

# Styles & Palette
C_PANEL = "rgba(17, 19, 31, 0.95)"
C_PANEL_SOLID = "#11131F"
C_ACCENT = "#00d2ff"
C_ACCENT_HOVER = "#33ddff"
C_TEXT_MAIN = "#FFFFFF"
C_TEXT_SEC = "#8F96A3"
C_BORDER = "rgba(255, 255, 255, 0.08)"

# Localization Dictionaries
LANGUAGES = {
    "RU": {
        "nav_play": "🎮 Запуск игры",
        "nav_mods": "📦 Моды",
        "nav_settings": "⚙️ Настройки",
        "welcome": "С возвращением!",
        "welcome_sub": "Выбирайте версию, подключайте Fabric и отправляйтесь в игру.",
        "version": "ВЕРСИЯ ИГРЫ",
        "mods": "МОДИФИКАЦИИ",
        "use_fabric": "Использовать Fabric",
        "btn_launch": "ИГРАТЬ",
        "ready": "Готов к запуску",
        "open_folders": "📁 Папки и Логи",
        "search_mods": "Поиск на Modrinth",
        "installed_mods": "Установленные моды",
        "search_placeholder": "Поиск модов в базе Modrinth...",
        "btn_find": "Найти",
        "refresh": "Обновить",
        "settings_title": "Параметры и Настройки",
        "acc_mgmt": "Управление Аккаунтом",
        "acc_offline": "Офлайн профиль",
        "acc_ms": "Microsoft (Лицензия)",
        "nick_placeholder": "Введите ваш никнейм...",
        "btn_apply_acc": "Применить аккаунт",
        "game_dir": "Директория игры (.minecraft)",
        "java_path": "Путь к Java Executable",
        "browse": "Обзор",
        "ram_alloc": "Выделение оперативной памяти (RAM)",
        "resolution": "Разрешение экрана",
        "auto": "Автоматически",
        "close_on_launch": "Закрывать лаунчер при запуске игры",
        "clean_logs_exit": "Автоматически очищать логи игры после работы",
        "jvm_args": "Аргументы JVM",
        "lang_select": "Язык интерфейса / Language",
        "quick_clean": "Очистка кэша и логов",
        "btn_clean_logs": "Очистить логи",
        "btn_clean_cache": "Очистить кэш",
        "folder_main": "Главная (.minecraft)",
        "folder_mods": "Моды (mods)",
        "folder_saves": "Миры (saves)",
        "folder_screens": "Скриншоты",
        "folder_logs": "Логи (logs)",
        "view_logs": "📋 Просмотр логов"
    },
    "EN": {
        "nav_play": "🎮 Play Game",
        "nav_mods": "📦 Mods",
        "nav_settings": "⚙️ Settings",
        "welcome": "Welcome back!",
        "welcome_sub": "Select your version, enable Fabric, and jump into the game.",
        "version": "GAME VERSION",
        "mods": "MODIFICATIONS",
        "use_fabric": "Use Fabric Loader",
        "btn_launch": "PLAY NOW",
        "ready": "Ready to launch",
        "open_folders": "📁 Folders & Logs",
        "search_mods": "Modrinth Search",
        "installed_mods": "Installed Mods",
        "search_placeholder": "Search mods on Modrinth...",
        "btn_find": "Search",
        "refresh": "Refresh",
        "settings_title": "Preferences & Settings",
        "acc_mgmt": "Account Management",
        "acc_offline": "Offline Profile",
        "acc_ms": "Microsoft (License)",
        "nick_placeholder": "Enter nickname...",
        "btn_apply_acc": "Apply Account",
        "game_dir": "Game Directory (.minecraft)",
        "java_path": "Java Executable Path",
        "browse": "Browse",
        "ram_alloc": "RAM Allocation",
        "resolution": "Screen Resolution",
        "auto": "Automatic",
        "close_on_launch": "Close launcher on game start",
        "clean_logs_exit": "Auto-clean logs on game exit",
        "jvm_args": "JVM Arguments",
        "lang_select": "Language / Язык",
        "quick_clean": "Clear Cache & Logs",
        "btn_clean_logs": "Clear Logs",
        "btn_clean_cache": "Clear Cache",
        "folder_main": "Root (.minecraft)",
        "folder_mods": "Mods Folder",
        "folder_saves": "Saves (Worlds)",
        "folder_screens": "Screenshots",
        "folder_logs": "Logs Folder",
        "view_logs": "📋 View Game Logs"
    },
    "UA": {
        "nav_play": "🎮 Запуск гри",
        "nav_mods": "📦 Моди",
        "nav_settings": "⚙️ Налаштування",
        "welcome": "З поверненням!",
        "welcome_sub": "Обирайте версію, підключайте Fabric та вирушайте у гру.",
        "version": "ВЕРСІЯ ГРИ",
        "mods": "МОДИФІКАЦІЇ",
        "use_fabric": "Використовувати Fabric",
        "btn_launch": "ГРАТИ",
        "ready": "Готово до запуску",
        "open_folders": "📁 Папки та Логи",
        "search_mods": "Пошук на Modrinth",
        "installed_mods": "Встановлені моди",
        "search_placeholder": "Пошук модів у базі Modrinth...",
        "btn_find": "Знайти",
        "refresh": "Оновити",
        "settings_title": "Параметри та Налаштування",
        "acc_mgmt": "Управління Акаунтом",
        "acc_offline": "Офлайн профіль",
        "acc_ms": "Microsoft (Ліцензія)",
        "nick_placeholder": "Введіть ваш нікнейм...",
        "btn_apply_acc": "Застосувати акаунт",
        "game_dir": "Директорія гри (.minecraft)",
        "java_path": "Шлях до Java Executable",
        "browse": "Огляд",
        "ram_alloc": "Виділення оперативної пам'яті (RAM)",
        "resolution": "Роздільна здатність екрана",
        "auto": "Автоматично",
        "close_on_launch": "Закривати лаунчер при запуску гри",
        "clean_logs_exit": "Автоматично очищати логи після гри",
        "jvm_args": "Аргументи JVM",
        "lang_select": "Мова інтерфейсу / Language",
        "quick_clean": "Очищення кешу та логів",
        "btn_clean_logs": "Очистити логи",
        "btn_clean_cache": "Очистити кеш",
        "folder_main": "Головна (.minecraft)",
        "folder_mods": "Моди (mods)",
        "folder_saves": "Світи (saves)",
        "folder_screens": "Скріншоти",
        "folder_logs": "Логи (logs)",
        "view_logs": "📋 Перегляд логів"
    }
}

def load_local_pixmap(file_name, width=None, height=None):
    path = os.path.join(PNG_DIR, file_name)
    if os.path.exists(path):
        pix = QPixmap(path)
        if width and height:
            return pix.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif width:
            return pix.scaledToWidth(width, Qt.SmoothTransformation)
        elif height:
            return pix.scaledToHeight(height, Qt.SmoothTransformation)
        return pix
    return None

def get_pixmap_from_url(url, size=64):
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            image = QImage.fromData(response.content)
            pix = QPixmap.fromImage(image)
            return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    except Exception:
        pass
    placeholder = QPixmap(size, size)
    placeholder.fill(QColor(30, 33, 48))
    return placeholder

class LogViewerDialog(QDialog):
    def __init__(self, log_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Minecraft Game Logs")
        self.resize(750, 500)
        self.setStyleSheet(f"background-color: {C_PANEL_SOLID}; color: #FFF;")

        layout = QVBoxLayout(self)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #0B0D17;
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #A9B7C6;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.text_area)

        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    self.text_area.setText(f.read())
            except Exception as e:
                self.text_area.setText(f"Error reading log file: {e}")
        else:
            self.text_area.setText("Log file not found (latest.log). Launch the game first.")

class VersionLoaderThread(QThread):
    versions_loaded = Signal(list)

    def run(self):
        try:
            versions = minecraft_launcher_lib.utils.get_version_list()
            releases = [v["id"] for v in versions if v["type"] == "release"]
            self.versions_loaded.emit(releases)
        except Exception:
            self.versions_loaded.emit(["1.20.4", "1.20.2", "1.20.1", "1.19.4", "1.18.2", "1.16.5", "1.12.2"])

class GameLaunchThread(QThread):
    progress_signal = Signal(str, int)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, username, version, ram_gb, use_fabric, game_dir, resolution, jvm_args, custom_java=None):
        super().__init__()
        self.username = username
        self.version = version
        self.ram_gb = ram_gb
        self.use_fabric = use_fabric
        self.game_dir = game_dir
        self.resolution = resolution
        self.jvm_args = jvm_args
        self.custom_java = custom_java

    def run(self):
        try:
            target_version = self.version

            if self.use_fabric:
                self.progress_signal.emit("Fabric Loader Check...", 10)
                if not minecraft_launcher_lib.fabric.is_fabric_installed(self.game_dir, self.version):
                    self.progress_signal.emit("Installing Fabric...", 20)
                    minecraft_launcher_lib.fabric.install_fabric(self.version, self.game_dir)
                
                installed = minecraft_launcher_lib.utils.get_installed_versions(self.game_dir)
                for v in installed:
                    if "fabric" in v["id"].lower() and self.version in v["id"]:
                        target_version = v["id"]
                        break

            options = {
                "username": self.username,
                "uuid": "", "token": "",
                "jvmArguments": [f"-Xmx{self.ram_gb}G", f"-Xms2G"]
            }

            if self.custom_java and os.path.exists(self.custom_java):
                options["executablePath"] = self.custom_java

            if self.jvm_args.strip():
                options["jvmArguments"].extend(self.jvm_args.strip().split())

            if self.resolution not in ["Автоматически", "Automatic"]:
                res_parts = self.resolution.split("x")
                if len(res_parts) == 2:
                    options["gameWidth"] = res_parts[0]
                    options["gameHeight"] = res_parts[1]

            def set_status(status): self.progress_signal.emit(status, 50)
            def set_progress(val): self.progress_signal.emit("Downloading assets...", int(val))
            callback = {"setStatus": set_status, "setProgress": set_progress}

            self.progress_signal.emit("Syncing files...", 30)
            minecraft_launcher_lib.install.install_minecraft_version(self.version, self.game_dir, callback=callback)

            self.progress_signal.emit("Starting Game...", 95)
            cmd = minecraft_launcher_lib.command.get_minecraft_command(target_version, self.game_dir, options)
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.Popen(cmd, startupinfo=startupinfo)
            self.progress_signal.emit("Launched!", 100)
            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))

class ModSearchThread(QThread):
    results_signal = Signal(list)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        url = f"https://api.modrinth.com/v2/search?query={self.query}&limit=20&facets=[[\"project_type:mod\"]]"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                self.results_signal.emit(res.json().get("hits", []))
            else: self.results_signal.emit([])
        except Exception: self.results_signal.emit([])

class ModDownloadThread(QThread):
    status_signal = Signal(str)

    def __init__(self, project_id, mod_name, target_dir):
        super().__init__()
        self.project_id = project_id
        self.mod_name = mod_name
        self.target_dir = target_dir

    def run(self):
        try:
            self.status_signal.emit(f"Fetching {self.mod_name}...")
            res = requests.get(f"https://api.modrinth.com/v2/project/{self.project_id}/version", timeout=5)
            if res.status_code == 200 and res.json():
                file_info = res.json()[0]["files"][0]
                self.status_signal.emit(f"Downloading {file_info['filename']}...")
                data = requests.get(file_info['url']).content
                mods_folder = os.path.join(self.target_dir, "mods")
                os.makedirs(mods_folder, exist_ok=True)
                with open(os.path.join(mods_folder, file_info['filename']), "wb") as f:
                    f.write(data)
                self.status_signal.emit(f"Installed: {self.mod_name}!")
            else: self.status_signal.emit("Download error.")
        except Exception: self.status_signal.emit("Download failed.")

class GlassFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {C_PANEL};
                border: 1px solid {C_BORDER};
                border-radius: 14px;
            }}
        """)

class NavButton(QPushButton):
    def __init__(self, text, icon_str, parent=None):
        super().__init__(f"{icon_str}  {text}", parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; border: none; color: {C_TEXT_SEC};
                font-size: 14px; font-weight: 600; text-align: left; padding-left: 20px;
                border-radius: 10px; margin-right: 12px;
            }}
            QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.05); color: #fff; }}
            QPushButton:checked {{ background-color: rgba(0, 210, 255, 0.15); color: {C_ACCENT}; font-weight: 700; }}
        """)

class ModCard(GlassFrame):
    def __init__(self, title, desc, icon_url, project_id, download_cb):
        super().__init__()
        self.download_cb = download_cb
        self.project_id = project_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(54, 54)
        self.lbl_icon.setPixmap(get_pixmap_from_url(icon_url, 54))
        self.lbl_icon.setStyleSheet("border-radius: 10px; background: rgba(0, 0, 0, 0.3); border: none;")
        layout.addWidget(self.lbl_icon)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #fff; border: none;")
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(f"font-size: 12px; color: {C_TEXT_SEC}; border: none;")
        lbl_desc.setWordWrap(True)
        info_layout.addWidget(lbl_title)
        info_layout.addWidget(lbl_desc)
        layout.addLayout(info_layout, 4)

        self.btn_get = QPushButton("Install")
        self.btn_get.setFixedSize(110, 36)
        self.btn_get.setCursor(Qt.PointingHandCursor)
        self.btn_get.setStyleSheet(f"""
            QPushButton {{
                background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%);
                border: none; border-radius: 8px; color: white; font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{ background: linear-gradient(135deg, #38F9D7 0%, #0072FF 100%); }}
        """)
        self.btn_get.clicked.connect(lambda: self.download_cb(self.project_id, title))
        layout.addWidget(self.btn_get, 1, Qt.AlignVCenter)

class LocalModItemWidget(QWidget):
    def __init__(self, filename, mods_dir, refresh_cb):
        super().__init__()
        self.filename = filename
        self.mods_dir = mods_dir
        self.refresh_cb = refresh_cb

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        is_enabled = filename.endswith(".jar")
        self.lbl_name = QLabel(filename)
        self.lbl_name.setStyleSheet(f"color: {'#FFF' if is_enabled else '#777'}; font-size: 13px; border:none;")

        self.btn_toggle = QPushButton("ON" if is_enabled else "OFF")
        self.btn_toggle.setFixedSize(50, 26)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#00C6FF' if is_enabled else '#444'};
                color: {'#000' if is_enabled else '#FFF'};
                border-radius: 4px; font-weight: bold; border: none;
            }}
        """)
        self.btn_toggle.clicked.connect(self.toggle_mod)

        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedSize(30, 26)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet("QPushButton { background-color: rgba(255,0,0,0.2); border-radius: 4px; border: none; } QPushButton:hover { background-color: rgba(255,0,0,0.5); }")
        self.btn_delete.clicked.connect(self.delete_mod)

        layout.addWidget(self.lbl_name, 1)
        layout.addWidget(self.btn_toggle)
        layout.addWidget(self.btn_delete)

    def toggle_mod(self):
        old_path = os.path.join(self.mods_dir, self.filename)
        if self.filename.endswith(".jar"):
            new_path = old_path + ".disabled"
        else:
            new_path = old_path.replace(".disabled", "")
        try:
            os.rename(old_path, new_path)
            self.refresh_cb()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to toggle mod: {e}")

    def delete_mod(self):
        path = os.path.join(self.mods_dir, self.filename)
        try:
            os.remove(path)
            self.refresh_cb()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete mod: {e}")

class BitLauncherPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BitLauncher Pro")
        self.resize(1100, 720)
        
        self.current_lang = "RU"
        self.current_game_dir = DEFAULT_GAME_DIR
        os.makedirs(self.current_game_dir, exist_ok=True)
        os.makedirs(os.path.join(self.current_game_dir, "mods"), exist_ok=True)

        self.active_account = {"type": "offline", "username": "BitPlayer"}
        self.banner_list = ["BitLauncher_banner1.png", "BitLauncher_banner2.png", "BitLauncher_banner3.png"]
        self.current_banner_idx = 0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.bg_label = QLabel(central_widget)
        self.bg_label.setGeometry(0, 0, 1100, 720)
        self.bg_label.setScaledContents(True)
        self.bg_label.setStyleSheet("background-color: #0B0D17;")

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet(f"background-color: {C_PANEL_SOLID}; border-right: 1px solid {C_BORDER};")
        
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(15, 25, 0, 25)

        self.lbl_logo = QLabel()
        logo_pixmap = load_local_pixmap("BitLauncher.png", width=190)
        if logo_pixmap:
            self.lbl_logo.setPixmap(logo_pixmap)
            self.lbl_logo.setStyleSheet("border: none; margin-bottom: 20px;")
            side_layout.addWidget(self.lbl_logo, 0, Qt.AlignLeft)
        else:
            brand = QLabel("BITLAUNCHER")
            brand.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {C_ACCENT}; letter-spacing: 1px; padding-left: 10px; border:none;")
            side_layout.addWidget(brand)

        self.nav_container = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(0,0,0,0)
        self.nav_layout.setSpacing(8)

        self.btn_play = NavButton("", "🎮")
        self.btn_mods = NavButton("", "📦")
        self.btn_settings = NavButton("", "⚙️")
        
        self.nav_layout.addWidget(self.btn_play)
        self.nav_layout.addWidget(self.btn_mods)
        self.nav_layout.addWidget(self.btn_settings)
        self.nav_layout.addStretch()
        side_layout.addWidget(self.nav_container)

        root_layout.addWidget(self.sidebar)

        main_content_area = QWidget()
        main_vbox = QVBoxLayout(main_content_area)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        # Top Bar
        top_bar = QWidget()
        top_bar.setFixedHeight(65)
        top_bar.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 15, 30, 0)
        
        self.cb_open_folders = QComboBox()
        self.cb_open_folders.setFixedHeight(36)
        self.cb_open_folders.setStyleSheet(self.get_combo_style())
        self.cb_open_folders.activated.connect(self.handle_folder_open)
        top_layout.addWidget(self.cb_open_folders)

        top_layout.addStretch()

        self.profile_widget = GlassFrame()
        self.profile_widget.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(22, 25, 41, 0.85);
                border: 1px solid {C_BORDER};
                border-radius: 20px;
            }}
        """)
        prof_lay = QHBoxLayout(self.profile_widget)
        prof_lay.setContentsMargins(8, 4, 14, 4)
        prof_lay.setSpacing(10)

        self.lbl_head_icon = QLabel()
        self.lbl_head_icon.setFixedSize(32, 32)
        head_pixmap = load_local_pixmap("vbd.png", width=32, height=32)
        if head_pixmap:
            self.lbl_head_icon.setPixmap(head_pixmap)
            self.lbl_head_icon.setStyleSheet("border-radius: 6px; border: none;")
        else:
            self.lbl_head_icon.setStyleSheet("background-color: #00d2ff; border-radius: 16px; border: none;")

        self.lbl_user_name = QLabel(self.active_account["username"])
        self.lbl_user_name.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 700; border: none;")

        prof_lay.addWidget(self.lbl_head_icon)
        prof_lay.addWidget(self.lbl_user_name)
        top_layout.addWidget(self.profile_widget)

        main_vbox.addWidget(top_bar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")
        main_vbox.addWidget(self.stack)

        root_layout.addWidget(main_content_area)

        self.init_play_view()
        self.init_mods_view()
        self.init_settings_view()

        self.btn_play.clicked.connect(lambda: self.switch_view(0, self.btn_play))
        self.btn_mods.clicked.connect(lambda: self.switch_view(1, self.btn_mods))
        self.btn_settings.clicked.connect(lambda: self.switch_view(2, self.btn_settings))

        self.btn_play.setChecked(True)

        self.banner_timer = QTimer(self)
        self.banner_timer.timeout.connect(self.rotate_next_banner)
        self.banner_timer.start(7000)

        self.ver_thread = VersionLoaderThread()
        self.ver_thread.versions_loaded.connect(self.on_versions_loaded)
        self.ver_thread.start()

        self.load_config()
        self.update_translations()

    def resizeEvent(self, event):
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

    def save_config(self):
        config_data = {
            "lang": self.current_lang,
            "username": self.inp_user.text().strip(),
            "game_dir": self.current_game_dir,
            "java_path": self.inp_java_path.text(),
            "ram": self.slider_ram.value(),
            "resolution": self.cb_resolution.currentText(),
            "close_on_start": self.chk_close_on_start.isChecked(),
            "clean_logs_on_exit": self.chk_clean_logs_on_exit.isChecked(),
            "jvm_args": self.inp_jvm.text()
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print("Failed to save config:", e)

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            lang_map = {"RU": 0, "EN": 1, "UA": 2}
            if data.get("lang") in lang_map:
                self.cb_language.setCurrentIndex(lang_map[data["lang"]])
            
            if data.get("username"):
                self.inp_user.setText(data["username"])
                self.save_account()
                
            if data.get("game_dir"):
                self.current_game_dir = data["game_dir"]
                self.inp_gdir_path.setText(self.current_game_dir)
                
            if data.get("java_path"):
                self.inp_java_path.setText(data["java_path"])
                
            if data.get("ram"):
                self.slider_ram.setValue(data["ram"])
                
            if data.get("resolution"):
                idx = self.cb_resolution.findText(data["resolution"])
                if idx >= 0: self.cb_resolution.setCurrentIndex(idx)
                
            if "close_on_start" in data:
                self.chk_close_on_start.setChecked(data["close_on_start"])
                
            if "clean_logs_on_exit" in data:
                self.chk_clean_logs_on_exit.setChecked(data["clean_logs_on_exit"])
                
            if data.get("jvm_args"):
                self.inp_jvm.setText(data["jvm_args"])

        except Exception as e:
            print("Failed to load config:", e)

    def switch_view(self, index, btn):
        for b in [self.btn_play, self.btn_mods, self.btn_settings]: b.setChecked(False)
        btn.setChecked(True)
        self.stack.setCurrentIndex(index)

    def update_translations(self):
        t = LANGUAGES[self.current_lang]
        self.btn_play.setText(t["nav_play"])
        self.btn_mods.setText(t["nav_mods"])
        self.btn_settings.setText(t["nav_settings"])

        self.lbl_welcome_title.setText(t["welcome"])
        self.lbl_welcome_sub.setText(t["welcome_sub"])
        self.lbl_v_hdr.setText(t["version"])
        self.lbl_m_hdr.setText(t["mods"])
        self.chk_fabric.setText(t["use_fabric"])
        self.btn_launch.setText(t["btn_launch"])
        self.lbl_status.setText(t["ready"])

        self.btn_tab_online.setText(t["search_mods"])
        self.btn_tab_local.setText(t["installed_mods"])
        self.inp_search.setPlaceholderText(t["search_placeholder"])
        self.btn_search.setText(t["btn_find"])
        self.btn_refresh_mods.setText(t["refresh"])

        self.lbl_settings_hdr.setText(t["settings_title"])
        self.lbl_acc_hdr.setText(t["acc_mgmt"])
        self.rb_offline.setText(t["acc_offline"])
        self.rb_ms.setText(t["acc_ms"])
        self.inp_user.setPlaceholderText(t["nick_placeholder"])
        self.btn_save_acc.setText(t["btn_apply_acc"])

        self.lbl_gdir_title.setText(t["game_dir"])
        self.lbl_jexec_title.setText(t["java_path"])
        self.btn_gdir_browse.setText(t["browse"])
        self.btn_java_browse.setText(t["browse"])

        self.lbl_ram_title.setText(t["ram_alloc"])
        self.lbl_res_title.setText(t["resolution"])
        self.chk_close_on_start.setText(t["close_on_launch"])
        self.chk_clean_logs_on_exit.setText(t["clean_logs_exit"])
        self.lbl_jvm_title.setText(t["jvm_args"])
        self.lbl_lang_title.setText(t["lang_select"])
        self.lbl_clean_title.setText(t["quick_clean"])
        self.btn_clean_logs.setText(t["btn_clean_logs"])
        self.btn_clean_cache.setText(t["btn_clean_cache"])

        self.cb_open_folders.clear()
        self.cb_open_folders.addItems([
            t["open_folders"],
            t["folder_main"],
            t["folder_mods"],
            t["folder_saves"],
            t["folder_screens"],
            t["folder_logs"],
            t["view_logs"]
        ])

    def handle_folder_open(self, index):
        if index == 0: return
        if index == 6:
            log_file = os.path.join(self.current_game_dir, "logs", "latest.log")
            dlg = LogViewerDialog(log_file, self)
            dlg.exec()
            self.cb_open_folders.setCurrentIndex(0)
            return

        paths = {
            1: self.current_game_dir,
            2: os.path.join(self.current_game_dir, "mods"),
            3: os.path.join(self.current_game_dir, "saves"),
            4: os.path.join(self.current_game_dir, "screenshots"),
            5: os.path.join(self.current_game_dir, "logs"),
        }
        target = paths.get(index)
        if target:
            os.makedirs(target, exist_ok=True)
            try:
                open_folder(target)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open folder: {e}")
        self.cb_open_folders.setCurrentIndex(0)

    # --- VIEW 1: PLAY ---
    def init_play_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 10, 35, 25)

        banner_frame = GlassFrame()
        banner_frame.setFixedHeight(210)
        banner_layout = QHBoxLayout(banner_frame)
        banner_layout.setContentsMargins(25, 20, 25, 20)

        text_vbox = QVBoxLayout()
        self.lbl_welcome_title = QLabel()
        self.lbl_welcome_title.setStyleSheet("font-size: 26px; font-weight: 800; color: #fff; border:none;")
        self.lbl_welcome_sub = QLabel()
        self.lbl_welcome_sub.setStyleSheet(f"font-size: 13px; color: {C_TEXT_SEC}; border:none;")
        self.lbl_welcome_sub.setWordWrap(True)
        
        text_vbox.addWidget(self.lbl_welcome_title)
        text_vbox.addWidget(self.lbl_welcome_sub)
        text_vbox.addStretch()

        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(6)
        self.dot_labels = []
        for i in range(len(self.banner_list)):
            dot = QLabel("•")
            dot.setStyleSheet(f"color: {C_ACCENT if i == 0 else C_TEXT_SEC}; font-size: 20px; border: none;")
            dots_layout.addWidget(dot)
            self.dot_labels.append(dot)
        dots_layout.addStretch()
        text_vbox.addLayout(dots_layout)

        banner_layout.addLayout(text_vbox, 3)

        self.lbl_banner_img = QLabel()
        self.lbl_banner_img.setFixedSize(280, 160)
        self.lbl_banner_img.setStyleSheet("border: none; border-radius: 10px;")
        
        initial_pixmap = load_local_pixmap(self.banner_list[0], height=160)
        if initial_pixmap: self.lbl_banner_img.setPixmap(initial_pixmap)

        banner_layout.addWidget(self.lbl_banner_img, 2, Qt.AlignRight)
        layout.addWidget(banner_frame)
        layout.addStretch()

        controls = GlassFrame()
        controls.setFixedHeight(140)
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(20, 15, 20, 15)

        # Выравнивание и геометрия по единой сетке QHBoxLayout / QVBoxLayout
        main_row = QHBoxLayout()
        main_row.setSpacing(20)

        v_box = QVBoxLayout()
        v_box.setSpacing(6)
        self.lbl_v_hdr = QLabel()
        self.lbl_v_hdr.setStyleSheet(f"color: {C_ACCENT}; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        self.cb_versions = QComboBox()
        self.cb_versions.setMinimumHeight(38)
        self.cb_versions.setStyleSheet(self.get_combo_style())
        self.cb_versions.addItem("Loading...")

        self.lbl_status = QLabel()
        self.lbl_status.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 11px; font-weight: 600; border: none;")

        v_box.addWidget(self.lbl_v_hdr)
        v_box.addWidget(self.cb_versions)
        v_box.addWidget(self.lbl_status)

        f_box = QVBoxLayout()
        f_box.setSpacing(6)
        self.lbl_m_hdr = QLabel()
        self.lbl_m_hdr.setStyleSheet(f"color: {C_ACCENT}; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        
        self.chk_fabric = QCheckBox()
        self.chk_fabric.setMinimumHeight(38)
        self.chk_fabric.setCursor(Qt.PointingHandCursor)
        self.chk_fabric.setStyleSheet(f"""
            QCheckBox {{
                background-color: #121520;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                color: {C_TEXT_MAIN};
                padding: 4px 12px;
                font-size: 13px;
            }}
            QCheckBox:hover {{
                border-color: {C_ACCENT};
            }}
        """)

        f_box.addWidget(self.lbl_m_hdr)
        f_box.addWidget(self.chk_fabric)
        f_box.addStretch()

        # Акцентная контрастная кнопка ИГРАТЬ
        self.btn_launch = QPushButton()
        self.btn_launch.setMinimumSize(180, 48)
        self.btn_launch.setCursor(Qt.PointingHandCursor)
        self.btn_launch.setStyleSheet(self.get_launch_btn_style())
        self.btn_launch.clicked.connect(self.start_launch)

        main_row.addLayout(v_box, stretch=1)
        main_row.addLayout(f_box, stretch=1)
        main_row.addWidget(self.btn_launch, alignment=Qt.AlignVCenter)
        controls_layout.addLayout(main_row)

        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(4)
        self.pbar.setTextVisible(False)
        self.pbar.setVisible(False)
        self.pbar.setStyleSheet(f"""
            QProgressBar {{ background-color: rgba(0,0,0,0.4); border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background: linear-gradient(90deg, {C_ACCENT}, {C_ACCENT_HOVER}); border-radius: 2px; }}
        """)

        controls_layout.addWidget(self.pbar)
        layout.addWidget(controls)

        self.stack.addWidget(page)

    def on_versions_loaded(self, version_list):
        self.cb_versions.clear()
        self.cb_versions.addItems(version_list)

    def rotate_next_banner(self):
        self.current_banner_idx = (self.current_banner_idx + 1) % len(self.banner_list)
        pix = load_local_pixmap(self.banner_list[self.current_banner_idx], height=160)
        if pix: self.lbl_banner_img.setPixmap(pix)
        for idx, dot in enumerate(self.dot_labels):
            dot.setStyleSheet(f"color: {C_ACCENT if idx == self.current_banner_idx else C_TEXT_SEC}; font-size: 20px; border: none;")

    def start_launch(self):
        user = self.active_account["username"]
        ver = self.cb_versions.currentText()
        ram = self.slider_ram.value()
        fabric = self.chk_fabric.isChecked()
        res = self.cb_resolution.currentText()
        jvm = self.inp_jvm.text()
        custom_java_text = self.inp_java_path.text().strip()
        custom_java = custom_java_text if custom_java_text and custom_java_text != self.default_java_text else None

        self.btn_launch.setEnabled(False)
        self.pbar.setVisible(True)
        self.pbar.setValue(0)

        self.launch_thread = GameLaunchThread(user, ver, ram, fabric, self.current_game_dir, res, jvm, custom_java)
        self.launch_thread.progress_signal.connect(self.on_launch_progress)
        self.launch_thread.finished_signal.connect(self.on_launch_finished)
        self.launch_thread.error_signal.connect(self.on_launch_error)
        self.launch_thread.start()

    def on_launch_progress(self, msg, val):
        self.lbl_status.setText(msg)
        self.pbar.setValue(val)

    def on_launch_finished(self):
        self.btn_launch.setEnabled(True)
        self.pbar.setVisible(False)
        self.lbl_status.setText(LANGUAGES[self.current_lang]["ready"])

        if self.chk_clean_logs_on_exit.isChecked():
            self.clear_logs()

        if self.chk_close_on_start.isChecked():
            sys.exit(0)

    def on_launch_error(self, err):
        self.btn_launch.setEnabled(True)
        self.pbar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Launch failed:\n{err}")

    # --- VIEW 2: MODS ---
    def init_mods_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 10, 35, 25)

        tab_row = QHBoxLayout()
        self.btn_tab_online = QPushButton()
        self.btn_tab_local = QPushButton()

        for b in (self.btn_tab_online, self.btn_tab_local):
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(36)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: 1px solid {C_BORDER};
                    border-radius: 8px; color: {C_TEXT_SEC}; font-weight: 600; padding: 0 16px;
                }}
                QPushButton:checked {{ background: {C_ACCENT}; color: #000; border: none; font-weight: 700; }}
            """)
            tab_row.addWidget(b)

        tab_row.addStretch()
        layout.addLayout(tab_row)

        self.mod_sub_stack = QStackedWidget()

        # Search Tab
        p_search = QWidget()
        p_s_lay = QVBoxLayout(p_search)
        p_s_lay.setContentsMargins(0, 10, 0, 0)

        search_layout = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setStyleSheet(self.get_input_style())
        
        self.btn_search = QPushButton()
        self.btn_search.setFixedSize(110, 42)
        self.btn_search.setCursor(Qt.PointingHandCursor)
        self.btn_search.setStyleSheet(self.get_action_btn_style())
        self.btn_search.clicked.connect(self.perform_mod_search)
        self.inp_search.returnPressed.connect(self.perform_mod_search)

        search_layout.addWidget(self.inp_search)
        search_layout.addWidget(self.btn_search)
        p_s_lay.addLayout(search_layout)

        self.lbl_mod_results = QLabel("...")
        self.lbl_mod_results.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 12px; margin: 6px 0;")
        p_s_lay.addWidget(self.lbl_mod_results)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.mod_list_content = QWidget()
        self.mod_list_layout = QVBoxLayout(self.mod_list_content)
        self.mod_list_layout.setContentsMargins(0, 0, 5, 0)
        self.mod_list_layout.setSpacing(10)
        self.mod_list_layout.addStretch()

        scroll.setWidget(self.mod_list_content)
        p_s_lay.addWidget(scroll)

        # Local Mods Tab
        p_local = QWidget()
        p_l_lay = QVBoxLayout(p_local)
        p_l_lay.setContentsMargins(0, 10, 0, 0)

        self.local_mods_list = QListWidget()
        self.local_mods_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {C_PANEL_SOLID};
                border: 1px solid {C_BORDER};
                border-radius: 10px; color: #fff; padding: 10px;
            }}
            QListWidget::item {{ border-bottom: 1px solid rgba(255,255,255,0.05); }}
        """)

        self.btn_refresh_mods = QPushButton()
        self.btn_refresh_mods.setStyleSheet(self.get_action_btn_style())
        self.btn_refresh_mods.setFixedHeight(36)
        self.btn_refresh_mods.clicked.connect(self.load_installed_mods)

        p_l_lay.addWidget(self.btn_refresh_mods)
        p_l_lay.addWidget(self.local_mods_list)

        self.mod_sub_stack.addWidget(p_search)
        self.mod_sub_stack.addWidget(p_local)
        layout.addWidget(self.mod_sub_stack)

        self.btn_tab_online.clicked.connect(lambda: self.switch_mod_tab(0))
        self.btn_tab_local.clicked.connect(lambda: self.switch_mod_tab(1))
        self.btn_tab_online.setChecked(True)

        self.stack.addWidget(page)

    def switch_mod_tab(self, index):
        self.btn_tab_online.setChecked(index == 0)
        self.btn_tab_local.setChecked(index == 1)
        self.mod_sub_stack.setCurrentIndex(index)
        if index == 1: self.load_installed_mods()

    def load_installed_mods(self):
        self.local_mods_list.clear()
        mods_dir = os.path.join(self.current_game_dir, "mods")
        if not os.path.exists(mods_dir): return
        for file in os.listdir(mods_dir):
            if file.endswith(".jar") or file.endswith(".disabled"):
                item = QListWidgetItem(self.local_mods_list)
                widget = LocalModItemWidget(file, mods_dir, self.load_installed_mods)
                item.setSizeHint(widget.sizeHint())
                self.local_mods_list.addItem(item)
                self.local_mods_list.setItemWidget(item, widget)

    def perform_mod_search(self):
        query = self.inp_search.text().strip()
        if not query: return
        self.clear_mod_list()
        self.lbl_mod_results.setText("Searching...")
        self.search_thread = ModSearchThread(query)
        self.search_thread.results_signal.connect(self.display_mod_results)
        self.search_thread.start()

    def clear_mod_list(self):
        while self.mod_list_layout.count() > 1:
            w = self.mod_list_layout.takeAt(0).widget()
            if w: w.deleteLater()

    def display_mod_results(self, hits):
        if not hits:
            self.lbl_mod_results.setText("Nothing found.")
            return
        self.lbl_mod_results.setText(f"Found: {len(hits)}")
        for hit in hits:
            card = ModCard(
                hit.get('title'), hit.get('description'), hit.get('icon_url'),
                hit.get('project_id'), self.install_mod
            )
            self.mod_list_layout.insertWidget(self.mod_list_layout.count()-1, card)

    def install_mod(self, pid, name):
        self.lbl_mod_results.setText(f"Downloading {name}...")
        self.dl_thread = ModDownloadThread(pid, name, self.current_game_dir)
        self.dl_thread.status_signal.connect(lambda m: self.lbl_mod_results.setText(m))
        self.dl_thread.start()

    # --- VIEW 3: SETTINGS ---
    def init_settings_view(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(35, 10, 35, 25)

        self.lbl_settings_hdr = QLabel()
        self.lbl_settings_hdr.setStyleSheet("font-size: 22px; font-weight: 800; color: #fff; margin-bottom: 5px;")
        main_layout.addWidget(self.lbl_settings_hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 10, 0)

        # Language Selection
        box_lang = GlassFrame()
        lay_lang = QVBoxLayout(box_lang)
        lay_lang.setContentsMargins(18, 16, 18, 16)
        self.lbl_lang_title = QLabel()
        self.lbl_lang_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #fff; border:none;")
        
        self.cb_language = QComboBox()
        self.cb_language.addItems(["Русский (RU)", "English (EN)", "Українська (UA)"])
        self.cb_language.setStyleSheet(self.get_combo_style())
        self.cb_language.currentIndexChanged.connect(self.change_language)

        lay_lang.addWidget(self.lbl_lang_title)
        lay_lang.addWidget(self.cb_language)
        layout.addWidget(box_lang)

        # Account Management
        box_acc = GlassFrame()
        lay_a = QVBoxLayout(box_acc)
        lay_a.setContentsMargins(18, 16, 18, 16)

        self.lbl_acc_hdr = QLabel()
        self.lbl_acc_hdr.setStyleSheet("font-size: 15px; font-weight: 700; color: #fff; border:none;")

        type_layout = QHBoxLayout()
        self.rb_offline = QRadioButton()
        self.rb_ms = QRadioButton()
        self.rb_offline.setChecked(True)

        for rb in (self.rb_offline, self.rb_ms):
            rb.setCursor(Qt.PointingHandCursor)
            rb.setStyleSheet("color: #fff; font-size: 13px; font-weight: 600; border: none;")
            type_layout.addWidget(rb)

        type_layout.addStretch()

        self.inp_user = QLineEdit("BitPlayer")
        self.inp_user.setStyleSheet(self.get_input_style())

        self.btn_save_acc = QPushButton()
        self.btn_save_acc.setFixedSize(160, 36)
        self.btn_save_acc.setCursor(Qt.PointingHandCursor)
        self.btn_save_acc.setStyleSheet(self.get_action_btn_style())
        self.btn_save_acc.clicked.connect(self.save_account)

        lay_a.addWidget(self.lbl_acc_hdr)
        lay_a.addLayout(type_layout)
        lay_a.addWidget(self.inp_user)
        lay_a.addWidget(self.btn_save_acc, 0, Qt.AlignRight)
        layout.addWidget(box_acc)

        # Custom Game Folder
        box_gdir = GlassFrame()
        lay_gdir = QVBoxLayout(box_gdir)
        lay_gdir.setContentsMargins(18, 16, 18, 16)

        self.lbl_gdir_title = QLabel()
        self.lbl_gdir_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #fff; border:none;")

        gdir_lay = QHBoxLayout()
        self.inp_gdir_path = QLineEdit(self.current_game_dir)
        self.inp_gdir_path.setStyleSheet(self.get_input_style())
        
        self.btn_gdir_browse = QPushButton()
        self.btn_gdir_browse.setFixedSize(90, 40)
        self.btn_gdir_browse.setStyleSheet(self.get_action_btn_style())
        self.btn_gdir_browse.clicked.connect(self.browse_game_dir)

        gdir_lay.addWidget(self.inp_gdir_path)
        gdir_lay.addWidget(self.btn_gdir_browse)

        lay_gdir.addWidget(self.lbl_gdir_title)
        lay_gdir.addLayout(gdir_lay)
        layout.addWidget(box_gdir)

        # Custom Java Path
        box_java = GlassFrame()
        lay_j_exec = QVBoxLayout(box_java)
        lay_j_exec.setContentsMargins(18, 16, 18, 16)

        self.lbl_jexec_title = QLabel()
        self.lbl_jexec_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #fff; border:none;")

        java_lay = QHBoxLayout()
        self.default_java_text = "Default (system Java)"
        self.inp_java_path = QLineEdit(self.default_java_text)
        self.inp_java_path.setStyleSheet(self.get_input_style())
        
        self.btn_java_browse = QPushButton()
        self.btn_java_browse.setFixedSize(90, 40)
        self.btn_java_browse.setStyleSheet(self.get_action_btn_style())
        self.btn_java_browse.clicked.connect(self.browse_java_path)

        java_lay.addWidget(self.inp_java_path)
        java_lay.addWidget(self.btn_java_browse)

        lay_j_exec.addWidget(self.lbl_jexec_title)
        lay_j_exec.addLayout(java_lay)
        layout.addWidget(box_java)

        # RAM Allocation
        total_ram = max(2, round(psutil.virtual_memory().total / (1024**3)))
        box_ram = GlassFrame()
        lay_r = QVBoxLayout(box_ram)
        lay_r.setContentsMargins(18, 16, 18, 16)

        hdr_r = QHBoxLayout()
        self.lbl_ram_title = QLabel()
        self.lbl_ram_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #fff; border:none;")
        self.lbl_ram_val = QLabel("4 GB")
        self.lbl_ram_val.setStyleSheet(f"color: {C_ACCENT}; font-size: 14px; font-weight: 800; border:none;")
        hdr_r.addWidget(self.lbl_ram_title)
        hdr_r.addWidget(self.lbl_ram_val, 0, Qt.AlignRight)

        self.slider_ram = QSlider(Qt.Horizontal)
        self.slider_ram.setMinimum(2)
        self.slider_ram.setMaximum(total_ram)
        self.slider_ram.setValue(min(4, total_ram))
        self.slider_ram.setStyleSheet(self.get_slider_style())
        self.slider_ram.valueChanged.connect(lambda v: self.lbl_ram_val.setText(f"{v} GB"))

        lay_r.addLayout(hdr_r)
        lay_r.addWidget(self.slider_ram)
        layout.addWidget(box_ram)

        # Behavior & Options
        box_opt = GlassFrame()
        lay_o = QVBoxLayout(box_opt)
        lay_o.setContentsMargins(18, 16, 18, 16)
        lay_o.setSpacing(10)

        self.lbl_res_title = QLabel()
        self.lbl_res_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #fff; border:none;")
        
        self.cb_resolution = QComboBox()
        self.cb_resolution.addItems(["Автоматически", "1920x1080", "1600x900", "1280x720", "854x480"])
        self.cb_resolution.setStyleSheet(self.get_combo_style())

        self.chk_close_on_start = QCheckBox()
        self.chk_close_on_start.setStyleSheet(f"color: {C_TEXT_MAIN}; font-size: 13px; font-weight: 600; border:none;")

        self.chk_clean_logs_on_exit = QCheckBox()
        self.chk_clean_logs_on_exit.setStyleSheet(f"color: {C_TEXT_MAIN}; font-size: 13px; font-weight: 600; border:none;")

        lay_o.addWidget(self.lbl_res_title)
        lay_o.addWidget(self.cb_resolution)
        lay_o.addWidget(self.chk_close_on_start)
        lay_o.addWidget(self.chk_clean_logs_on_exit)
        layout.addWidget(box_opt)

        # JVM Arguments
        box_jvm = GlassFrame()
        lay_j = QVBoxLayout(box_jvm)
        lay_j.setContentsMargins(18, 16, 18, 16)

        self.lbl_jvm_title = QLabel()
        self.lbl_jvm_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #fff; border:none;")

        self.inp_jvm = QLineEdit("-XX:+UseG1GC")
        self.inp_jvm.setStyleSheet(self.get_input_style())

        lay_j.addWidget(self.lbl_jvm_title)
        lay_j.addWidget(self.inp_jvm)
        layout.addWidget(box_jvm)

        # Maintenance Tools (Cache / Logs Cleaning)
        box_clean = GlassFrame()
        lay_c = QVBoxLayout(box_clean)
        lay_c.setContentsMargins(18, 16, 18, 16)

        self.lbl_clean_title = QLabel()
        self.lbl_clean_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #fff; border:none;")

        clean_row = QHBoxLayout()
        self.btn_clean_logs = QPushButton()
        self.btn_clean_logs.setStyleSheet(self.get_action_btn_style())
        self.btn_clean_logs.setFixedHeight(36)
        self.btn_clean_logs.clicked.connect(self.clear_logs)

        self.btn_clean_cache = QPushButton()
        self.btn_clean_cache.setStyleSheet(self.get_action_btn_style())
        self.btn_clean_cache.setFixedHeight(36)
        self.btn_clean_cache.clicked.connect(self.clear_cache)

        clean_row.addWidget(self.btn_clean_logs)
        clean_row.addWidget(self.btn_clean_cache)

        lay_c.addWidget(self.lbl_clean_title)
        lay_c.addLayout(clean_row)
        layout.addWidget(box_clean)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.stack.addWidget(page)

    def change_language(self, index):
        langs = ["RU", "EN", "UA"]
        self.current_lang = langs[index]
        self.update_translations()

    def browse_game_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Game Directory", self.current_game_dir)
        if directory:
            self.current_game_dir = directory
            self.inp_gdir_path.setText(directory)
            os.makedirs(os.path.join(self.current_game_dir, "mods"), exist_ok=True)

    def save_account(self):
        nick = self.inp_user.text().strip()
        if nick:
            self.active_account = {"type": "offline", "username": nick}
            self.lbl_user_name.setText(nick)
            QMessageBox.information(self, "Success", f"Profile set to: {nick}")

    def browse_java_path(self):
        if sys.platform.startswith("win"):
            title = "Select Java executable"
            file_filter = "Java executable (java.exe javaw.exe)"
        else:
            title = "Select Java executable"
            file_filter = "All files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if file_path:
            self.inp_java_path.setText(file_path)

    def clear_logs(self):
        logs_dir = os.path.join(self.current_game_dir, "logs")
        if os.path.exists(logs_dir):
            try:
                shutil.rmtree(logs_dir)
                os.makedirs(logs_dir, exist_ok=True)
                QMessageBox.information(self, "Info", "Logs cleared successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear logs: {e}")

    def clear_cache(self):
        assets_dir = os.path.join(self.current_game_dir, "assets")
        if os.path.exists(assets_dir):
            try:
                shutil.rmtree(assets_dir)
                QMessageBox.information(self, "Info", "Game cache cleared successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear cache: {e}")

    def get_input_style(self):
        return f"background-color: rgba(26, 29, 41, 0.85); border: 1px solid {C_BORDER}; border-radius: 8px; padding: 10px; color: #fff; font-size: 13px;"
    
    def get_combo_style(self):
        return f"""
            QComboBox {{
                background-color: #121520;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px; padding: 4px 10px; color: #FFFFFF; font-size: 13px; font-weight: 600;
                min-width: 140px;
            }}
            QComboBox:hover {{ border-color: {C_ACCENT}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background-color: {C_PANEL_SOLID}; border: 1px solid rgba(255, 255, 255, 0.15);
                outline: none; padding: 4px; color: #FFFFFF; selection-background-color: {C_ACCENT}; selection-color: #000000;
            }}
        """

    def get_launch_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {C_ACCENT};
                color: #05060a;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {C_ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #00b8e6;
            }}
            QPushButton:disabled {{
                background-color: #2A2E3F;
                color: #555D73;
            }}
        """
    
    def get_action_btn_style(self):
        return f"QPushButton {{ background-color: {C_ACCENT}; border: none; border-radius: 8px; color: #08090E; font-weight: 700; font-size: 13px; }} QPushButton:hover {{ background-color: {C_ACCENT_HOVER}; }}"

    def get_slider_style(self):
        return f"""
            QSlider::groove:horizontal {{ background: rgba(255, 255, 255, 0.1); height: 6px; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: #fff; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }}
            QSlider::sub-page:horizontal {{ background-color: {C_ACCENT}; border-radius: 3px; }}
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    launcher = BitLauncherPro()
    launcher.show()
    sys.exit(app.exec())