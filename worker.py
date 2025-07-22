#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Рабочие потоки
Фоновые потоки для загрузки данных без блокировки UI
"""

import time
import traceback
from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QThread, pyqtSignal

from steam_api import SteamAPI, SteamAPIError
from cache import Cache

class GameLoaderThread(QThread):
    """Поток для загрузки списка игр"""
    
    # Сигналы для связи с UI
    games_loaded = pyqtSignal(list)  # Список загруженных игр
    loading_progress = pyqtSignal(str)  # Прогресс загрузки
    loading_error = pyqtSignal(str)  # Ошибка загрузки
    
    def __init__(self, steam_api: SteamAPI, cache: Cache, parent=None):
        super().__init__(parent)
        self.steam_api = steam_api
        self.cache = cache
        self.is_cancelled = False
        
    def run(self):
        """Основная функция потока"""
        try:
            self.loading_progress.emit("Загрузка популярных игр...")
            
            # Проверяем кэш
            cache_key = "popular_games_list"
            cached_games = self.cache.get(cache_key)
            
            if cached_games and not self.is_cancelled:
                self.loading_progress.emit("Загрузка из кэша...")
                time.sleep(0.5)  # Небольшая задержка для демонстрации
                self.games_loaded.emit(cached_games)
                return
                
            # Загружаем из API
            if not self.is_cancelled:
                self.loading_progress.emit("Получение данных из Steam API...")
                
                # Загружаем первые 50 популярных игр
                games = self.steam_api.get_popular_games(limit=50)
                
                if not self.is_cancelled:
                    # Сохраняем в кэш на 1 час
                    self.cache.set(cache_key, games, ttl=3600)
                    
                    self.loading_progress.emit("Загрузка завершена")
                    self.games_loaded.emit(games)
                    
                    # Запускаем фоновую загрузку остальных игр
                    self._load_additional_games()
                    
        except SteamAPIError as e:
            if not self.is_cancelled:
                self.loading_error.emit(f"Ошибка Steam API: {str(e)}")
        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"Неожиданная ошибка: {str(e)}\n{traceback.format_exc()}"
                self.loading_error.emit(error_msg)
                
    def _load_additional_games(self):
        """Загрузка дополнительных игр в фоне"""
        try:
            if self.is_cancelled:
                return
                
            # Загружаем все доступные игры
            all_games = self.steam_api.get_popular_games(limit=200)
            
            if not self.is_cancelled and len(all_games) > 50:
                # Обновляем кэш с полным списком
                cache_key = "all_games_list"
                self.cache.set(cache_key, all_games, ttl=7200)  # 2 часа
                
                # Отправляем обновленный список
                self.games_loaded.emit(all_games)
                
        except Exception as e:
            print(f"Ошибка загрузки дополнительных игр: {e}")
            
    def cancel(self):
        """Отмена загрузки"""
        self.is_cancelled = True

class WorkshopLoaderThread(QThread):
    """Поток для загрузки элементов мастерской"""
    
    # Сигналы
    workshop_loaded = pyqtSignal(list)  # Список элементов мастерской
    loading_progress = pyqtSignal(str, int)  # Прогресс (сообщение, процент)
    loading_error = pyqtSignal(str)  # Ошибка загрузки
    item_loaded = pyqtSignal(dict)  # Отдельный элемент загружен
    
    def __init__(self, steam_api: SteamAPI, cache: Cache, app_id: int, 
                 page: int = 1, per_page: int = 50, parent=None):
        super().__init__(parent)
        self.steam_api = steam_api
        self.cache = cache
        self.app_id = app_id
        self.page = page
        self.per_page = per_page
        self.is_cancelled = False
        
    def run(self):
        """Основная функция потока"""
        try:
            self.loading_progress.emit("Поиск элементов мастерской...", 0)
            
            # Проверяем кэш
            cache_key = f"workshop_items_{self.app_id}_{self.page}_{self.per_page}"
            cached_items = self.cache.get(cache_key)
            
            if cached_items and not self.is_cancelled:
                self.loading_progress.emit("Загрузка из кэша...", 50)
                time.sleep(0.3)
                self.loading_progress.emit("Готово", 100)
                self.workshop_loaded.emit(cached_items)
                return
                
            # Загружаем из API
            if not self.is_cancelled:
                self.loading_progress.emit("Получение данных из Steam API...", 25)
                
                workshop_items = self.steam_api.get_workshop_items(
                    self.app_id, self.page, self.per_page
                )
                
                if not self.is_cancelled:
                    self.loading_progress.emit("Обработка данных...", 75)
                    
                    # Обрабатываем каждый элемент
                    processed_items = []
                    total_items = len(workshop_items)
                    
                    for i, item in enumerate(workshop_items):
                        if self.is_cancelled:
                            break
                            
                        # Дополнительная обработка элемента
                        processed_item = self._process_workshop_item(item)
                        processed_items.append(processed_item)
                        
                        # Отправляем отдельный элемент для немедленного отображения
                        self.item_loaded.emit(processed_item)
                        
                        # Обновляем прогресс
                        progress = 75 + (20 * (i + 1) // total_items)
                        self.loading_progress.emit(f"Обработано {i+1}/{total_items}", progress)
                        
                        # Небольшая пауза чтобы не блокировать UI
                        time.sleep(0.01)
                        
                    if not self.is_cancelled:
                        # Сохраняем в кэш на 30 минут
                        self.cache.set(cache_key, processed_items, ttl=1800)
                        
                        self.loading_progress.emit("Загрузка завершена", 100)
                        self.workshop_loaded.emit(processed_items)
                        
        except SteamAPIError as e:
            if not self.is_cancelled:
                self.loading_error.emit(f"Ошибка Steam API: {str(e)}")
        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"Неожиданная ошибка: {str(e)}\n{traceback.format_exc()}"
                self.loading_error.emit(error_msg)
                
    def _process_workshop_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Дополнительная обработка элемента мастерской"""
        try:
            # Добавляем дополнительные поля
            processed_item = item.copy()
            
            # Форматируем размер файла
            file_size = item.get('file_size', 0)
            if file_size > 0:
                if file_size >= 1024 * 1024 * 1024:  # GB
                    processed_item['file_size_formatted'] = f"{file_size / (1024**3):.1f} GB"
                elif file_size >= 1024 * 1024:  # MB
                    processed_item['file_size_formatted'] = f"{file_size / (1024**2):.1f} MB"
                elif file_size >= 1024:  # KB
                    processed_item['file_size_formatted'] = f"{file_size / 1024:.1f} KB"
                else:
                    processed_item['file_size_formatted'] = f"{file_size} B"
            else:
                processed_item['file_size_formatted'] = "Неизвестно"
                
            # Форматируем дату создания
            time_created = item.get('time_created', 0)
            if time_created > 0:
                import datetime
                dt = datetime.datetime.fromtimestamp(time_created)
                processed_item['created_date'] = dt.strftime("%d.%m.%Y")
                processed_item['created_time'] = dt.strftime("%H:%M")
            else:
                processed_item['created_date'] = "Неизвестно"
                processed_item['created_time'] = ""
                
            # Форматируем количество подписчиков
            subscriptions = item.get('subscriptions', 0)
            if subscriptions >= 1000000:
                processed_item['subscriptions_formatted'] = f"{subscriptions / 1000000:.1f}M"
            elif subscriptions >= 1000:
                processed_item['subscriptions_formatted'] = f"{subscriptions / 1000:.1f}K"
            else:
                processed_item['subscriptions_formatted'] = str(subscriptions)
                
            return processed_item
            
        except Exception as e:
            print(f"Ошибка обработки элемента мастерской: {e}")
            return item
            
    def cancel(self):
        """Отмена загрузки"""
        self.is_cancelled = True

