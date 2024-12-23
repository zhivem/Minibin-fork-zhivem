import ctypes
import sys
import os
import autostart
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer, QSettings

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

CSIDL_BITBUCKET = 0x000a

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).parent 
    full_path = base_path / relative_path
    if not full_path.exists():
        raise FileNotFoundError(f"Ресурс не найден: {full_path}")
    return str(full_path)

def load_icon(icon_path):
    full_icon_path = resource_path(icon_path)
    print(f"Попытка загрузить иконку по пути: {full_icon_path}")  # Отладочный вывод
    try:
        return QIcon(full_icon_path)
    except Exception as e:
        print(f"Ошибка при загрузке иконки: {e}")
        return QIcon()  # Возвращает пустой значок или можно установить значок по умолчанию

# Используем QSettings для сохранения состояния уведомлений
settings = QSettings("MinibinFork", "RecycleBinManager")

def show_notification(title, message, icon_path=None):
    if settings.value("show_notifications", True, type=bool):
        if icon_path:
            icon = QIcon(resource_path(icon_path))
        else:
            icon = QIcon()
        tray_icon.showMessage(title, message, icon, 5000)

def empty_recycle_bin():
    try:
        SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
        flags = 0x01
        bin_path = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_BITBUCKET, 0, 0, bin_path)
        result = SHEmptyRecycleBin(None, bin_path.value, flags)

        if result == 0 or result == -2147418113:
            show_notification("Корзина", "Корзина успешно очищена.", "icons/minibin-kt-empty.ico")
        else:
            show_notification("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", "icons/minibin-kt-full.ico")
        
        update_icon()
    except Exception as e:
        print(f"Ошибка при очистке корзины: {e}")
        show_notification("Ошибка", f"Не удалось очистить корзину: {e}", "icons/minibin-kt-full.ico")

def open_recycle_bin():
    try:
        os.startfile("shell:RecycleBinFolder")
    except Exception as e:
        print(f"Ошибка при открытии корзины: {e}")
        show_notification("Ошибка", f"Не удалось открыть корзину: {e}", "icons/minibin-kt-full.ico")

def exit_program():
    QApplication.quit()

def update_icon():
    if is_recycle_bin_empty():
        tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))
    else:
        tray_icon.setIcon(load_icon("icons/minibin-kt-full.ico"))

def is_recycle_bin_empty():
    rbinfo = SHQUERYRBINFO()
    rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))

    if result != 0:
        show_notification("Ошибка", "Не удалось получить состояние корзины.", "icons/minibin-kt-full.ico")
        return False

    return rbinfo.i64NumItems == 0

def periodic_update():
    update_icon()

def verify_icons():
    icons = ["icons/minibin-kt-empty.ico", "icons/minibin-kt-full.ico",
             "icons/autostart-enabled.ico", "icons/autostart-disabled.ico",]  
    for icon in icons:
        icon_full_path = resource_path(icon)
        if not Path(icon_full_path).exists():
            print(f"Иконка не найдена: {icon_full_path}")
            raise FileNotFoundError(f"Иконка не найдена: {icon_full_path}")
        else:
            print(f"Иконка найдена: {icon_full_path}")

def toggle_autostart(checked):
    if checked:
        success = autostart.enable_autostart()
        if success:
            show_notification("Автозапуск", "Автозапуск включен.", "icons/autostart-enabled.ico")
        else:
            show_notification("Автозапуск", "Не удалось включить автозапуск.", "icons/autostart-disabled.ico")
            autostart_action.setChecked(False)
    else:
        success = autostart.disable_autostart()
        if success:
            show_notification("Автозапуск", "Автозапуск отключен.", "icons/autostart-disabled.ico")
        else:
            show_notification("Автозапуск", "Не удалось отключить автозапуск.", "icons/autostart-enabled.ico")
            autostart_action.setChecked(True)

def toggle_show_notifications(checked):
    settings.setValue("show_notifications", checked)
    # Можно добавить уведомление о смене состояния, если необходимо
    if checked:
        show_notification("Уведомления", "Уведомления включены.", "icons/notifications-enabled.ico")
    else:
        # Не показываем уведомление при отключении
        pass

def initialize_autostart_menu():
    global autostart_action
    autostart_action = QAction("Автозапуск", checkable=True)
    autostart_action.setChecked(autostart.is_autostart_enabled())
    autostart_action.triggered.connect(toggle_autostart)
    tray_menu.insertAction(empty_action, autostart_action)  # Вставляем перед разделителем

def initialize_notifications_menu():
    global show_notifications_action
    show_notifications_action = QAction("Показывать уведомления", checkable=True)
    show_notifications_action.setChecked(settings.value("show_notifications", True, type=bool))
    show_notifications_action.triggered.connect(toggle_show_notifications)
    tray_menu.insertAction(autostart_action, show_notifications_action)  # Вставляем после автозапуска

if __name__ == "__main__":
    print(f"Текущая рабочая директория: {Path.cwd()}")

    if os.name != 'nt':
        print("Это приложение работает только на Windows.")
        sys.exit(1)

    try:
        verify_icons()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    app = QApplication(sys.argv)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))

    tray_menu = QMenu()
    open_action = QAction("Открыть корзину", triggered=open_recycle_bin)
    empty_action = QAction("Очистить корзину", triggered=empty_recycle_bin)
    exit_action = QAction("Выход", triggered=exit_program)

    tray_menu.addAction(open_action)
    tray_menu.addAction(empty_action)
    
    # Инициализируем пункт автозапуска
    initialize_autostart_menu()
    
    # Инициализируем пункт "Показывать уведомления"
    initialize_notifications_menu()

    tray_menu.addSeparator()
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("Менеджер Корзины")
    tray_icon.show()

    timer = QTimer()
    timer.timeout.connect(periodic_update)
    timer.start(3000)  # Интервал обновления в миллисекундах (3 секунды)

    sys.exit(app.exec())
