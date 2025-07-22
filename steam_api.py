#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Workshop Downloader - Steam API модуль
Работа с Steam Web API для получения данных игр и мастерской
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any

class SteamAPIError(Exception):
    """Исключение для ошибок Steam API"""
    pass

class SteamAPI:
    """Класс для работы с Steam Web API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Steam Workshop Downloader/1.0'
        })
        
        # Популярные игры с мастерской (для демонстрации)
        self.popular_games = [
            {'appid': 730, 'name': 'Counter-Strike: Global Offensive'},
            {'appid': 570, 'name': 'Dota 2'},
            {'appid': 440, 'name': 'Team Fortress 2'},
            {'appid': 4000, 'name': "Garry's Mod"},
            {'appid': 252490, 'name': 'Rust'},
            {'appid': 304930, 'name': 'Unturned'},
            {'appid': 431960, 'name': 'Wallpaper Engine'},
            {'appid': 294100, 'name': 'RimWorld'},
            {'appid': 255710, 'name': 'Cities: Skylines'},
            {'appid': 108600, 'name': 'Project Zomboid'},
            {'appid': 211820, 'name': 'Starbound'},
            {'appid': 105600, 'name': 'Terraria'},
            {'appid': 72850, 'name': 'The Elder Scrolls V: Skyrim'},
            {'appid': 489830, 'name': 'The Elder Scrolls V: Skyrim Special Edition'},
            {'appid': 1085660, 'name': 'Destiny 2'},
            {'appid': 271590, 'name': 'Grand Theft Auto V'},
            {'appid': 346110, 'name': 'ARK: Survival Evolved'},
            {'appid': 322330, 'name': 'Don\'t Starve Together'},
            {'appid': 230410, 'name': 'Warframe'},
            {'appid': 582010, 'name': 'Monster Hunter: World'},
            {'appid': 1172470, 'name': 'Apex Legends'},
            {'appid': 359550, 'name': 'Tom Clancy\'s Rainbow Six Siege'},
            {'appid': 292030, 'name': 'The Witcher 3: Wild Hunt'},
            {'appid': 1174180, 'name': 'Red Dead Redemption 2'},
            {'appid': 413150, 'name': 'Stardew Valley'},
            {'appid': 367520, 'name': 'Hollow Knight'},
            {'appid': 381210, 'name': 'Dead by Daylight'},
            {'appid': 236430, 'name': 'A Hat in Time'},
            {'appid': 418370, 'name': 'Subnautica'},
            {'appid': 774281, 'name': 'Subnautica: Below Zero'},
            {'appid': 892970, 'name': 'Valheim'},
            {'appid': 945360, 'name': 'Among Us'},
            {'appid': 1203220, 'name': 'NARAKA: BLADEPOINT'},
            {'appid': 1172620, 'name': 'Sea of Thieves'},
            {'appid': 1091500, 'name': 'Cyberpunk 2077'},
            {'appid': 1245620, 'name': 'ELDEN RING'},
            {'appid': 1086940, 'name': 'Baldur\'s Gate 3'},
            {'appid': 1517290, 'name': 'Battlefield 2042'},
            {'appid': 1599340, 'name': 'Call of Duty: Modern Warfare II'},
            {'appid': 1938090, 'name': 'Call of Duty: Modern Warfare III'},
            {'appid': 1966720, 'name': 'Hogwarts Legacy'},
            {'appid': 1817070, 'name': 'Marvel\'s Spider-Man Remastered'},
            {'appid': 1888930, 'name': 'Marvel\'s Spider-Man: Miles Morales'},
            {'appid': 1623730, 'name': 'Palworld'},
            {'appid': 1868140, 'name': 'DAVE THE DIVER'},
            {'appid': 1449850, 'name': 'Yu-Gi-Oh! Master Duel'},
            {'appid': 1593500, 'name': 'God of War'},
            {'appid': 1817190, 'name': 'Marvel\'s Guardians of the Galaxy'},
            {'appid': 1237970, 'name': 'Titanfall 2'},
            {'appid': 1174370, 'name': 'Phasmophobia'}
        ]
        
    def set_api_key(self, api_key: str):
        """Установка API ключа Steam"""
        self.api_key = api_key
        
    def get_popular_games(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение списка популярных игр с мастерской"""
        try:
            # Возвращаем первые N игр из предустановленного списка
            return self.popular_games[:limit]
        except Exception as e:
            raise SteamAPIError(f"Ошибка получения списка игр: {str(e)}")
            
    def search_games(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Поиск игр по названию"""
        try:
            # Простой поиск по предустановленному списку
            query_lower = query.lower()
            results = []
            
            for game in self.popular_games:
                if query_lower in game['name'].lower():
                    results.append(game)
                    if len(results) >= limit:
                        break
                        
            return results
        except Exception as e:
            raise SteamAPIError(f"Ошибка поиска игр: {str(e)}")
            
    def get_workshop_items(self, app_id: int, page: int = 1, per_page: int = 50) -> List[Dict[str, Any]]:
        """Получение элементов мастерской для игры"""
        try:
            # Используем Steam Web API для получения элементов мастерской
            url = f"{self.base_url}/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
            
            # Для демонстрации создаем тестовые данные
            # В реальном приложении здесь будет запрос к API
            workshop_items = self._generate_demo_workshop_items(app_id, per_page)
            
            return workshop_items
            
        except Exception as e:
            raise SteamAPIError(f"Ошибка получения элементов мастерской: {str(e)}")
            
    def _generate_demo_workshop_items(self, app_id: int, count: int) -> List[Dict[str, Any]]:
        """Генерация демонстрационных элементов мастерской"""
        items = []
        
        # Получаем название игры
        game_name = "Unknown Game"
        for game in self.popular_games:
            if game['appid'] == app_id:
                game_name = game['name']
                break
                
        # Типы модов в зависимости от игры
        mod_types = {
            730: ['Карты', 'Скины оружия', 'Наклейки', 'Граффити'],  # CS:GO
            570: ['Предметы героев', 'Курьеры', 'Варды', 'Эффекты'],  # Dota 2
            440: ['Шляпы', 'Оружие', 'Карты', 'Тауны'],  # TF2
            4000: ['Аддоны', 'Карты', 'Модели', 'Эффекты'],  # Garry's Mod
            252490: ['Скины', 'Плагины', 'Карты'],  # Rust
            431960: ['Обои', 'Интерактивные обои', 'Видео обои'],  # Wallpaper Engine
            255710: ['Здания', 'Карты', 'Моды транспорта', 'Декорации'],  # Cities: Skylines
        }
        
        current_mod_types = mod_types.get(app_id, ['Мод', 'Карта', 'Скин', 'Аддон'])
        
        for i in range(count):
            mod_type = current_mod_types[i % len(current_mod_types)]
            
            item = {
                'publishedfileid': f"{app_id}{1000000 + i}",
                'title': f"{mod_type} для {game_name} #{i+1}",
                'description': f"Отличный {mod_type.lower()} для игры {game_name}. "
                              f"Добавляет новые возможности и улучшает игровой процесс. "
                              f"Совместим с последней версией игры.",
                'creator': f"Модер_{i+1}",
                'time_created': int(time.time()) - (i * 86400),  # Разные даты
                'time_updated': int(time.time()) - (i * 3600),
                'visibility': 0,  # Публичный
                'banned': 0,
                'ban_reason': '',
                'subscriptions': 1000 + (i * 100),
                'favorited': 50 + (i * 10),
                'lifetime_subscriptions': 2000 + (i * 200),
                'lifetime_favorited': 100 + (i * 20),
                'views': 5000 + (i * 500),
                'tags': [
                    {'tag': mod_type.lower()},
                    {'tag': 'популярное'},
                    {'tag': 'новое'}
                ],
                'preview_url': f"https://steamuserimages-a.akamaihd.net/ugc/demo_{app_id}_{i}.jpg",
                'file_url': f"https://steamworkshopdownloader.io/download/{app_id}{1000000 + i}",
                'file_size': 1024 * 1024 * (1 + (i % 50)),  # Размер от 1MB до 50MB
                'filename': f"{mod_type.lower()}_{i+1}.zip"
            }
            
            items.append(item)
            
        return items
        
    def get_published_file_details(self, published_file_ids: List[str]) -> Dict[str, Any]:
        """Получение детальной информации о файлах мастерской"""
        try:
            if not self.api_key:
                raise SteamAPIError("Требуется API ключ Steam")
                
            url = f"{self.base_url}/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
            
            # Подготавливаем данные для POST запроса
            data = {
                'key': self.api_key,
                'itemcount': len(published_file_ids),
                'format': 'json'
            }
            
            # Добавляем ID файлов
            for i, file_id in enumerate(published_file_ids):
                data[f'publishedfileids[{i}]'] = file_id
                
            response = self.session.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'response' not in result:
                raise SteamAPIError("Неверный формат ответа API")
                
            return result['response']
            
        except requests.exceptions.RequestException as e:
            raise SteamAPIError(f"Ошибка сети: {str(e)}")
        except json.JSONDecodeError as e:
            raise SteamAPIError(f"Ошибка парсинга JSON: {str(e)}")
        except Exception as e:
            raise SteamAPIError(f"Неизвестная ошибка: {str(e)}")
            
    def get_user_published_files(self, steam_id: str, app_id: int) -> List[Dict[str, Any]]:
        """Получение файлов пользователя в мастерской"""
        try:
            if not self.api_key:
                raise SteamAPIError("Требуется API ключ Steam")
                
            url = f"{self.base_url}/ISteamRemoteStorage/GetUserPublishedItemVoteDetails/v1/"
            
            params = {
                'key': self.api_key,
                'steamid': steam_id,
                'appid': app_id,
                'format': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'response' not in result:
                raise SteamAPIError("Неверный формат ответа API")
                
            return result['response'].get('publishedfiledetails', [])
            
        except requests.exceptions.RequestException as e:
            raise SteamAPIError(f"Ошибка сети: {str(e)}")
        except json.JSONDecodeError as e:
            raise SteamAPIError(f"Ошибка парсинга JSON: {str(e)}")
        except Exception as e:
            raise SteamAPIError(f"Неизвестная ошибка: {str(e)}")
            
    def download_workshop_item(self, item_data: Dict[str, Any]) -> str:
        """Получение URL для скачивания элемента мастерской"""
        try:
            # В реальном приложении здесь будет логика получения прямой ссылки
            # Для демонстрации возвращаем тестовую ссылку
            file_url = item_data.get('file_url')
            
            if not file_url:
                # Генерируем URL через сторонний сервис (например, steamworkshopdownloader.io)
                published_file_id = item_data.get('publishedfileid')
                file_url = f"https://steamworkshopdownloader.io/download/{published_file_id}"
                
            return file_url
            
        except Exception as e:
            raise SteamAPIError(f"Ошибка получения ссылки для скачивания: {str(e)}")
            
    def validate_api_key(self) -> bool:
        """Проверка валидности API ключа"""
        try:
            if not self.api_key:
                return False
                
            # Простой запрос для проверки ключа
            url = f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/"
            params = {
                'key': self.api_key,
                'steamids': '76561197960435530',  # Тестовый Steam ID
                'format': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return 'response' in result
            else:
                return False
                
        except Exception:
            return False
            
    def get_app_info(self, app_id: int) -> Dict[str, Any]:
        """Получение информации о приложении"""
        try:
            # Поиск в локальном списке
            for game in self.popular_games:
                if game['appid'] == app_id:
                    return {
                        'appid': app_id,
                        'name': game['name'],
                        'has_workshop': True,
                        'workshop_enabled': True
                    }
                    
            # Если не найдено в локальном списке
            return {
                'appid': app_id,
                'name': f'Game {app_id}',
                'has_workshop': True,
                'workshop_enabled': True
            }
            
        except Exception as e:
            raise SteamAPIError(f"Ошибка получения информации о приложении: {str(e)}")
