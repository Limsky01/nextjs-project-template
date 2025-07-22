#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Утилиты
Вспомогательные функции для приложения
"""

import os
import sys
import time
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

# Настройка логирования
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Настройка системы логирования"""
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем корневой логгер
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик (если указан файл)
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Не удалось создать файл логов: {e}")
    
    return logger

# Форматирование размеров файлов
def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла в читаемый вид"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

# Форматирование времени
def format_time_ago(timestamp: int) -> str:
    """Форматирование времени 'назад'"""
    try:
        now = datetime.now()
        dt = datetime.fromtimestamp(timestamp)
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} {'год' if years == 1 else 'лет'} назад"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} {'месяц' if months == 1 else 'месяцев'} назад"
        elif diff.days > 0:
            return f"{diff.days} {'день' if diff.days == 1 else 'дней'} назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} {'час' if hours == 1 else 'часов'} назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} {'минуту' if minutes == 1 else 'минут'} назад"
        else:
            return "только что"
            
    except Exception:
        return "неизвестно"

# Форматирование даты
def format_date(timestamp: int, format_str: str = "%d.%m.%Y") -> str:
    """Форматирование даты"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime(format_str)
    except Exception:
        return "неизвестно"

# Очистка имени файла
def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """Очистка имени файла от недопустимых символов"""
    # Недопустимые символы для имен файлов
    invalid_chars = '<>:"/\\|?*'
    
    # Заменяем недопустимые символы
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Убираем лишние пробелы и точки
    filename = filename.strip(' .')
    
    # Ограничиваем длину
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename

# Создание хэша строки
def create_hash(text: str, algorithm: str = "md5") -> str:
    """Создание хэша строки"""
    try:
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(text.encode('utf-8'))
        return hash_obj.hexdigest()
    except Exception:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

# Проверка доступности URL
def is_url_accessible(url: str, timeout: int = 5) -> bool:
    """Проверка доступности URL"""
    try:
        import requests
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False

# Получение информации о системе
def get_system_info() -> Dict[str, Any]:
    """Получение информации о системе"""
    import platform
    
    try:
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'memory_total': memory.total,
            'memory_available': memory.available,
            'disk_total': disk.total,
            'disk_free': disk.free
        }
    except ImportError:
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'memory_total': 0,
            'memory_available': 0,
            'disk_total': 0,
            'disk_free': 0
        }
    
    return system_info

# Создание резервной копии файла
def backup_file(file_path: str, backup_dir: str = "backups") -> Optional[str]:
    """Создание резервной копии файла"""
    try:
        if not os.path.exists(file_path):
            return None
            
        # Создаем директорию для бэкапов
        os.makedirs(backup_dir, exist_ok=True)
        
        # Генерируем имя бэкапа
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{timestamp}_{filename}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Копируем файл
        import shutil
        shutil.copy2(file_path, backup_path)
        
        return backup_path
        
    except Exception as e:
        print(f"Ошибка создания бэкапа: {e}")
        return None

# Очистка старых файлов
def cleanup_old_files(directory: str, max_age_days: int = 7, pattern: str = "*") -> int:
    """Очистка старых файлов в директории"""
    try:
        import glob
        
        if not os.path.exists(directory):
            return 0
            
        pattern_path = os.path.join(directory, pattern)
        files = glob.glob(pattern_path)
        
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        removed_count = 0
        
        for file_path in files:
            try:
                if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    removed_count += 1
            except OSError:
                continue
                
        return removed_count
        
    except Exception as e:
        print(f"Ошибка очистки файлов: {e}")
        return 0

# Проверка свободного места на диске
def check_disk_space(path: str, required_bytes: int) -> bool:
    """Проверка наличия свободного места на диске"""
    try:
        import shutil
        free_bytes = shutil.disk_usage(path).free
        return free_bytes >= required_bytes
    except Exception:
        return True  # Если не можем проверить, считаем что места достаточно

# Безопасное создание директории
def safe_makedirs(path: str, mode: int = 0o755) -> bool:
    """Безопасное создание директории"""
    try:
        os.makedirs(path, mode=mode, exist_ok=True)
        return True
    except Exception as e:
        print(f"Ошибка создания директории {path}: {e}")
        return False

# Получение размера директории
def get_directory_size(path: str) -> int:
    """Получение размера директории в байтах"""
    total_size = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    continue
    except Exception:
        pass
        
    return total_size

# Валидация URL
def is_valid_url(url: str) -> bool:
    """Проверка валидности URL"""
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

# Получение расширения файла из URL
def get_file_extension_from_url(url: str) -> str:
    """Получение расширения файла из URL"""
    try:
        from urllib.parse import urlparse, unquote
        parsed = urlparse(url)
        path = unquote(parsed.path)
        
        if '.' in path:
            return os.path.splitext(path)[1].lower()
        else:
            return '.zip'  # По умолчанию
    except Exception:
        return '.zip'

# Форматирование скорости загрузки
def format_download_speed(bytes_per_second: float) -> str:
    """Форматирование скорости загрузки"""
    if bytes_per_second < 1024:
        return f"{bytes_per_second:.1f} B/s"
    elif bytes_per_second < 1024 * 1024:
        return f"{bytes_per_second / 1024:.1f} KB/s"
    else:
        return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"

# Оценка времени загрузки
def estimate_download_time(total_bytes: int, bytes_per_second: float) -> str:
    """Оценка времени загрузки"""
    if bytes_per_second <= 0:
        return "неизвестно"
        
    try:
        seconds_remaining = (total_bytes) / bytes_per_second
        
        if seconds_remaining < 60:
            return f"{int(seconds_remaining)} сек"
        elif seconds_remaining < 3600:
            minutes = int(seconds_remaining / 60)
            return f"{minutes} мин"
        else:
            hours = int(seconds_remaining / 3600)
            minutes = int((seconds_remaining % 3600) / 60)
            return f"{hours}ч {minutes}м"
            
    except Exception:
        return "неизвестно"

# Проверка версии приложения
def check_app_version() -> Dict[str, str]:
    """Получение информации о версии приложения"""
    return {
        'version': '1.0.0',
        'build_date': '2024-01-01',
        'python_version': sys.version.split()[0],
        'platform': sys.platform
    }

# Создание конфигурационного файла
def create_default_config() -> Dict[str, Any]:
    """Создание конфигурации по умолчанию"""
    return {
        'app': {
            'theme': 'dark',
            'language': 'ru',
            'auto_update': True,
            'check_updates_on_start': True
        },
        'downloads': {
            'default_directory': os.path.expanduser("~/Downloads/Steam Workshop"),
            'max_concurrent_downloads': 3,
            'chunk_size': 8192,
            'timeout': 30
        },
        'cache': {
            'ttl_games': 3600,  # 1 час
            'ttl_workshop': 1800,  # 30 минут
            'ttl_images': 86400,  # 24 часа
            'max_cache_size_mb': 500
        },
        'ui': {
            'window_width': 1200,
            'window_height': 800,
            'remember_window_size': True,
            'show_splash_screen': True
        }
    }

# Логгер для приложения
app_logger = setup_logging("INFO", "logs/app.log")
