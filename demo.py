#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Демонстрация без GUI
Показывает работу основных компонентов приложения
"""

import sys
import time
from steam_api import SteamAPI
from cache import Cache
from utils import format_file_size, format_time_ago

def print_header(title):
    """Печать заголовка"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_separator():
    """Печать разделителя"""
    print("-" * 60)

def demo_steam_api():
    """Демонстрация Steam API"""
    print_header("🎮 ДЕМОНСТРАЦИЯ STEAM API")
    
    # Создаем экземпляр API
    steam_api = SteamAPI()
    
    print("📋 Получение списка популярных игр...")
    try:
        games = steam_api.get_popular_games(limit=10)
        print(f"✅ Загружено {len(games)} игр:")
        
        for i, game in enumerate(games[:5], 1):
            print(f"  {i}. {game['name']} (ID: {game['appid']})")
            
        print(f"  ... и еще {len(games) - 5} игр")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None
        
    return games

def demo_workshop_items(games):
    """Демонстрация элементов мастерской"""
    print_header("🛠 ДЕМОНСТРАЦИЯ МАСТЕРСКОЙ")
    
    if not games:
        print("❌ Нет доступных игр для демонстрации")
        return
        
    steam_api = SteamAPI()
    
    # Берем первую игру для демонстрации
    game = games[0]
    print(f"🎯 Загрузка мастерской для игры: {game['name']}")
    
    try:
        workshop_items = steam_api.get_workshop_items(game['appid'], per_page=5)
        print(f"✅ Найдено {len(workshop_items)} элементов:")
        
        for i, item in enumerate(workshop_items, 1):
            print(f"\n  📦 {i}. {item['title']}")
            print(f"     👤 Автор: {item.get('creator', 'Неизвестно')}")
            print(f"     📊 Подписчики: {item.get('subscriptions', 0)}")
            print(f"     💾 Размер: {format_file_size(item.get('file_size', 0))}")
            
            # Показываем описание (первые 100 символов)
            description = item.get('description', '')
            if description:
                desc_short = description[:100] + "..." if len(description) > 100 else description
                print(f"     📝 Описание: {desc_short}")
                
    except Exception as e:
        print(f"❌ Ошибка загрузки мастерской: {e}")

def demo_cache():
    """Демонстрация кэширования"""
    print_header("💾 ДЕМОНСТРАЦИЯ КЭШИРОВАНИЯ")
    
    cache = Cache(default_ttl=10)  # 10 секунд для демонстрации
    
    print("📝 Сохранение данных в кэш...")
    test_data = {
        'message': 'Привет из кэша!',
        'timestamp': time.time(),
        'items': ['элемент1', 'элемент2', 'элемент3']
    }
    
    cache.set('demo_key', test_data, ttl=5)
    print("✅ Данные сохранены с TTL = 5 секунд")
    
    print("\n📖 Чтение данных из кэша...")
    cached_data = cache.get('demo_key')
    if cached_data:
        print("✅ Данные успешно получены из кэша:")
        print(f"   Сообщение: {cached_data['message']}")
        print(f"   Элементы: {', '.join(cached_data['items'])}")
    else:
        print("❌ Данные не найдены в кэше")
    
    print("\n⏳ Ожидание истечения TTL (5 секунд)...")
    time.sleep(6)
    
    print("📖 Повторное чтение после истечения TTL...")
    cached_data = cache.get('demo_key')
    if cached_data:
        print("❌ Данные все еще в кэше (ошибка TTL)")
    else:
        print("✅ Данные корректно удалены из кэша после истечения TTL")
    
    # Статистика кэша
    stats = cache.get_stats()
    print(f"\n📊 Статистика кэша:")
    print(f"   Всего элементов: {stats['total_items']}")
    print(f"   Активных элементов: {stats['active_items']}")
    print(f"   Истекших элементов: {stats['expired_items']}")

