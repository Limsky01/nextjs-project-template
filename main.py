#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Главный файл запуска
Современное приложение для скачивания модов из мастерской Steam
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QFont
from ui_main import MainWindow

class SplashScreen(QSplashScreen):
    """Экран загрузки с анимацией"""
    
    def __init__(self):
        # Создаем красивый градиентный фон
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Создаем градиент в стиле Steam
        gradient = QLinearGradient(0, 0, 600, 400)
        gradient.setColorAt(0, QColor(23, 26, 33))  # Темно-серый
        gradient.setColorAt(0.5, QColor(39, 43, 53))  # Средний серый
        gradient.setColorAt(1, QColor(23, 26, 33))  # Темно-серый
        
        painter.fillRect(0, 0, 600, 400, gradient)
        
        # Добавляем текст
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Steam Workshop\nDownloader")
        
        # Добавляем подзаголовок
        font = QFont("Arial", 12)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(50, 320, 500, 50, Qt.AlignCenter, "Загрузка приложения...")
        
        painter.end()
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

class InitializationThread(QThread):
    """Поток для инициализации приложения в фоне"""
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    
    def run(self):
        """Имитация загрузки компонентов"""
        import time
        
        self.progress.emit("Инициализация Steam API...")
        time.sleep(0.8)
        
        self.progress.emit("Загрузка кэша...")
        time.sleep(0.5)
        
        self.progress.emit("Подготовка интерфейса...")
        time.sleep(0.7)
        
        self.finished.emit()

def main():
    """Главная функция запуска приложения"""
    app = QApplication(sys.argv)
    app.setApplicationName("Steam Workshop Downloader")
    app.setApplicationVersion("1.0.0")
    
    # Устанавливаем темную тему для всего приложения
    app.setStyleSheet("""
        QApplication {
            background-color: #171a21;
            color: #c7d5e0;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    
    # Создаем и показываем splash screen
    splash = SplashScreen()
    splash.show()
    
    # Создаем поток инициализации
    init_thread = InitializationThread()
    
    def update_splash_message(message):
        splash.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255))
    
    def show_main_window():
        """Показываем главное окно после загрузки"""
        try:
            main_window = MainWindow()
            main_window.show()
            splash.finish(main_window)
        except Exception as e:
            print(f"Ошибка при запуске главного окна: {e}")
            sys.exit(1)
    
    # Подключаем сигналы
    init_thread.progress.connect(update_splash_message)
    init_thread.finished.connect(show_main_window)
    
    # Запускаем инициализацию
    init_thread.start()
    
    # Запускаем приложение
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\nПриложение закрыто пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
