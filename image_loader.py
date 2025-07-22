#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Загрузчик изображений
Асинхронная загрузка и отображение превью изображений
"""

import os
import hashlib
from typing import Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QNetworkAccessManager, QNetworkRequest, QUrl, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QBrush, QLinearGradient
from PyQt5.QtWidgets import QLabel
from PyQt5.QtNetwork import QNetworkReply

class ImageLoader(QObject):
    """Класс для асинхронной загрузки изображений"""
    
    # Сигналы
    image_loaded = pyqtSignal(QLabel, QPixmap)  # Изображение загружено
    image_error = pyqtSignal(QLabel, str)  # Ошибка загрузки
    
    def __init__(self, cache_dir: str = "image_cache", parent=None):
        super().__init__(parent)
        
        self.cache_dir = cache_dir
        self.network_manager = QNetworkAccessManager(self)
        self.active_requests: Dict[QNetworkReply, QLabel] = {}
        self.loading_labels: Dict[QLabel, bool] = {}
        
        # Создаем директорию для кэша изображений
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # Подключаем обработчик завершения запросов
        self.network_manager.finished.connect(self._on_request_finished)
        
        # Таймер для очистки старых изображений из кэша
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_cache)
        self.cleanup_timer.start(3600000)  # Очистка каждый час
        
    def load_image(self, url: str, target_label: QLabel, 
                   placeholder_text: str = "Загрузка...") -> None:
        """
        Загрузка изображения по URL
        
        Args:
            url: URL изображения
            target_label: QLabel для отображения изображения
            placeholder_text: Текст-заглушка во время загрузки
        """
        if not url or not target_label:
            return
            
        # Проверяем, не загружается ли уже изображение для этого label
        if target_label in self.loading_labels:
            return
            
        # Проверяем кэш
        cached_pixmap = self._get_cached_image(url)
        if cached_pixmap and not cached_pixmap.isNull():
            self.image_loaded.emit(target_label, cached_pixmap)
            return
            
        # Устанавливаем заглушку
        self._set_placeholder(target_label, placeholder_text)
        
        # Отмечаем что изображение загружается
        self.loading_labels[target_label] = True
        
        # Создаем сетевой запрос
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, "Steam Workshop Downloader/1.0")
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, 
                           QNetworkRequest.PreferCache)
        
        # Отправляем запрос
        reply = self.network_manager.get(request)
        self.active_requests[reply] = target_label
        
    def _on_request_finished(self, reply: QNetworkReply) -> None:
        """Обработка завершения сетевого запроса"""
        try:
            # Получаем связанный label
            target_label = self.active_requests.get(reply)
            if not target_label:
                reply.deleteLater()
                return
                
            # Удаляем из активных запросов
            del self.active_requests[reply]
            
            # Удаляем флаг загрузки
            if target_label in self.loading_labels:
                del self.loading_labels[target_label]
                
            # Проверяем ошибки
            if reply.error() != QNetworkReply.NoError:
                error_msg = reply.errorString()
                self._set_error_placeholder(target_label, f"Ошибка: {error_msg}")
                self.image_error.emit(target_label, error_msg)
                reply.deleteLater()
                return
                
            # Читаем данные изображения
            image_data = reply.readAll()
            if image_data.isEmpty():
                self._set_error_placeholder(target_label, "Пустое изображение")
                self.image_error.emit(target_label, "Пустые данные изображения")
                reply.deleteLater()
                return
                
            # Создаем QPixmap из данных
            pixmap = QPixmap()
            if not pixmap.loadFromData(image_data):
                self._set_error_placeholder(target_label, "Неверный формат")
                self.image_error.emit(target_label, "Неверный формат изображения")
                reply.deleteLater()
                return
                
            # Сохраняем в кэш
            url = reply.request().url().toString()
            self._cache_image(url, image_data)
            
            # Отправляем сигнал о загрузке
            self.image_loaded.emit(target_label, pixmap)
            
        except Exception as e:
            print(f"Ошибка обработки загруженного изображения: {e}")
            if target_label:
                self._set_error_placeholder(target_label, "Ошибка обработки")
                
        finally:
            reply.deleteLater()
            
    def _get_cached_image(self, url: str) -> Optional[QPixmap]:
        """Получение изображения из кэша"""
        try:
            cache_filename = self._get_cache_filename(url)
            cache_path = os.path.join(self.cache_dir, cache_filename)
            
            if os.path.exists(cache_path):
                # Проверяем возраст файла (кэш на 24 часа)
                file_age = os.path.getmtime(cache_path)
                import time
                if time.time() - file_age < 86400:  # 24 часа
                    pixmap = QPixmap(cache_path)
                    if not pixmap.isNull():
                        return pixmap
                else:
                    # Удаляем устаревший файл
                    os.remove(cache_path)
                    
        except Exception as e:
            print(f"Ошибка загрузки из кэша: {e}")
            
        return None
        
    def _cache_image(self, url: str, image_data) -> None:
        """Сохранение изображения в кэш"""
        try:
            cache_filename = self._get_cache_filename(url)
            cache_path = os.path.join(self.cache_dir, cache_filename)
            
            with open(cache_path, 'wb') as f:
                f.write(image_data.data())
                
        except Exception as e:
            print(f"Ошибка сохранения в кэш: {e}")
            
    def _get_cache_filename(self, url: str) -> str:
        """Получение имени файла для кэша"""
        # Создаем хэш от URL для безопасного имени файла
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Пытаемся определить расширение из URL
        extension = ".jpg"
        if url.lower().endswith(('.png', '.gif', '.bmp', '.webp')):
            extension = url[url.rfind('.'):].lower()
            
        return f"{url_hash}{extension}"
        
    def _set_placeholder(self, label: QLabel, text: str) -> None:
        """Установка заглушки во время загрузки"""
        # Создаем красивую заглушку
        pixmap = QPixmap(label.size())
        pixmap.fill(QColor(43, 67, 83))  # Темно-серый фон
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Градиентный фон
        gradient = QLinearGradient(0, 0, pixmap.width(), pixmap.height())
        gradient.setColorAt(0, QColor(43, 67, 83))
        gradient.setColorAt(1, QColor(27, 40, 56))
        painter.fillRect(pixmap.rect(), QBrush(gradient))
        
        # Текст
        painter.setPen(QColor(199, 213, 224))
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x84, text)  # Qt.AlignCenter | Qt.TextWordWrap
        
        painter.end()
        
        label.setPixmap(pixmap)
        
    def _set_error_placeholder(self, label: QLabel, error_text: str) -> None:
        """Установка заглушки при ошибке"""
        # Создаем заглушку с ошибкой
        pixmap = QPixmap(label.size())
        pixmap.fill(QColor(60, 65, 76))  # Серый фон
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Фон с красноватым оттенком
        gradient = QLinearGradient(0, 0, pixmap.width(), pixmap.height())
        gradient.setColorAt(0, QColor(60, 65, 76))
        gradient.setColorAt(1, QColor(80, 45, 45))
        painter.fillRect(pixmap.rect(), QBrush(gradient))
        
        # Текст ошибки
        painter.setPen(QColor(200, 150, 150))
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x84, f"Изображение\nнедоступно\n\n{error_text}")
        
        painter.end()
        
        label.setPixmap(pixmap)
        
    def _cleanup_cache(self) -> None:
        """Очистка старых файлов из кэша"""
        try:
            import time
            current_time = time.time()
            max_age = 86400 * 7  # 7 дней
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age:
                        try:
                            os.remove(file_path)
                            print(f"Удален старый файл кэша: {filename}")
                        except OSError:
                            pass
                            
        except Exception as e:
            print(f"Ошибка очистки кэша изображений: {e}")
            
    def cancel_all_requests(self) -> None:
        """Отмена всех активных запросов"""
        for reply in list(self.active_requests.keys()):
            reply.abort()
            reply.deleteLater()
            
        self.active_requests.clear()
        self.loading_labels.clear()
        
    def get_cache_stats(self) -> Dict[str, int]:
        """Получение статистики кэша изображений"""
        try:
            total_files = 0
            total_size = 0
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    total_files += 1
                    total_size += os.path.getsize(file_path)
                    
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'active_requests': len(self.active_requests)
            }
            
        except Exception as e:
            print(f"Ошибка получения статистики кэша: {e}")
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'active_requests': len(self.active_requests)
            }
            
    def clear_cache(self) -> bool:
        """Очистка всего кэша изображений"""
        try:
            # Отменяем все активные запросы
            self.cancel_all_requests()
            
            # Удаляем все файлы кэша
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    
            return True
            
        except Exception as e:
            print(f"Ошибка очистки кэша изображений: {e}")
            return False
            
    def preload_images(self, urls: list, labels: list) -> None:
        """Предварительная загрузка изображений"""
        if len(urls) != len(labels):
            print("Количество URL и labels должно совпадать")
            return
            
        for url, label in zip(urls, labels):
            if url and label:
                self.load_image(url, label)
                
    def set_default_placeholder(self, label: QLabel, width: int = 200, height: int = 150) -> None:
        """Установка стандартной заглушки"""
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(43, 67, 83))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Градиентный фон
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor(43, 67, 83))
        gradient.setColorAt(1, QColor(27, 40, 56))
        painter.fillRect(0, 0, width, height, QBrush(gradient))
        
        # Рамка
        painter.setPen(QColor(60, 65, 76))
        painter.drawRect(0, 0, width-1, height-1)
        
        # Текст
        painter.setPen(QColor(143, 152, 160))
        font = QFont("Arial", 12)
        painter.setFont(font)
        painter.drawText(0, 0, width, height, 0x84, "Нет изображения")
        
        painter.end()
        
        label.setPixmap(pixmap)
