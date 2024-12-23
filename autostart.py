import os
import sys
from pathlib import Path
import winshell

def get_startup_folder():
    """
    Возвращает путь к папке автозапуска пользователя.
    """
    return winshell.startup()

def get_executable_path():
    """
    Возвращает путь к исполняемому файлу приложения.
    Если приложение собрано с помощью PyInstaller, используется sys._MEIPASS.
    """
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(sys.argv[0])

def get_shortcut_path():
    """
    Возвращает путь к ярлыку приложения в папке автозапуска.
    """
    startup_folder = get_startup_folder()
    executable_path = get_executable_path()
    shortcut_name = Path(executable_path).stem + '.lnk'
    return os.path.join(startup_folder, shortcut_name)

def is_autostart_enabled():
    """
    Проверяет, добавлено ли приложение в автозапуск.
    """
    return Path(get_shortcut_path()).exists()

def enable_autostart():
    """
    Добавляет приложение в автозапуск, создавая ярлык в папке автозапуска.
    """
    try:
        shortcut_path = get_shortcut_path()
        executable_path = get_executable_path()
        with winshell.shortcut(shortcut_path) as link:
            link.path = executable_path
            link.description = "Recycle Bin Manager"
            link.working_directory = os.path.dirname(executable_path)
            # Если вам нужно, можно добавить иконку
            # link.icon_location = (executable_path, 0)
        return True
    except Exception as e:
        print(f"Ошибка при добавлении в автозапуск: {e}")
        return False

def disable_autostart():
    """
    Удаляет приложение из автозапуска, удаляя ярлык из папки автозапуска.
    """
    try:
        shortcut_path = get_shortcut_path()
        if Path(shortcut_path).exists():
            Path(shortcut_path).unlink()
            return True
        return False
    except Exception as e:
        print(f"Ошибка при удалении из автозапуска: {e}")
        return False
