#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Главное окно интерфейса
Современный интерфейс в стиле Steam для выбора игр и скачивания модов
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLineEdit, QListWidget, QListWidgetItem, QScrollArea,
                            QLabel, QPushButton, QGridLayout, QFrame, QMessageBox,
                            QFileDialog, QProgressBar, QSplitter, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor

from steam_api import SteamAPI
from worker import GameLoaderThread, WorkshopLoaderThread
from cache import Cache
from image_loader import ImageLoader
from download_manager import DownloadManager
from auth import SteamAuthDialog

class GameListWidget(QListWidget):
    """Кастомный виджет списка игр с современным дизайном"""
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QListWidget {
                background-color: #2a2f3a;
                border: 1px solid #3c414c;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                color: #c7d5e0;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #3c414c;
                border-radius: 3px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background-color: #3c414c;
            }
            QListWidget::item:selected {
                background-color: #4c9eff;
                color: white;
            }
        """)

class WorkshopItemWidget(QFrame):
    """Виджет для отображения элемента мастерской"""
    download_requested = pyqtSignal(dict)
    
    def __init__(self, item_data):
        super().__init__()
        self.item_data = item_data
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса элемента"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #2a2f3a;
                border: 1px solid #3c414c;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
            QFrame:hover {
                border-color: #4c9eff;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Превью изображение
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 150)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #1b2838;
                border: 1px solid #3c414c;
                border-radius: 5px;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("Загрузка...")
        layout.addWidget(self.image_label)
        
        # Название
        title_label = QLabel(self.item_data.get('title', 'Без названия'))
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #c7d5e0; margin: 5px 0px;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Описание (краткое)
        description = self.item_data.get('description', '')[:100] + "..." if len(self.item_data.get('description', '')) > 100 else self.item_data.get('description', '')
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setStyleSheet("color: #8f98a0; margin: 5px 0px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Кнопка скачивания
        download_btn = QPushButton("Скачать")
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4c9eff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5aa3ff;
            }
            QPushButton:pressed {
                background-color: #3d8ce6;
            }
        """)
        download_btn.clicked.connect(self.request_download)
        layout.addWidget(download_btn)
        
    def request_download(self):
        """Запрос на скачивание элемента"""
        self.download_requested.emit(self.item_data)

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.steam_api = SteamAPI()
        self.cache = Cache()
        self.image_loader = ImageLoader()
        self.download_manager = DownloadManager()
        
        self.current_game = None
        self.workshop_items = []
        
        self.setup_ui()
        self.setup_connections()
        self.load_initial_games()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Steam Workshop Downloader")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 600)
        
        # Применяем темную тему
        self.setStyleSheet("""
            QMainWindow {
                background-color: #171a21;
                color: #c7d5e0;
            }
            QLabel {
                color: #c7d5e0;
            }
        """)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QHBoxLayout(central_widget)
        
        # Создаем сплиттер для изменяемых панелей
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Левая панель - выбор игр
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Правая панель - элементы мастерской
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Устанавливаем пропорции панелей
        splitter.setSizes([300, 900])
        
    def create_left_panel(self):
        """Создание левой панели с играми"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1b2838;
                border-right: 1px solid #3c414c;
            }
        """)
        
        layout = QVBoxLayout(panel)
        
        # Заголовок
        title_label = QLabel("Выбор игры")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #c7d5e0; padding: 10px; border-bottom: 1px solid #3c414c;")
        layout.addWidget(title_label)
        
        # Поиск игр
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск игр...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2f3a;
                border: 1px solid #3c414c;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                color: #c7d5e0;
                margin: 10px;
            }
            QLineEdit:focus {
                border-color: #4c9eff;
            }
        """)
        layout.addWidget(self.search_input)
        
        # Список игр
        self.games_list = GameListWidget()
        layout.addWidget(self.games_list)
        
        # Статус загрузки
        self.loading_label = QLabel("Загрузка игр...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #8f98a0; padding: 10px;")
        layout.addWidget(self.loading_label)
        
        return panel
        
    def create_right_panel(self):
        """Создание правой панели с элементами мастерской"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #171a21;
            }
        """)
        
        layout = QVBoxLayout(panel)
        
        # Заголовок с названием игры
        self.game_title_label = QLabel("Выберите игру")
        self.game_title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.game_title_label.setStyleSheet("color: #c7d5e0; padding: 15px; border-bottom: 1px solid #3c414c;")
        layout.addWidget(self.game_title_label)
        
        # Область прокрутки для элементов мастерской
        self.workshop_scroll = QScrollArea()
        self.workshop_scroll.setWidgetResizable(True)
        self.workshop_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #171a21;
                border: none;
            }
        """)
        
        # Контейнер для элементов мастерской
        self.workshop_container = QWidget()
        self.workshop_layout = QGridLayout(self.workshop_container)
        self.workshop_layout.setSpacing(10)
        
        self.workshop_scroll.setWidget(self.workshop_container)
        layout.addWidget(self.workshop_scroll)
        
        # Статус загрузки мастерской
        self.workshop_loading_label = QLabel("")
        self.workshop_loading_label.setAlignment(Qt.AlignCenter)
        self.workshop_loading_label.setStyleSheet("color: #8f98a0; padding: 20px; font-size: 14px;")
        layout.addWidget(self.workshop_loading_label)
        
        return panel
        
    def setup_connections(self):
        """Настройка соединений сигналов"""
        # Поиск игр
        self.search_input.textChanged.connect(self.filter_games)
        
        # Выбор игры
        self.games_list.itemClicked.connect(self.on_game_selected)
        
        # Загрузчик изображений
        self.image_loader.image_loaded.connect(self.on_image_loaded)
        
        # Менеджер загрузок
        self.download_manager.download_progress.connect(self.on_download_progress)
        self.download_manager.download_finished.connect(self.on_download_finished)
        self.download_manager.download_error.connect(self.on_download_error)
        
    def load_initial_games(self):
        """Загрузка начального списка игр"""
        self.game_loader_thread = GameLoaderThread(self.steam_api, self.cache)
        self.game_loader_thread.games_loaded.connect(self.on_games_loaded)
        self.game_loader_thread.loading_error.connect(self.on_loading_error)
        self.game_loader_thread.start()
        
    def on_games_loaded(self, games):
        """Обработка загруженных игр"""
        self.loading_label.hide()
        self.games_list.clear()
        
        for game in games:
            item = QListWidgetItem(game['name'])
            item.setData(Qt.UserRole, game)
            self.games_list.addItem(item)
            
    def on_loading_error(self, error_message):
        """Обработка ошибки загрузки"""
        self.loading_label.setText(f"Ошибка: {error_message}")
        QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список игр:\n{error_message}")
        
    def filter_games(self, text):
        """Фильтрация списка игр по поисковому запросу"""
        for i in range(self.games_list.count()):
            item = self.games_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
            
    def on_game_selected(self, item):
        """Обработка выбора игры"""
        game_data = item.data(Qt.UserRole)
        self.current_game = game_data
        self.game_title_label.setText(f"Мастерская: {game_data['name']}")
        
        # Очищаем предыдущие элементы
        self.clear_workshop_items()
        
        # Показываем статус загрузки
        self.workshop_loading_label.setText("Загрузка элементов мастерской...")
        self.workshop_loading_label.show()
        
        # Загружаем элементы мастерской
        self.workshop_loader_thread = WorkshopLoaderThread(
            self.steam_api, self.cache, game_data['appid']
        )
        self.workshop_loader_thread.workshop_loaded.connect(self.on_workshop_loaded)
        self.workshop_loader_thread.loading_error.connect(self.on_workshop_loading_error)
        self.workshop_loader_thread.start()
        
    def on_workshop_loaded(self, items):
        """Обработка загруженных элементов мастерской"""
        self.workshop_loading_label.hide()
        self.workshop_items = items
        
        # Добавляем элементы в сетку
        row, col = 0, 0
        max_cols = 3
        
        for item_data in items:
            workshop_widget = WorkshopItemWidget(item_data)
            workshop_widget.download_requested.connect(self.on_download_requested)
            
            self.workshop_layout.addWidget(workshop_widget, row, col)
            
            # Загружаем превью изображение
            if 'preview_url' in item_data:
                self.image_loader.load_image(item_data['preview_url'], workshop_widget.image_label)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def on_workshop_loading_error(self, error_message):
        """Обработка ошибки загрузки мастерской"""
        self.workshop_loading_label.setText(f"Ошибка: {error_message}")
        QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить мастерскую:\n{error_message}")
        
    def clear_workshop_items(self):
        """Очистка элементов мастерской"""
        while self.workshop_layout.count():
            child = self.workshop_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def on_download_requested(self, item_data):
        """Обработка запроса на скачивание"""
        # Выбираем папку для скачивания
        download_dir = QFileDialog.getExistingDirectory(
            self, "Выберите папку для скачивания", ""
        )
        
        if download_dir:
            # Запускаем скачивание
            self.download_manager.start_download(item_data, download_dir)
            
    def on_download_progress(self, progress):
        """Обработка прогресса скачивания"""
        # Можно добавить прогресс-бар в статус-бар
        pass
        
    def on_download_finished(self, file_path):
        """Обработка завершения скачивания"""
        QMessageBox.information(self, "Скачивание завершено", f"Файл сохранен:\n{file_path}")
        
    def on_download_error(self, error_message):
        """Обработка ошибки скачивания"""
        QMessageBox.critical(self, "Ошибка скачивания", error_message)
        
    def on_image_loaded(self, label, pixmap):
        """Обработка загруженного изображения"""
        if pixmap and not pixmap.isNull():
            # Масштабируем изображение
            scaled_pixmap = pixmap.scaled(
                label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            label.setPixmap(scaled_pixmap)
        else:
            label.setText("Изображение\nнедоступно")
