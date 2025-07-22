#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Модуль кэширования
Кэширование данных с TTL и автообновлением
"""

import time
import threading
import json
import os
import pickle
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta

class Cache:
    """Класс для кэширования данных с TTL"""
    
    def __init__(self, default_ttl: int = 3600, cache_dir: str = "cache"):
        """
        Инициализация кэша
        
        Args:
            default_ttl: Время жизни кэша по умолчанию в секундах (1 час)
            cache_dir: Директория для сохранения кэша на диск
        """
        self.default_ttl = default_ttl
        self.cache_dir = cache_dir
        self._memory_cache: Dict[str, Tuple[Any, float, int]] = {}
        self._lock = threading.RLock()
        
        # Создаем директорию для кэша если её нет
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # Загружаем кэш с диска
        self._load_from_disk()
        
        # Запускаем фоновую очистку устаревших записей
        self._start_cleanup_timer()
        
    def get(self, key: str) -> Optional[Any]:
        """
        Получение данных из кэша
        
        Args:
            key: Ключ для поиска
            
        Returns:
            Данные из кэша или None если данных нет или они устарели
        """
        with self._lock:
            if key not in self._memory_cache:
                return None
                
            data, timestamp, ttl = self._memory_cache[key]
            
            # Проверяем не истекло ли время жизни
            if time.time() - timestamp > ttl:
                del self._memory_cache[key]
                self._remove_from_disk(key)
                return None
                
            return data
            
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        Сохранение данных в кэш
        
        Args:
            key: Ключ для сохранения
            data: Данные для сохранения
            ttl: Время жизни в секундах (если None, используется default_ttl)
        """
        if ttl is None:
            ttl = self.default_ttl
            
        with self._lock:
            timestamp = time.time()
            self._memory_cache[key] = (data, timestamp, ttl)
            
            # Сохраняем на диск для персистентности
            self._save_to_disk(key, data, timestamp, ttl)
            
    def delete(self, key: str) -> bool:
        """
        Удаление данных из кэша
        
        Args:
            key: Ключ для удаления
            
        Returns:
            True если данные были удалены, False если ключ не найден
        """
        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                self._remove_from_disk(key)
                return True
            return False
            
    def clear(self) -> None:
        """Очистка всего кэша"""
        with self._lock:
            self._memory_cache.clear()
            
            # Очищаем директорию кэша
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    try:
                        os.remove(os.path.join(self.cache_dir, filename))
                    except OSError:
                        pass
                        
    def has_key(self, key: str) -> bool:
        """
        Проверка наличия ключа в кэше
        
        Args:
            key: Ключ для проверки
            
        Returns:
            True если ключ существует и не истек, False иначе
        """
        return self.get(key) is not None
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики кэша
        
        Returns:
            Словарь со статистикой
        """
        with self._lock:
            total_items = len(self._memory_cache)
            expired_items = 0
            current_time = time.time()
            
            for key, (data, timestamp, ttl) in self._memory_cache.items():
                if current_time - timestamp > ttl:
                    expired_items += 1
                    
            return {
                'total_items': total_items,
                'active_items': total_items - expired_items,
                'expired_items': expired_items,
                'cache_dir': self.cache_dir,
                'default_ttl': self.default_ttl
            }
            
    def cleanup_expired(self) -> int:
        """
        Очистка истекших записей
        
        Returns:
            Количество удаленных записей
        """
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, (data, timestamp, ttl) in self._memory_cache.items():
                if current_time - timestamp > ttl:
                    expired_keys.append(key)
                    
            for key in expired_keys:
                del self._memory_cache[key]
                self._remove_from_disk(key)
                
            return len(expired_keys)
            
    def _save_to_disk(self, key: str, data: Any, timestamp: float, ttl: int) -> None:
        """Сохранение данных на диск"""
        try:
            cache_data = {
                'data': data,
                'timestamp': timestamp,
                'ttl': ttl
            }
            
            filename = self._get_cache_filename(key)
            filepath = os.path.join(self.cache_dir, filename)
            
            with open(filepath, 'wb') as f:
                pickle.dump(cache_data, f)
                
        except Exception as e:
            print(f"Ошибка сохранения кэша на диск: {e}")
            
    def _load_from_disk(self) -> None:
        """Загрузка кэша с диска"""
        try:
            if not os.path.exists(self.cache_dir):
                return
                
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.cache'):
                    continue
                    
                filepath = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(filepath, 'rb') as f:
                        cache_data = pickle.load(f)
                        
                    key = self._get_key_from_filename(filename)
                    data = cache_data['data']
                    timestamp = cache_data['timestamp']
                    ttl = cache_data['ttl']
                    
                    # Проверяем не истекли ли данные
                    if time.time() - timestamp <= ttl:
                        self._memory_cache[key] = (data, timestamp, ttl)
                    else:
                        # Удаляем истекший файл
                        os.remove(filepath)
                        
                except Exception as e:
                    print(f"Ошибка загрузки кэша из файла {filename}: {e}")
                    # Удаляем поврежденный файл
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass
                        
        except Exception as e:
            print(f"Ошибка загрузки кэша с диска: {e}")
            
    def _remove_from_disk(self, key: str) -> None:
        """Удаление файла кэша с диска"""
        try:
            filename = self._get_cache_filename(key)
            filepath = os.path.join(self.cache_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                
        except Exception as e:
            print(f"Ошибка удаления кэша с диска: {e}")
            
    def _get_cache_filename(self, key: str) -> str:
        """Получение имени файла для ключа кэша"""
        # Заменяем небезопасные символы
        safe_key = key.replace('/', '_').replace('\\', '_').replace(':', '_')
        return f"{safe_key}.cache"
        
    def _get_key_from_filename(self, filename: str) -> str:
        """Получение ключа из имени файла"""
        return filename.replace('.cache', '').replace('_', '/')
        
    def _start_cleanup_timer(self) -> None:
        """Запуск таймера для периодической очистки"""
        def cleanup_worker():
            while True:
                time.sleep(300)  # Очистка каждые 5 минут
                try:
                    cleaned = self.cleanup_expired()
                    if cleaned > 0:
                        print(f"Очищено {cleaned} истекших записей кэша")
                except Exception as e:
                    print(f"Ошибка при очистке кэша: {e}")
                    
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        
    def get_or_set(self, key: str, factory_func, ttl: Optional[int] = None) -> Any:
        """
        Получение данных из кэша или создание новых с помощью функции
        
        Args:
            key: Ключ кэша
            factory_func: Функция для создания данных если их нет в кэше
            ttl: Время жизни кэша
            
        Returns:
            Данные из кэша или созданные функцией
        """
        # Сначала пытаемся получить из кэша
        cached_data = self.get(key)
        if cached_data is not None:
            return cached_data
            
        # Если данных нет, создаем новые
        try:
            new_data = factory_func()
            self.set(key, new_data, ttl)
            return new_data
        except Exception as e:
            print(f"Ошибка создания данных для кэша: {e}")
            raise
            
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Удаление всех ключей, соответствующих паттерну
        
        Args:
            pattern: Паттерн для поиска (простое совпадение подстроки)
            
        Returns:
            Количество удаленных ключей
        """
        with self._lock:
            keys_to_delete = []
            
            for key in self._memory_cache.keys():
                if pattern in key:
                    keys_to_delete.append(key)
                    
            for key in keys_to_delete:
                self.delete(key)
                
            return len(keys_to_delete)
            
    def refresh_key(self, key: str, factory_func, ttl: Optional[int] = None) -> Any:
        """
        Принудительное обновление данных в кэше
        
        Args:
            key: Ключ кэша
            factory_func: Функция для создания новых данных
            ttl: Время жизни кэша
            
        Returns:
            Новые данные
        """
        try:
            new_data = factory_func()
            self.set(key, new_data, ttl)
            return new_data
        except Exception as e:
            print(f"Ошибка обновления данных кэша: {e}")
            raise
            
    def get_cache_size(self) -> Dict[str, int]:
        """
        Получение размера кэша
        
        Returns:
            Словарь с информацией о размере
        """
        memory_size = 0
        disk_size = 0
        
        # Подсчет размера в памяти (приблизительно)
        with self._lock:
            memory_size = len(self._memory_cache)
            
        # Подсчет размера на диске
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    filepath = os.path.join(self.cache_dir, filename)
                    disk_size += os.path.getsize(filepath)
        except Exception:
            pass
            
        return {
            'memory_items': memory_size,
            'disk_size_bytes': disk_size,
            'disk_size_mb': round(disk_size / (1024 * 1024), 2)
        }

# Глобальный экземпляр кэша для использования в приложении
app_cache = Cache(default_ttl=3600)  # 1 час по умолчанию