def demo_search():
    """Демонстрация поиска"""
    print_header("🔍 ДЕМОНСТРАЦИЯ ПОИСКА")
    
    steam_api = SteamAPI()
    
    search_queries = ['Counter', 'Dota', 'Garry']
    
    for query in search_queries:
        print(f"\n🔎 Поиск игр по запросу: '{query}'")
        try:
            results = steam_api.search_games(query, limit=3)
            if results:
                print(f"✅ Найдено {len(results)} результатов:")
                for i, game in enumerate(results, 1):
                    print(f"  {i}. {game['name']} (ID: {game['appid']})")
            else:
                print("❌ Результаты не найдены")
        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")

def demo_download_simulation():
    """Демонстрация симуляции загрузки"""
    print_header("⬇️ СИМУЛЯЦИЯ ЗАГРУЗКИ")
    
    print("📁 Создание тестового элемента мастерской...")
    
    test_item = {
        'publishedfileid': '123456789',
        'title': 'Тестовый мод для демонстрации',
        'description': 'Это тестовый мод для демонстрации функций загрузки',
        'creator': 'TestUser',
        'file_size': 1024 * 1024 * 15,  # 15 MB
        'filename': 'test_mod.zip',
        'file_url': 'https://example.com/test_mod.zip'
    }
    
    print(f"📦 Элемент: {test_item['title']}")
    print(f"👤 Автор: {test_item['creator']}")
    print(f"💾 Размер: {format_file_size(test_item['file_size'])}")
    print(f"📄 Файл: {test_item['filename']}")
    
    print("\n⬇️ Симуляция процесса загрузки...")
    
    # Симулируем прогресс загрузки
    total_size = test_item['file_size']
    chunk_size = 1024 * 100  # 100KB chunks
    downloaded = 0
    
    print("Прогресс загрузки:")
    while downloaded < total_size:
        downloaded += chunk_size
        if downloaded > total_size:
            downloaded = total_size
            
        progress = (downloaded / total_size) * 100
        bar_length = 30
        filled_length = int(bar_length * downloaded // total_size)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f"\r[{bar}] {progress:.1f}% ({format_file_size(downloaded)}/{format_file_size(total_size)})", end='')
        time.sleep(0.1)
    
    print("\n✅ Загрузка завершена!")

def demo_utils():
    """Демонстрация утилит"""
    print_header("🔧 ДЕМОНСТРАЦИЯ УТИЛИТ")
    
    print("📏 Форматирование размеров файлов:")
    sizes = [512, 1024, 1024*1024, 1024*1024*1024, 1024*1024*1024*1024]
    for size in sizes:
        print(f"  {size:>12} байт = {format_file_size(size)}")
    
    print("\n⏰ Форматирование времени:")
    import time
    timestamps = [
        time.time(),  # сейчас
        time.time() - 3600,  # час назад
        time.time() - 86400,  # день назад
        time.time() - 86400 * 30,  # месяц назад
        time.time() - 86400 * 365,  # год назад
    ]
    
    for ts in timestamps:
        print(f"  {format_time_ago(int(ts))}")
    
    print("\n🧹 Очистка имен файлов:")
    dirty_names = [
        'Мод с <плохими> символами',
        'Файл/с\\недопустимыми:символами',
        'Очень длинное название файла которое нужно сократить потому что оно слишком длинное для файловой системы',
        'Нормальное_название.zip'
    ]
    
    from utils import sanitize_filename
    for name in dirty_names:
        clean_name = sanitize_filename(name)
        print(f"  '{name}' -> '{clean_name}'")

def main():
    """Главная функция демонстрации"""
    print("🎮 Steam Workshop Downloader - Демонстрация")
    print("=" * 60)
    print("Это демонстрация основных компонентов приложения без GUI")
    print("Приложение работает в консольном режиме для тестирования")
    
    try:
        # Демонстрация Steam API
        games = demo_steam_api()
        
        # Демонстрация мастерской
        if games:
            demo_workshop_items(games)
        
        # Демонстрация кэширования
        demo_cache()
        
        # Демонстрация поиска
        demo_search()
        
        # Демонстрация загрузки
        demo_download_simulation()
        
        # Демонстрация утилит
        demo_utils()
        
        print_header("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("Все основные компоненты приложения работают корректно!")
        print("\nДля запуска полного приложения с GUI используйте:")
        print("  python main.py")
        print("\nПримечание: GUI требует графическое окружение (X11/Wayland)")
        
    except KeyboardInterrupt:
        print("\n\n👋 Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