class SearchThread(QThread):
    """Поток для поиска игр"""
    
    # Сигналы
    search_results = pyqtSignal(list)  # Результаты поиска
    search_error = pyqtSignal(str)  # Ошибка поиска
    
    def __init__(self, steam_api: SteamAPI, cache: Cache, query: str, parent=None):
        super().__init__(parent)
        self.steam_api = steam_api
        self.cache = cache
        self.query = query
        self.is_cancelled = False
        
    def run(self):
        """Основная функция потока"""
        try:
            if len(self.query.strip()) < 2:
                self.search_results.emit([])
                return
                
            # Проверяем кэш
            cache_key = f"search_games_{self.query.lower()}"
            cached_results = self.cache.get(cache_key)
            
            if cached_results and not self.is_cancelled:
                self.search_results.emit(cached_results)
                return
                
            # Выполняем поиск
            if not self.is_cancelled:
                results = self.steam_api.search_games(self.query, limit=20)
                
                if not self.is_cancelled:
                    # Сохраняем в кэш на 15 минут
                    self.cache.set(cache_key, results, ttl=900)
                    self.search_results.emit(results)
                    
        except SteamAPIError as e:
            if not self.is_cancelled:
                self.search_error.emit(f"Ошибка поиска: {str(e)}")
        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"Ошибка поиска: {str(e)}"
                self.search_error.emit(error_msg)
                
    def cancel(self):
        """Отмена поиска"""
        self.is_cancelled = True

class LazyGameLoaderThread(QThread):
    """Поток для ленивой загрузки дополнительных игр"""
    
    # Сигналы
    additional_games_loaded = pyqtSignal(list)  # Дополнительные игры
    loading_progress = pyqtSignal(str)  # Прогресс загрузки
    
    def __init__(self, steam_api: SteamAPI, cache: Cache, 
                 start_index: int = 50, batch_size: int = 25, parent=None):
        super().__init__(parent)
        self.steam_api = steam_api
        self.cache = cache
        self.start_index = start_index
        self.batch_size = batch_size
        self.is_cancelled = False
        
    def run(self):
        """Основная функция потока"""
        try:
            # Небольшая задержка перед началом фоновой загрузки
            time.sleep(2)
            
            if self.is_cancelled:
                return
                
            self.loading_progress.emit("Загрузка дополнительных игр...")
            
            # Получаем полный список игр
            all_games = self.steam_api.get_popular_games(limit=200)
            
            if not self.is_cancelled and len(all_games) > self.start_index:
                # Берем дополнительные игры батчами
                additional_games = all_games[self.start_index:]
                
                # Отправляем батчами для плавного обновления UI
                for i in range(0, len(additional_games), self.batch_size):
                    if self.is_cancelled:
                        break
                        
                    batch = additional_games[i:i + self.batch_size]
                    self.additional_games_loaded.emit(batch)
                    
                    # Пауза между батчами
                    time.sleep(0.5)
                    
                self.loading_progress.emit("Фоновая загрузка завершена")
                
        except Exception as e:
            print(f"Ошибка ленивой загрузки игр: {e}")
            
    def cancel(self):
        """Отмена загрузки"""
        self.is_cancelled = True
