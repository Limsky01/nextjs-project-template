#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Менеджер загрузок
Управление загрузкой файлов из мастерской Steam
"""

import os
import time
import requests
from typing import Dict, Any, Optional
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from urllib.parse import urlparse, unquote

class DownloadThread(QThread):
    """Поток для загрузки файла"""
    
    # Сигналы
    progress_updated = pyqtSignal(int, int, int)  # downloaded, total, percentage
    download_finished = pyqtSignal(str)  # file_path
    download_error = pyqtSignal(str)  # error_message
    speed_updated = pyqtSignal(float)  # download_speed in MB/s
    
    def __init__(self, url: str, file_path: str, item_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.url = url
        self.file_path = file_path
        self.item_data = item_data
        self.is_cancelled = False
        self.chunk_size = 8192  # 8KB chunks
        
    def run(self):
        """Основная функция загрузки"""
        try:
            # Создаем директорию если её нет
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Начинаем загрузку
            response = requests.get(self.url, stream=True, timeout=30, headers={
                'User-Agent': 'Steam Workshop Downloader/1.0'
            })
            response.raise_for_status()
            
            # Получаем размер файла
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            # Переменные для расчета скорости
            start_time = time.time()
            last_time = start_time
            last_downloaded = 0
            
            # Загружаем файл по частям
            with open(self.file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if self.is_cancelled:
                        # Удаляем частично загруженный файл
                        try:
                            f.close()
                            os.remove(self.file_path)
                        except OSError:
                            pass
                        return
                        
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Обновляем прогресс
                        if total_size > 0:
                            percentage = int((downloaded_size / total_size) * 100)
                        else:
                            percentage = 0
                            
                        self.progress_updated.emit(downloaded_size, total_size, percentage)
                        
                        # Рассчитываем скорость загрузки
                        current_time = time.time()
                        if current_time - last_time >= 1.0:  # Обновляем скорость каждую секунду
                            time_diff = current_time - last_time
                            bytes_diff = downloaded_size - last_downloaded
                            speed_mbps = (bytes_diff / time_diff) / (1024 * 1024)
                            
                            self.speed_updated.emit(speed_mbps)
                            
                            last_time = current_time
                            last_downloaded = downloaded_size
                            
            if not self.is_cancelled:
                self.download_finished.emit(self.file_path)
                
        except requests.exceptions.RequestException as e:
            if not self.is_cancelled:
                self.download_error.emit(f"Ошибка сети: {str(e)}")
        except OSError as e:
            if not self.is_cancelled:
                self.download_error.emit(f"Ошибка файловой системы: {str(e)}")
        except Exception as e:
            if not self.is_cancelled:
                self.download_error.emit(f"Неожиданная ошибка: {str(e)}")
                
    def cancel(self):
        """Отмена загрузки"""
        self.is_cancelled = True

class DownloadManager(QObject):
    """Менеджер загрузок файлов"""
    
    # Сигналы
    download_started = pyqtSignal(str, dict)  # file_path, item_data
    download_progress = pyqtSignal(str, int, int, int)  # file_path, downloaded, total, percentage
    download_speed = pyqtSignal(str, float)  # file_path, speed_mbps
    download_finished = pyqtSignal(str, str)  # file_path, final_path
    download_error = pyqtSignal(str, str)  # file_path, error_message
    all_downloads_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.active_downloads: Dict[str, DownloadThread] = {}
        self.download_queue: list = []
        self.max_concurrent_downloads = 3
        self.default_download_dir = os.path.expanduser("~/Downloads/Steam Workshop")
        
        # Создаем директорию по умолчанию
        os.makedirs(self.default_download_dir, exist_ok=True)
        
    def start_download(self, item_data: Dict[str, Any], download_dir: str) -> bool:
        """
        Начать загрузку элемента мастерской
        
        Args:
            item_data: Данные элемента мастерской
            download_dir: Директория для сохранения
            
        Returns:
            True если загрузка началась, False если ошибка
        """
        try:
            # Получаем URL для загрузки
            download_url = self._get_download_url(item_data)
            if not download_url:
                self.download_error.emit("", "Не удалось получить ссылку для загрузки")
                return False
                
            # Формируем имя файла
            filename = self._generate_filename(item_data)
            file_path = os.path.join(download_dir, filename)
            
            # Проверяем, не загружается ли уже этот файл
            if file_path in self.active_downloads:
                self.download_error.emit(file_path, "Файл уже загружается")
                return False
                
            # Проверяем количество активных загрузок
            if len(self.active_downloads) >= self.max_concurrent_downloads:
                # Добавляем в очередь
                self.download_queue.append((item_data, download_dir))
                return True
                
            # Начинаем загрузку
            return self._start_download_thread(item_data, download_url, file_path)
            
        except Exception as e:
            self.download_error.emit("", f"Ошибка запуска загрузки: {str(e)}")
            return False
            
    def _start_download_thread(self, item_data: Dict[str, Any], 
                             download_url: str, file_path: str) -> bool:
        """Запуск потока загрузки"""
        try:
            # Создаем поток загрузки
            download_thread = DownloadThread(download_url, file_path, item_data)
            
            # Подключаем сигналы
            download_thread.progress_updated.connect(
                lambda d, t, p: self.download_progress.emit(file_path, d, t, p)
            )
            download_thread.speed_updated.connect(
                lambda s: self.download_speed.emit(file_path, s)
            )
            download_thread.download_finished.connect(
                lambda fp: self._on_download_finished(file_path, fp)
            )
            download_thread.download_error.connect(
                lambda err: self._on_download_error(file_path, err)
            )
            
            # Добавляем в активные загрузки
            self.active_downloads[file_path] = download_thread
            
            # Запускаем поток
            download_thread.start()
            
            # Отправляем сигнал о начале загрузки
            self.download_started.emit(file_path, item_data)
            
            return True
            
        except Exception as e:
            self.download_error.emit(file_path, f"Ошибка создания потока: {str(e)}")
            return False
            
    def _on_download_finished(self, file_path: str, final_path: str):
        """Обработка завершения загрузки"""
        # Удаляем из активных загрузок
        if file_path in self.active_downloads:
            thread = self.active_downloads[file_path]
            thread.quit()
            thread.wait()
            del self.active_downloads[file_path]
            
        # Отправляем сигнал о завершении
        self.download_finished.emit(file_path, final_path)
        
        # Запускаем следующую загрузку из очереди
        self._start_next_download()
        
        # Проверяем, все ли загрузки завершены
        if not self.active_downloads and not self.download_queue:
            self.all_downloads_finished.emit()
            
    def _on_download_error(self, file_path: str, error_message: str):
        """Обработка ошибки загрузки"""
        # Удаляем из активных загрузок
        if file_path in self.active_downloads:
            thread = self.active_downloads[file_path]
            thread.quit()
            thread.wait()
            del self.active_downloads[file_path]
            
        # Отправляем сигнал об ошибке
        self.download_error.emit(file_path, error_message)
        
        # Запускаем следующую загрузку из очереди
        self._start_next_download()
        
    def _start_next_download(self):
        """Запуск следующей загрузки из очереди"""
        if self.download_queue and len(self.active_downloads) < self.max_concurrent_downloads:
            item_data, download_dir = self.download_queue.pop(0)
            self.start_download(item_data, download_dir)
            
    def _get_download_url(self, item_data: Dict[str, Any]) -> Optional[str]:
        """Получение URL для загрузки"""
        # Сначала пытаемся получить прямую ссылку
        if 'file_url' in item_data and item_data['file_url']:
            return item_data['file_url']
            
        # Если прямой ссылки нет, используем сторонний сервис
        published_file_id = item_data.get('publishedfileid')
        if published_file_id:
            # Используем steamworkshopdownloader.io или аналогичный сервис
            return f"https://steamworkshopdownloader.io/download/{published_file_id}"
            
        return None
        
    def _generate_filename(self, item_data: Dict[str, Any]) -> str:
        """Генерация имени файла"""
        # Получаем название элемента
        title = item_data.get('title', 'workshop_item')
        
        # Очищаем название от недопустимых символов
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Ограничиваем длину
        
        # Получаем ID файла
        file_id = item_data.get('publishedfileid', 'unknown')
        
        # Получаем расширение файла
        filename = item_data.get('filename', '')
        if filename and '.' in filename:
            extension = filename[filename.rfind('.'):]
        else:
            extension = '.zip'  # По умолчанию
            
        return f"{safe_title}_{file_id}{extension}"
        
    def cancel_download(self, file_path: str) -> bool:
        """Отмена загрузки"""
        if file_path in self.active_downloads:
            thread = self.active_downloads[file_path]
            thread.cancel()
            return True
        return False
        
    def cancel_all_downloads(self):
        """Отмена всех загрузок"""
        # Отменяем активные загрузки
        for thread in self.active_downloads.values():
            thread.cancel()
            
        # Очищаем очередь
        self.download_queue.clear()
        
    def get_download_stats(self) -> Dict[str, Any]:
        """Получение статистики загрузок"""
        return {
            'active_downloads': len(self.active_downloads),
            'queued_downloads': len(self.download_queue),
            'max_concurrent': self.max_concurrent_downloads,
            'default_dir': self.default_download_dir
        }
        
    def set_max_concurrent_downloads(self, max_downloads: int):
        """Установка максимального количества одновременных загрузок"""
        if max_downloads > 0:
            self.max_concurrent_downloads = max_downloads
            
            # Запускаем дополнительные загрузки если возможно
            while (len(self.active_downloads) < self.max_concurrent_downloads 
                   and self.download_queue):
                self._start_next_download()
                
    def pause_download(self, file_path: str) -> bool:
        """Приостановка загрузки (пока не реализовано)"""
        # TODO: Реализовать приостановку загрузки
        return False
        
    def resume_download(self, file_path: str) -> bool:
        """Возобновление загрузки (пока не реализовано)"""
        # TODO: Реализовать возобновление загрузки
        return False
        
    def get_active_downloads(self) -> list:
        """Получение списка активных загрузок"""
        return list(self.active_downloads.keys())
        
    def is_downloading(self, file_path: str) -> bool:
        """Проверка, загружается ли файл"""
        return file_path in self.active_downloads
        
    def clear_completed_downloads(self):
        """Очистка завершенных загрузок"""
        # Удаляем завершенные потоки
        completed_threads = []
        for file_path, thread in self.active_downloads.items():
            if thread.isFinished():
                completed_threads.append(file_path)
                
        for file_path in completed_threads:
            thread = self.active_downloads[file_path]
            thread.quit()
            thread.wait()
            del self.active_downloads[file_path]
