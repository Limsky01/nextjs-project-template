#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Модуль авторизации
Поддержка Steam Guard авторизации для доступа к приватным элементам
"""

import json
import time
import requests
from typing import Dict, Optional, Any
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox, QCheckBox,
                            QProgressBar, QTextEdit, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor

class SteamAuthThread(QThread):
    """Поток для авторизации Steam"""
    
    # Сигналы
    auth_success = pyqtSignal(dict)  # session_data
    auth_error = pyqtSignal(str)  # error_message
    auth_progress = pyqtSignal(str)  # status_message
    captcha_required = pyqtSignal(str)  # captcha_url
    guard_code_required = pyqtSignal()
    
    def __init__(self, username: str, password: str, guard_code: str = "", 
                 captcha_text: str = "", parent=None):
        super().__init__(parent)
        self.username = username
        self.password = password
        self.guard_code = guard_code
        self.captcha_text = captcha_text
        self.session = requests.Session()
        
    def run(self):
        """Основная функция авторизации"""
        try:
            self.auth_progress.emit("Подключение к Steam...")
            
            # Получаем RSA ключ для шифрования пароля
            rsa_key = self._get_rsa_key()
            if not rsa_key:
                self.auth_error.emit("Не удалось получить ключ шифрования")
                return
                
            self.auth_progress.emit("Шифрование данных...")
            
            # Шифруем пароль (упрощенная версия)
            encrypted_password = self._encrypt_password(self.password, rsa_key)
            
            self.auth_progress.emit("Отправка данных авторизации...")
            
            # Отправляем данные для авторизации
            auth_result = self._perform_login(encrypted_password, rsa_key)
            
            if auth_result.get('success'):
                self.auth_progress.emit("Авторизация успешна")
                self.auth_success.emit(auth_result)
            else:
                error_msg = auth_result.get('message', 'Неизвестная ошибка')
                
                if 'captcha' in error_msg.lower():
                    captcha_url = auth_result.get('captcha_gid')
                    if captcha_url:
                        self.captcha_required.emit(captcha_url)
                        return
                        
                if 'guard' in error_msg.lower() or 'code' in error_msg.lower():
                    self.guard_code_required.emit()
                    return
                    
                self.auth_error.emit(error_msg)
                
        except Exception as e:
            self.auth_error.emit(f"Ошибка авторизации: {str(e)}")
            
    def _get_rsa_key(self) -> Optional[Dict[str, Any]]:
        """Получение RSA ключа для шифрования"""
        try:
            url = "https://steamcommunity.com/login/getrsakey/"
            data = {'username': self.username}
            
            response = self.session.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('success'):
                return result
            else:
                return None
                
        except Exception as e:
            print(f"Ошибка получения RSA ключа: {e}")
            return None
            
    def _encrypt_password(self, password: str, rsa_key: Dict[str, Any]) -> str:
        """Шифрование пароля (упрощенная версия)"""
        # В реальном приложении здесь должно быть RSA шифрование
        # Для демонстрации возвращаем base64 кодированный пароль
        import base64
        return base64.b64encode(password.encode()).decode()
        
    def _perform_login(self, encrypted_password: str, rsa_key: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение авторизации"""
        try:
            url = "https://steamcommunity.com/login/dologin/"
            
            data = {
                'username': self.username,
                'password': encrypted_password,
                'emailauth': self.guard_code,
                'loginfriendlyname': 'Steam Workshop Downloader',
                'captchagid': '-1',
                'captcha_text': self.captcha_text,
                'emailsteamid': '',
                'rsatimestamp': rsa_key.get('timestamp', ''),
                'remember_login': 'false',
                'donotcache': str(int(time.time() * 1000))
            }
            
            response = self.session.post(url, data=data, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            
            # Добавляем cookies в результат для последующего использования
            if result.get('success'):
                result['cookies'] = dict(self.session.cookies)
                result['session'] = self.session
                
            return result
            
        except Exception as e:
            return {'success': False, 'message': str(e)}

class SteamAuthDialog(QDialog):
    """Диалог авторизации Steam"""
    
    # Сигналы
    auth_completed = pyqtSignal(dict)  # session_data
    auth_cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_data = None
        self.auth_thread = None
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle("Авторизация Steam")
        self.setFixedSize(400, 500)
        self.setModal(True)
        
        # Применяем темную тему
        self.setStyleSheet("""
            QDialog {
                background-color: #1b2838;
                color: #c7d5e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3c414c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit {
                background-color: #2a2f3a;
                border: 1px solid #3c414c;
                border-radius: 3px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4c9eff;
            }
            QPushButton {
                background-color: #4c9eff;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5aa3ff;
            }
            QPushButton:pressed {
                background-color: #3d8ce6;
            }
            QPushButton:disabled {
                background-color: #3c414c;
                color: #8f98a0;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Авторизация Steam")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("margin: 10px; color: #c7d5e0;")
        layout.addWidget(title_label)
        
        # Описание
        desc_label = QLabel("Для доступа к приватным элементам мастерской\nтребуется авторизация в Steam")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #8f98a0; margin-bottom: 20px;")
        layout.addWidget(desc_label)
        
        # Группа данных авторизации
        auth_group = QGroupBox("Данные для входа")
        auth_layout = QFormLayout(auth_group)
        
        # Поле логина
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин Steam")
        auth_layout.addRow("Логин:", self.username_input)
        
        # Поле пароля
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        auth_layout.addRow("Пароль:", self.password_input)
        
        layout.addWidget(auth_group)
        
        # Группа Steam Guard
        guard_group = QGroupBox("Steam Guard")
        guard_layout = QFormLayout(guard_group)
        
        # Поле кода Steam Guard
        self.guard_code_input = QLineEdit()
        self.guard_code_input.setPlaceholderText("Код из приложения или email")
        self.guard_code_input.setEnabled(False)
        guard_layout.addRow("Код:", self.guard_code_input)
        
        # Поле капчи
        self.captcha_input = QLineEdit()
        self.captcha_input.setPlaceholderText("Текст с картинки")
        self.captcha_input.setEnabled(False)
        guard_layout.addRow("Капча:", self.captcha_input)
        
        layout.addWidget(guard_group)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #8f98a0; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # Чекбокс сохранения сессии
        self.remember_checkbox = QCheckBox("Запомнить авторизацию")
        self.remember_checkbox.setStyleSheet("margin: 10px;")
        layout.addWidget(self.remember_checkbox)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Войти")
        self.login_button.setDefault(True)
        buttons_layout.addWidget(self.login_button)
        
        self.cancel_button = QPushButton("Отмена")
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        
        # Информационное поле
        info_text = QTextEdit()
        info_text.setMaximumHeight(80)
        info_text.setReadOnly(True)
        info_text.setPlainText(
            "Примечание: Ваши данные используются только для авторизации "
            "и не сохраняются в приложении. Для безопасности рекомендуется "
            "использовать Steam Guard."
        )
        info_text.setStyleSheet("""
            QTextEdit {
                background-color: #2a2f3a;
                border: 1px solid #3c414c;
                border-radius: 3px;
                padding: 5px;
                font-size: 10px;
                color: #8f98a0;
            }
        """)
        layout.addWidget(info_text)
        
    def setup_connections(self):
        """Настройка соединений сигналов"""
        self.login_button.clicked.connect(self.start_auth)
        self.cancel_button.clicked.connect(self.reject)
        
        # Enter в полях ввода
        self.username_input.returnPressed.connect(self.start_auth)
        self.password_input.returnPressed.connect(self.start_auth)
        self.guard_code_input.returnPressed.connect(self.start_auth)
        self.captcha_input.returnPressed.connect(self.start_auth)
        
    def start_auth(self):
        """Начало авторизации"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
            
        # Отключаем интерфейс
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Неопределенный прогресс
        
        # Создаем поток авторизации
        guard_code = self.guard_code_input.text().strip()
        captcha_text = self.captcha_input.text().strip()
        
        self.auth_thread = SteamAuthThread(username, password, guard_code, captcha_text)
        
        # Подключаем сигналы
        self.auth_thread.auth_success.connect(self.on_auth_success)
        self.auth_thread.auth_error.connect(self.on_auth_error)
        self.auth_thread.auth_progress.connect(self.on_auth_progress)
        self.auth_thread.captcha_required.connect(self.on_captcha_required)
        self.auth_thread.guard_code_required.connect(self.on_guard_code_required)
        
        # Запускаем поток
        self.auth_thread.start()
        
    def on_auth_success(self, session_data: Dict[str, Any]):
        """Обработка успешной авторизации"""
        self.session_data = session_data
        self.status_label.setText("Авторизация успешна!")
        self.status_label.setStyleSheet("color: #4c9eff; margin: 10px;")
        
        # Сохраняем сессию если нужно
        if self.remember_checkbox.isChecked():
            self._save_session(session_data)
            
        # Закрываем диалог с успехом
        QTimer.singleShot(1000, self.accept)
        
    def on_auth_error(self, error_message: str):
        """Обработка ошибки авторизации"""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Ошибка: {error_message}")
        self.status_label.setStyleSheet("color: #ff6b6b; margin: 10px;")
        
        QMessageBox.critical(self, "Ошибка авторизации", error_message)
        
    def on_auth_progress(self, message: str):
        """Обработка прогресса авторизации"""
        self.status_label.setText(message)
        
    def on_captcha_required(self, captcha_url: str):
        """Обработка требования капчи"""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.captcha_input.setEnabled(True)
        self.status_label.setText("Требуется ввод капчи")
        
        QMessageBox.information(self, "Требуется капча", 
                              "Введите текст с картинки капчи и повторите попытку")
        
    def on_guard_code_required(self):
        """Обработка требования кода Steam Guard"""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.guard_code_input.setEnabled(True)
        self.guard_code_input.setFocus()
        self.status_label.setText("Требуется код Steam Guard")
        
        QMessageBox.information(self, "Steam Guard", 
                              "Введите код из приложения Steam Guard или email")
        
    def set_ui_enabled(self, enabled: bool):
        """Включение/отключение интерфейса"""
        self.username_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.login_button.setEnabled(enabled)
        
    def get_session_data(self) -> Optional[Dict[str, Any]]:
        """Получение данных сессии"""
        return self.session_data
        
    def _save_session(self, session_data: Dict[str, Any]):
        """Сохранение сессии (упрощенная версия)"""
        try:
            # В реальном приложении здесь должно быть безопасное сохранение
            # Для демонстрации просто выводим сообщение
            print("Сессия сохранена (функция не реализована)")
        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")
            
    def _load_session(self) -> Optional[Dict[str, Any]]:
        """Загрузка сохраненной сессии"""
        try:
            # В реальном приложении здесь должна быть загрузка сессии
            return None
        except Exception as e:
            print(f"Ошибка загрузки сессии: {e}")
            return None

class SteamSession:
    """Класс для управления сессией Steam"""
    
    def __init__(self):
        self.session_data = None
        self.is_authenticated = False
        self.session = requests.Session()
        
    def authenticate(self, parent_widget=None) -> bool:
        """Авторизация пользователя"""
        # Проверяем сохраненную сессию
        saved_session = self._load_saved_session()
        if saved_session and self._validate_session(saved_session):
            self.session_data = saved_session
            self.is_authenticated = True
            return True
            
        # Показываем диалог авторизации
        auth_dialog = SteamAuthDialog(parent_widget)
        if auth_dialog.exec_() == QDialog.Accepted:
            self.session_data = auth_dialog.get_session_data()
            self.is_authenticated = True
            
            # Настраиваем сессию
            if self.session_data and 'cookies' in self.session_data:
                for name, value in self.session_data['cookies'].items():
                    self.session.cookies.set(name, value)
                    
            return True
            
        return False
        
    def logout(self):
        """Выход из системы"""
        self.session_data = None
        self.is_authenticated = False
        self.session.cookies.clear()
        self._clear_saved_session()
        
    def get_authenticated_session(self) -> Optional[requests.Session]:
        """Получение авторизованной сессии"""
        if self.is_authenticated:
            return self.session
        return None
        
    def _validate_session(self, session_data: Dict[str, Any]) -> bool:
        """Проверка валидности сессии"""
        try:
            # Простая проверка - в реальном приложении должна быть более сложная
            return 'cookies' in session_data and session_data.get('success', False)
        except Exception:
            return False
            
    def _load_saved_session(self) -> Optional[Dict[str, Any]]:
        """Загрузка сохраненной сессии"""
        # В реальном приложении здесь должна быть загрузка из безопасного хранилища
        return None
        
    def _clear_saved_session(self):
        """Очистка сохраненной сессии"""
        # В реальном приложении здесь должна быть очистка сохраненных данных
        pass

# Глобальный экземпляр сессии
steam_session = SteamSession()
