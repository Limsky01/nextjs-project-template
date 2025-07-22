#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Скрипт запуска
Проверяет зависимости и запускает приложение
"""

import sys
import os
import subprocess
import importlib.util

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 7):
        print("❌ Ошибка: Требуется Python 3.7 или выше")
        print(f"   Текущая версия: {sys.version}")
        return False
    else:
        print(f"✅ Python версия: {sys.version.split()[0]}")
        return True

def check_module(module_name, package_name=None):
    """Проверка наличия модуля"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print(f"✅ {module_name} установлен")
            return True
        else:
            print(f"❌ {module_name} не найден")
            if package_name:
                print(f"   Установите: pip install {package_name}")
            return False
    except ImportError:
        print(f"❌ {module_name} не найден")
        if package_name:
            print(f"   Установите: pip install {package_name}")
        return False

def check_dependencies():
    """Проверка всех зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    dependencies = [
        ("PyQt5", "PyQt5"),
        ("requests", "requests"),
        ("PIL", "Pillow"),
        ("cryptography", "cryptography"),
    ]
    
    missing_deps = []
    
    for module, package in dependencies:
        if not check_module(module, package):
            missing_deps.append(package)
    
    if missing_deps:
        print(f"\n❌ Отсутствуют зависимости: {', '.join(missing_deps)}")
        print("📦 Установите их командой:")
        print(f"   pip install {' '.join(missing_deps)}")
        print("\nИли установите все зависимости:")
        print("   pip install -r requirements.txt")
        return False
    
    print("\n✅ Все зависимости установлены!")
    return True

def install_dependencies():
    """Автоматическая установка зависимостей"""
    print("📦 Установка зависимостей...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости успешно установлены!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False
    except FileNotFoundError:
        print("❌ Файл requirements.txt не найден")
        return False

def check_files():
    """Проверка наличия необходимых файлов"""
    print("📁 Проверка файлов...")
    
    required_files = [
        "main.py",
        "ui_main.py", 
        "steam_api.py",
        "cache.py",
        "worker.py",
        "image_loader.py",
        "download_manager.py",
        "auth.py"
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} не найден")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    print("\n✅ Все файлы на месте!")
    return True

def create_directories():
    """Создание необходимых директорий"""
    print("📂 Создание директорий...")
    
    directories = [
        "cache",
        "image_cache",
        os.path.expanduser("~/Downloads/Steam Workshop")
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ {directory}")
        except Exception as e:
            print(f"❌ Ошибка создания {directory}: {e}")

def run_application():
    """Запуск приложения"""
    print("\n🚀 Запуск Steam Workshop Downloader...")
    print("=" * 50)
    
    try:
        # Импортируем и запускаем main
        import main
        # main.main() будет вызван автоматически при импорте
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return False
    
    return True

def main():
    """Главная функция"""
    print("🎮 Steam Workshop Downloader")
    print("=" * 50)
    
    # Проверка версии Python
    if not check_python_version():
        input("\nНажмите Enter для выхода...")
        return
    
    # Проверка файлов
    if not check_files():
        input("\nНажмите Enter для выхода...")
        return
    
    # Создание директорий
    create_directories()
    
    # Проверка зависимостей
    if not check_dependencies():
        response = input("\n❓ Установить зависимости автоматически? (y/n): ")
        if response.lower() in ['y', 'yes', 'да', 'д']:
            if not install_dependencies():
                input("\nНажмите Enter для выхода...")
                return
        else:
            print("❌ Невозможно запустить приложение без зависимостей")
            input("\nНажмите Enter для выхода...")
            return
    
    # Запуск приложения
    try:
        run_application()
    except KeyboardInterrupt:
        print("\n\n👋 Приложение закрыто пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
