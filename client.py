from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import socket
import json
import threading
import time
import struct
import os
import sys
from settings import get_saved_display_settings, scale_value, get_audio_settings

class GameClient:
    def __init__(self):
        # Получаем сохраненные настройки отображения
        try:
            display_mode, resolution = get_saved_display_settings()
        except Exception as e:
            print(f"[CLIENT] Ошибка загрузки настроек: {e}")
            # Настройки по умолчанию
            display_mode = "windowed"
            resolution = (1280, 720)
        
        self.display_mode = display_mode
        self.selected_width, self.selected_height = resolution
        
        # Получаем настройки звука
        try:
            self.audio_settings = get_audio_settings()
        except Exception as e:
            print(f"[CLIENT] Ошибка загрузки настроек звука: {e}")
            self.audio_settings = {
                "music_volume": 0.5,
                "sound_volume": 0.5,
                "music_enabled": True
            }
        
        # Флаг загрузки музыки
        self.music_loaded = False
        self.music_playing = False
        
        # Инициализация звука и загрузка музыки
        self.init_audio()

        # Инициализация Pygame с выбранным режимом
        pygame.init()
        
        if display_mode == "fullscreen":
            self.screen = pygame.display.set_mode((self.selected_width, self.selected_height), pygame.FULLSCREEN)
        elif display_mode == "borderless":
            self.screen = pygame.display.set_mode((self.selected_width, self.selected_height), pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode((self.selected_width, self.selected_height))
        
        pygame.display.set_caption(f"Гамбит - {self.selected_width}x{self.selected_height}")
        
        # Масштабирование
        self.SCALE_X = self.selected_width / 1280
        self.SCALE_Y = self.selected_height / 850
        
        # Настройки соединения
        self.host = 'localhost'
        self.port = 5555
        
        # Сокет
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Игровые данные
        self.player_id = None
        self.player_name = None
        self.game_state = None
        self.line_cards = None
        self.hands = {"p1": [], "p2": []}
        self.card_images = {}
        self.zoomed_card = None
        
        # Загрузка изображения поля
        self.field_image = None
        self.load_field_image()
        
        # Инициализация звука и загрузка музыки
        self.init_audio()
        
        # Цвета
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 120, 0)
        self.RED = (120, 0, 0)
        self.HIGHLIGHT = (220, 220, 60)
        self.DARK_BG = (34, 34, 34)
        self.LIFE_COLOR = (200, 50, 50)
        self.PASS_COLOR = (100, 100, 100)
        
        # Размеры карт
        self.CARD_WIDTH = scale_value(100, 'x', self.SCALE_X, self.SCALE_Y)
        self.CARD_HEIGHT = scale_value(140, 'y', self.SCALE_X, self.SCALE_Y)
        self.ZOOMED_CARD_WIDTH = scale_value(180, 'x', self.SCALE_X, self.SCALE_Y)
        self.ZOOMED_CARD_HEIGHT = scale_value(270, 'y', self.SCALE_X, self.SCALE_Y)
        
        # Позиции линий
        self.LINES_Y = {
            "p1_back": int(self.selected_height * 0.6),
            "p1_front": int(self.selected_height * 0.427),
            "p2_front": int(self.selected_height * 0.246),
            "p2_back": int(self.selected_height * 0.072)
        }
        self.LINE_HEIGHT = scale_value(150, 'y', self.SCALE_X, self.SCALE_Y)
        
        # Размеры шрифтов (вычисляем ДО загрузки шрифтов)
        self.FONT_SIZE = scale_value(20, 'y', self.SCALE_X, self.SCALE_Y)
        self.SMALL_FONT_SIZE = scale_value(14, 'y', self.SCALE_X, self.SCALE_Y)
        self.BIG_FONT_SIZE = scale_value(60, 'y', self.SCALE_X, self.SCALE_Y)

        # Шрифты
        try:
            possible_font_paths = [
                os.path.join("fonts", "OFONT.RU_VINQUE RG.TTF"),
                "fonts/OFONT.RU_VINQUE RG.TTF",
                "OFONT.RU_VINQUE RG.TTF",
                os.path.join(os.path.dirname(__file__), "fonts", "OFONT.RU_VINQUE RG.TTF"),
                os.path.join(os.path.dirname(__file__), "OFONT.RU_VINQUE RG.TTF"),
                os.path.join("assets", "fonts", "OFONT.RU_VINQUE RG.TTF"),
                os.path.join("assets", "OFONT.RU_VINQUE RG.TTF"),
            ]
            
            font_path = None
            for path in possible_font_paths:
                if os.path.exists(path):
                    font_path = path
                    print(f"[CLIENT] Найден шрифт Vinque: {font_path}")
                    break
            
            if font_path:
                # Загружаем основные шрифты разных размеров
                self.FONT = pygame.font.Font(font_path, self.FONT_SIZE)
                self.SMALL_FONT = pygame.font.Font(font_path, self.SMALL_FONT_SIZE)
                self.BIG_FONT = pygame.font.Font(font_path, scale_value(60, 'y', self.SCALE_X, self.SCALE_Y))
                print("[CLIENT] Шрифт Vinque успешно загружен")
            else:
                raise FileNotFoundError("Шрифт Vinque не найден ни по одному из путей")
                
        except Exception as e:
            print(f"[CLIENT] Ошибка загрузки шрифта Vinque: {e}. Используются стандартные шрифты.")
            # Запасной вариант - системные шрифты
            self.FONT = pygame.font.SysFont("arial", self.FONT_SIZE)
            self.SMALL_FONT = pygame.font.SysFont("arial", self.SMALL_FONT_SIZE)
            self.BIG_FONT = pygame.font.SysFont("arial", scale_value(60, 'y', self.SCALE_X, self.SCALE_Y), bold=True)
        
        # Позиция руки
        self.hand_y = self.selected_height - scale_value(180, 'y', self.SCALE_X, self.SCALE_Y)
        self.card_spacing = scale_value(110, 'x', self.SCALE_X, self.SCALE_Y)
        
        # Кнопка ПАС
        self.pass_btn_rect = pygame.Rect(
            self.selected_width - scale_value(50, 'x', self.SCALE_X, self.SCALE_Y),
            self.selected_height // 2.6,
            scale_value(50, 'x', self.SCALE_X, self.SCALE_Y),
            scale_value(50, 'y', self.SCALE_X, self.SCALE_Y)
        )
        
        # Состояние
        self.connected = False
        self.game_started = False
        self.chat_messages = []
        self.chat_input = ""
        self.chat_active = False
        self.selected_card_index = None
        self.dragging_card = False
        self.drag_offset = (0, 0)
        
        # Переменные для отслеживания смены хода
        self.last_turn = None
        
        # Флаг для музыки
        self.music_playing = False
        
        # Загружаем стандартное изображение для карт
        self.default_card_image = pygame.Surface((self.CARD_WIDTH, self.CARD_HEIGHT))
        self.default_card_image.fill((100, 100, 100))

    def init_audio(self):
        """Инициализация звука и загрузка музыки"""
        try:
            pygame.mixer.init()

            music_paths = [
                "sounds/track1.mp3", 
                os.path.join("sounds", "track1.mp3"),  
                os.path.join(os.path.dirname(__file__), "sounds", "track1.mp3"),
                os.path.join(os.getcwd(), "sounds", "track1.mp3"),
            ]
            
            music_loaded = False
            actual_path = None
            
            for path in music_paths:
                try:
                    if os.path.exists(path):
                        pygame.mixer.music.load(path)
                        music_loaded = True
                        actual_path = path
                        print(f"[CLIENT] Музыка загружена из: {actual_path}")
                        break
                except Exception as e:
                    print(f"[CLIENT] Не удалось загрузить музыку из {path}: {e}")
                    continue
            
            if not music_loaded:
                print("[CLIENT] ВНИМАНИЕ: Музыка не загружена. Будет играть без музыки.")
                self.music_loaded = False
            else:
                self.music_loaded = True

                if self.audio_settings["music_enabled"]:
                    pygame.mixer.music.set_volume(self.audio_settings["music_volume"])
                    print(f"[CLIENT] Громкость музыки установлена: {self.audio_settings['music_volume']}")
                else:
                    pygame.mixer.music.set_volume(0)
                    print("[CLIENT] Музыка выключена в настройках")
                    
        except Exception as e:
            print(f"[CLIENT] Ошибка инициализации звука: {e}")
            self.music_loaded = False

    def play_game_music(self):
        """Запуск игровой музыки"""
        if not self.music_playing and self.audio_settings["music_enabled"] and self.music_loaded:
            try:
                pygame.mixer.music.play(-1)
                self.music_playing = True
                print("[CLIENT] Игровая музыка запущена")
            except Exception as e:
                print(f"[CLIENT] Ошибка воспроизведения музыки: {e}")
                self.music_playing = False
        elif not self.music_loaded:
            print("[CLIENT] Не удалось запустить музыку: файл не загружен")

    def stop_music(self):
        """Остановка музыки"""
        if self.music_playing:
            pygame.mixer.music.stop()
            self.music_playing = False
            print("[CLIENT] Музыка остановлена")

    def load_user_deck(self):
        import os
        import json
 
        base_path = os.path.dirname(os.path.abspath(__file__))
        deck_path = os.path.join(base_path, "my_deck.json")
        
        print(f"[CLIENT] Ищу файл колоды здесь: {deck_path}")

        if not os.path.exists(deck_path):
            print(f"[CLIENT] ОШИБКА: Файл my_deck.json не найден по указанному пути!")
            deck_path = os.path.join(base_path, "assets", "my_deck.json")
            print(f"[CLIENT] Пробую искать здесь: {deck_path}")
            if not os.path.exists(deck_path):
                return None

        try:
            with open(deck_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Проверяем структуру JSON
                if "cards" in data:
                    cards = data["cards"]
                elif isinstance(data, list):
                    cards = data
                else:
                    print("[CLIENT] ОШИБКА: Непонятный формат JSON (нет ключа 'cards' и это не список)")
                    return None
                
                print(f"[CLIENT] Успешно загружено {len(cards)} карт из файла.")
                
                if len(cards) != 20:
                    print(f"[CLIENT] ВНИМАНИЕ: В колоде {len(cards)} карт! Сервер отклонит её (надо 20).")
                
                return cards
                
        except Exception as e:
            print(f"[CLIENT] Критическая ошибка чтения файла: {e}")
            return None

    def get_card_image_path(self, image_path):
        """Получение корректного пути к изображению карты"""
        if os.path.exists(image_path):
            return image_path
        
        possible_paths = [
            image_path,
            os.path.join("assets", os.path.basename(image_path)),
            os.path.join(os.path.dirname(__file__), "assets", os.path.basename(image_path)),
            os.path.join("assets", "cards", os.path.basename(image_path)),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path

        return image_path

    def load_field_image(self):
        """Загрузка изображения поля"""
        try:
            possible_paths = [
                "field.png",
                os.path.join("assets", "field.png"),
                os.path.join("images", "field.png"),
                os.path.join("textures", "field.png"),
                os.path.join(os.path.dirname(__file__), "field.png"),
                os.path.join(os.path.dirname(__file__), "assets", "field.png"),
                os.path.join(os.path.dirname(__file__), "images", "field.png"),
                os.path.join(os.path.dirname(__file__), "textures", "field.png"),
            ]
            
            field_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    field_path = path
                    break
            
            if field_path:
                print(f"[CLIENT] Загрузка изображения поля: {field_path}")
                img = pygame.image.load(field_path)
                self.field_image = pygame.transform.scale(img, (self.selected_width, self.selected_height))
                print(f"[CLIENT] Изображение поля загружено успешно")
            else:
                print(f"[CLIENT] Предупреждение: файл field.png не найден. Будет использован цветной фон.")
                self.field_image = pygame.Surface((self.selected_width, self.selected_height))
                self.field_image.fill((20, 40, 20))  
                # Добавляем текстуру
                for i in range(0, self.selected_width, 20):
                    for j in range(0, self.selected_height, 20):
                        if (i // 20 + j // 20) % 2 == 0:
                            pygame.draw.rect(self.field_image, (15, 35, 15), (i, j, 20, 20))
        except Exception as e:
            print(f"[CLIENT] Ошибка загрузки изображения поля: {e}")
            # Создаем простой фон
            self.field_image = pygame.Surface((self.selected_width, self.selected_height))
            self.field_image.fill((34, 34, 34))
    
    def send_message(self, message):
        """Отправка сообщения с указанием размера"""
        try:
            
            data = json.dumps(message).encode('utf-8')
           
            self.client.send(struct.pack('!I', len(data)))
            
            self.client.send(data)
            return True
        except Exception as e:
            print(f"[CLIENT] Ошибка отправки: {e}")
            return False
    
    def receive_message(self):
        """Получение сообщения с указанием размера"""
        try:
            
            raw_msglen = self.client.recv(4)
            if not raw_msglen:
                return None
            
            msglen = struct.unpack('!I', raw_msglen)[0]
            
           
            data = b''
            while len(data) < msglen:
                packet = self.client.recv(min(4096, msglen - len(data)))
                if not packet:
                    return None
                data += packet
            
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"[CLIENT] Ошибка получения: {e}")
            return None
    
    def connect_to_server(self):
        """Подключение к серверу (версия для лаунчера)"""
        try:
            # Получаем IP из переменной окружения или используем localhost
            ip = os.environ.get('GAME_SERVER_IP', 'localhost')
            port = 5555
            
            print(f"[CLIENT] Подключение к серверу {ip}:{port}...")
            self.client.connect((ip, port))
            self.connected = True
            
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
        except Exception as e:
            print(f"[CLIENT] Не удалось подключиться к серверу: {e}")
            print("Проверьте:")
            print("1. Сервер запущен")
            print("2. Правильно указан IP-адрес")
            print("3. Работает Radmin VPN (если подключаетесь через него)")
            return False
    
    def receive_messages(self):
        """Получение сообщений от сервера"""
        while self.connected:
            try:
                message = self.receive_message()
                if message is None:
                    break
                    
                self.handle_server_message(message)
                
            except Exception as e:
                print(f"[CLIENT] Ошибка обработки сообщения: {e}")
                break
        
        print("[CLIENT] Отключен от сервера")
        self.connected = False
    
    def handle_server_message(self, data):
        """Обработка сообщений от сервера"""
        msg_type = data.get("type")
        
        if msg_type == "welcome":
            self.player_id = data["player_id"]
            self.player_name = data["player_name"]
            print(f"[CLIENT] Вы {self.player_name} (ID: {self.player_id})")
            
        elif msg_type == "player_ready":
            print(f"[CLIENT] Игрок {data['player']} готов. Готовых: {data['ready_players']}/2")
            
        elif msg_type == "game_update":
            
            old_turn = self.game_state["current_turn"] if self.game_state else None
            self.game_state = data["game_state"]
            new_turn = self.game_state["current_turn"]

            if old_turn is not None and old_turn != new_turn and new_turn != self.player_id:
                self.reset_drag_state()
            
            self.line_cards = data["line_cards"]
            self.hands = data["hands"]
            self.game_started = self.game_state["game_started"]

            self.preload_card_images()
            
        elif msg_type == "chat_message":
            message = f"""{data.get('player_name', f"Игрок {data['player']}")}: {data['message']}"""
            self.chat_messages.append(message)
            if len(self.chat_messages) > 10:
                self.chat_messages.pop(0)
                
        elif msg_type == "player_disconnected":
            print(f"[CLIENT] Игрок {data['player']} отключился")
    
    def reset_drag_state(self):
        """Сброс состояния перетаскивания"""
        self.selected_card_index = None
        self.dragging_card = False
        self.drag_offset = (0, 0)
        self.zoomed_card = None
    
    def preload_card_images(self):
        """Предзагрузка изображений карт"""
        all_cards = []
        for player in ["p1", "p2"]:
            all_cards.extend(self.hands.get(player, []))
        
        for key in self.line_cards:
            all_cards.extend(self.line_cards.get(key, []))
        
        for card in all_cards:
            image_path = card.get("image_path", "")
            if image_path and image_path not in self.card_images:
                try:
                    
                    actual_path = self.get_card_image_path(image_path)
                    
                    if os.path.exists(actual_path):
                        img = pygame.image.load(actual_path)
                        self.card_images[image_path] = pygame.transform.scale(
                            img, (self.CARD_WIDTH, self.CARD_HEIGHT)
                        )
                        print(f"[CLIENT] Загружена картинка: {actual_path}")
                    else:
                        self.create_card_placeholder(image_path, card)
                        
                except Exception as e:
                    print(f"[CLIENT] Ошибка загрузки картинки {image_path}: {e}")
                    self.create_card_placeholder(image_path, card)
    
    def create_card_placeholder(self, image_path, card):
        """Создание заглушки для карты"""
        surface = pygame.Surface((self.CARD_WIDTH, self.CARD_HEIGHT))

        if card.get("player", "").startswith("p1"):
            color = (50, 50, 100)  
        elif card.get("player", "").startswith("p2"):
            color = (100, 50, 50)  
        else:
            color = (100, 100, 100)  
        
        surface.fill(color)
        
        # Рамка
        pygame.draw.rect(surface, (200, 200, 200), surface.get_rect(), 2)
        
        # Название карты
        name = card.get("name", "Карта")
        font = pygame.font.SysFont("arial", 14)
        name_text = font.render(name[:8], True, (255, 255, 255))
        surface.blit(name_text, (self.CARD_WIDTH//2 - name_text.get_width()//2, 
                            self.CARD_HEIGHT//2 - name_text.get_height()//2))
        
        # Сила карты
        power = card.get("power", 0)
        power_text = font.render(str(power), True, (255, 200, 200))
        surface.blit(power_text, (10, 10))
        
        self.card_images[image_path] = surface

    def get_card_image(self, image_path):
        """Получение изображения карты"""
        if image_path in self.card_images:
            return self.card_images[image_path]
        return self.default_card_image
    
    def send_action(self, action, data=None):
        """Отправка действия на сервер"""
        if not self.connected:
            return False
            
        message = {"action": action}
        if data:
            message.update(data)
            
        return self.send_message(message)
    
    def draw_lobby(self):
        """Отрисовка лобби"""
        self.screen.fill(self.DARK_BG)
        
        # Заголовок
        title = self.BIG_FONT.render("ОЖИДАНИЕ ИГРОКОВ", True, self.HIGHLIGHT)
        self.screen.blit(title, (self.selected_width//2 - title.get_width()//2, 
                               scale_value(100, 'y', self.SCALE_X, self.SCALE_Y)))
        
        # Информация о игроке
        player_text = self.FONT.render(f"ВЫ: {self.player_name}", True, self.WHITE)
        self.screen.blit(player_text, (self.selected_width//2 - player_text.get_width()//2, 
                                     scale_value(200, 'y', self.SCALE_X, self.SCALE_Y)))
        
        # Кнопка готовности
        button_rect = pygame.Rect(
            self.selected_width//2 - scale_value(100, 'x', self.SCALE_X, self.SCALE_Y),
            scale_value(300, 'y', self.SCALE_X, self.SCALE_Y),
            scale_value(200, 'x', self.SCALE_X, self.SCALE_Y),
            scale_value(60, 'y', self.SCALE_X, self.SCALE_Y)
        )
        
        mouse_pos = pygame.mouse.get_pos()
        button_color = (70, 130, 180) if button_rect.collidepoint(mouse_pos) else (50, 100, 150)
        
        pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 150, 200), button_rect, 3, border_radius=10)
        
        ready_text = self.FONT.render("ГОТОВ", True, self.WHITE)
        self.screen.blit(ready_text, (button_rect.centerx - ready_text.get_width()//2,
                                    button_rect.centery - ready_text.get_height()//2))
        
        # Подключенные игроки
        y_offset = scale_value(400, 'y', self.SCALE_X, self.SCALE_Y)
        for i in range(2):
            player_key = f"p{i+1}"
            status = "Готов" if self.game_state and self.game_state["players"].get(player_key, {}).get("ready") else "Ожидание"
            color = self.GREEN if status == "Готов" else self.RED
            
            player_status = self.FONT.render(f"Игрок {i+1}: {status}", True, color)
            self.screen.blit(player_status, (self.selected_width//2 - player_status.get_width()//2, y_offset))
            y_offset += scale_value(40, 'y', self.SCALE_X, self.SCALE_Y)
        
        # IP и порт сервера
        server_info = self.SMALL_FONT.render(f"Сервер: {self.host}:{self.port}", True, (180, 180, 220))
        self.screen.blit(server_info, (self.selected_width//2 - server_info.get_width()//2, 
                                     scale_value(550, 'y', self.SCALE_X, self.SCALE_Y)))
        
        pygame.display.update()
        return button_rect
    
    def draw_game(self):
        """Отрисовка игрового поля"""
        self.screen.blit(self.field_image, (0, 0))
        
        if not self.game_state:
            return
 
        current_turn = self.game_state["current_turn"]
        if self.last_turn is not None and self.last_turn != current_turn:
            
            if current_turn != self.player_id:
                self.reset_drag_state()
        self.last_turn = current_turn
        
        # Рисуем линии
        mouse_pos = pygame.mouse.get_pos()
        hover_line = None
        
        for key, y in self.LINES_Y.items():
            
            if (self.selected_card_index is not None and 
                self.game_state["current_turn"] == self.player_id):
                player_key = f"p{self.player_id+1}"
                if player_key in key:
                    line_rect = pygame.Rect(
                        scale_value(50, 'x', self.SCALE_X, self.SCALE_Y),
                        y,
                        self.selected_width - scale_value(100, 'x', self.SCALE_X, self.SCALE_Y),
                        self.LINE_HEIGHT
                    )
                    if line_rect.collidepoint(mouse_pos):
                        hover_line = key
            
            # Цвет линии
            color = self.BLACK if "p1" in key else self.BLACK
            if hover_line == key:
                color = self.HIGHLIGHT
            
            # Рисуем линию
            line_rect = pygame.Rect(
                scale_value(30, 'x', self.SCALE_X, self.SCALE_Y),
                y,
                self.selected_width - scale_value(64, 'x', self.SCALE_X, self.SCALE_Y),
                self.LINE_HEIGHT
            )
            line_width = scale_value(5, 'x', self.SCALE_X, self.SCALE_Y) if hover_line == key else scale_value(2, 'x', self.SCALE_X, self.SCALE_Y)
            pygame.draw.rect(self.screen, color, line_rect, line_width)
            
            # Сила линии
            line_power = 0
            for card in self.line_cards.get(key, []):
                line_power += card.get("power", 0)
            
            power_text = self.FONT.render(str(line_power), True, self.WHITE)
            self.screen.blit(power_text, (scale_value(10, 'x', self.SCALE_X, self.SCALE_Y), 
                                        y + self.LINE_HEIGHT // 2 - power_text.get_height() // 2))
        
        # Карты на поле
        for key, cards in self.line_cards.items():
            for i, card in enumerate(cards):
                x_pos = scale_value(120, 'x', self.SCALE_X, self.SCALE_Y) + i * scale_value(120, 'x', self.SCALE_X, self.SCALE_Y)
                y_pos = self.LINES_Y[key] + self.LINE_HEIGHT // 2
                
                card_image = self.get_card_image(card.get("image_path", ""))
                card_rect = card_image.get_rect(center=(x_pos, y_pos))
                self.screen.blit(card_image, card_rect)

                power = card.get("power", 0)

                # Координаты для кружка
                circle_radius = scale_value(8, 'x', self.SCALE_X, self.SCALE_Y)
                circle_x = card_rect.left + circle_radius + 11
                circle_y = card_rect.top + circle_radius + 15
                
                # Кружок
                pygame.draw.circle(self.screen, (50, 50, 50), (circle_x, circle_y), circle_radius)
                pygame.draw.circle(self.screen, (255, 255, 0), (circle_x, circle_y), circle_radius, 2)
                
                # Рисуем текст с мощностью
                power_text = self.SMALL_FONT.render(str(power), True, (255, 255, 0))
                text_rect = power_text.get_rect(center=(circle_x, circle_y))
                self.screen.blit(power_text, text_rect)
        
        player_key = f"p{self.player_id+1}"
        current_hand = self.hands.get(player_key, [])

        can_interact = (self.game_state["current_turn"] == self.player_id and 
                       not self.game_state["passed"][player_key])
        
        if len(current_hand) > 0:
            total_width = len(current_hand) * self.card_spacing
            start_x = (self.selected_width - total_width) // 2
            
            for i, card in enumerate(current_hand):

                if i == self.selected_card_index and self.dragging_card and can_interact:
                    card_x = mouse_pos[0] - self.drag_offset[0]
                    card_y = mouse_pos[1] - self.drag_offset[1]
                else:
                    card_x = start_x + i * self.card_spacing
                    card_y = self.hand_y
                
                card_rect = pygame.Rect(card_x, card_y, self.CARD_WIDTH, self.CARD_HEIGHT)

                card_image = self.get_card_image(card.get("image_path", ""))
                self.screen.blit(card_image, card_rect)

                if card_rect.collidepoint(mouse_pos) and not self.dragging_card and can_interact:
                    pygame.draw.rect(self.screen, self.HIGHLIGHT, card_rect, 
                                   scale_value(3, 'x', self.SCALE_X, self.SCALE_Y))
        
        # --- ИНТЕРФЕЙС ---
        
        # 1. Очки и жизни игроков
        ui_y = scale_value(10, 'y', self.SCALE_X, self.SCALE_Y)
        text_x_start = scale_value(20, 'x', self.SCALE_X, self.SCALE_Y)
        
        # Игрок 1 (слева)
        p1_color = self.HIGHLIGHT if self.game_state["current_turn"] == 0 else self.WHITE
        p1_info = f"Игрок 1 (Очки: {self.game_state['score']['p1']})"
        p1_surf = self.FONT.render(p1_info, True, p1_color)
        self.screen.blit(p1_surf, (text_x_start, ui_y))
        
        # Жизни игрока 1
        lives_x_p1 = text_x_start + p1_surf.get_width() + scale_value(10, 'x', self.SCALE_X, self.SCALE_Y)
        for i in range(2):
            color = self.LIFE_COLOR if i < self.game_state["lives"]["p1"] else (50, 50, 50)
            pygame.draw.circle(self.screen, color, 
                             (lives_x_p1 + i*scale_value(22, 'x', self.SCALE_X, self.SCALE_Y), 
                              ui_y + scale_value(15, 'y', self.SCALE_X, self.SCALE_Y)), 8)
        
        if self.game_state["passed"]["p1"]:
            self.screen.blit(self.SMALL_FONT.render("ПАС", True, (150, 150, 150)), 
                           (lives_x_p1 + scale_value(50, 'x', self.SCALE_X, self.SCALE_Y), ui_y + 5))
        
        # Игрок 2 (правее)
        text_x_p2 = lives_x_p1 + scale_value(150, 'x', self.SCALE_X, self.SCALE_Y)
        p2_color = self.HIGHLIGHT if self.game_state["current_turn"] == 1 else self.WHITE
        p2_info = f"Игрок 2 (Очки: {self.game_state['score']['p2']})"
        p2_surf = self.FONT.render(p2_info, True, p2_color)
        self.screen.blit(p2_surf, (text_x_p2, ui_y))
        
        # Жизни игрока 2
        lives_x_p2 = text_x_p2 + p2_surf.get_width() + scale_value(10, 'x', self.SCALE_X, self.SCALE_Y)
        for i in range(2):
            color = self.LIFE_COLOR if i < self.game_state["lives"]["p2"] else (50, 50, 50)
            pygame.draw.circle(self.screen, color, 
                             (lives_x_p2 + i*scale_value(22, 'x', self.SCALE_X, self.SCALE_Y), 
                              ui_y + scale_value(15, 'y', self.SCALE_X, self.SCALE_Y)), 8)
        
        if self.game_state["passed"]["p2"]:
            self.screen.blit(self.SMALL_FONT.render("ПАС", True, (150, 150, 150)), 
                           (lives_x_p2 + scale_value(50, 'x', self.SCALE_X, self.SCALE_Y), ui_y + 5))
        
        # 2. Индикатор хода
        turn_player = '1' if self.game_state["current_turn"] == 0 else '2'
        turn_text = f"ХОД: ИГРОК {turn_player}"
        turn_color = self.HIGHLIGHT
        turn_surf = self.FONT.render(turn_text, True, turn_color)
        self.screen.blit(turn_surf, (self.selected_width // 2 - turn_surf.get_width() // 2, ui_y))
        
        # Индикация, чей сейчас ход (для текущего игрока)
        if self.game_state["current_turn"] == self.player_id:
            your_turn_text = self.SMALL_FONT.render("(Ваш ход)", True, (100, 255, 100))
            self.screen.blit(your_turn_text, (self.selected_width // 2 - your_turn_text.get_width() // 2, 
                                            ui_y + self.FONT_SIZE + 5))
        else:
            # Индикация, что ход другого игрока
            waiting_text = self.SMALL_FONT.render("(Ход противника)", True, (255, 100, 100))
            self.screen.blit(waiting_text, (self.selected_width // 2 - waiting_text.get_width() // 2, 
                                          ui_y + self.FONT_SIZE + 5))
        
        # 3. Номер раунда
        round_text = f"РАУНД {self.game_state['round']}"
        round_surf = self.FONT.render(round_text, True, self.WHITE)
        self.screen.blit(round_surf, (self.selected_width - round_surf.get_width() - text_x_start, ui_y))
        
        # 4. Кнопка ПАС
        if (self.game_state["current_turn"] == self.player_id and 
            not self.game_state["passed"][player_key]):
            
            btn_color = (200, 200, 200) if self.pass_btn_rect.collidepoint(mouse_pos) else self.PASS_COLOR
            pygame.draw.rect(self.screen, btn_color, self.pass_btn_rect, border_radius=5)
            
            btn_text = self.FONT.render("ПАС", True, (0, 0, 0))
            self.screen.blit(btn_text, (self.pass_btn_rect.centerx - btn_text.get_width()//2,
                                      self.pass_btn_rect.centery - btn_text.get_height()//2))
        
        # 5. Сообщения игры
        if (self.game_state.get("message") and 
            self.game_state.get("message_timer", 0) > time.time()):
            
            text_surf = self.FONT.render(self.game_state["message"], True, (255, 255, 0))
            bg_rect = text_surf.get_rect(center=(self.selected_width // 2, 
                                               self.selected_height // 2 - scale_value(50, 'y', self.SCALE_X, self.SCALE_Y)))
            bg_surface = pygame.Surface((bg_rect.width + 20, bg_rect.height + 10), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 200))
            self.screen.blit(bg_surface, (bg_rect.x - 10, bg_rect.y - 5))
            self.screen.blit(text_surf, bg_rect)
        
        # 6. Чат
        self.draw_chat()
        
        # 7. Увеличенная карта
        if self.zoomed_card:
            self.draw_zoomed_card()
        
        pygame.display.update()
    
    def draw_chat(self):
        """Отрисовка чата"""
        chat_rect = pygame.Rect(
            scale_value(10, 'x', self.SCALE_X, self.SCALE_Y),
            self.selected_height - scale_value(200, 'y', self.SCALE_X, self.SCALE_Y),
            scale_value(300, 'x', self.SCALE_X, self.SCALE_Y),
            scale_value(190, 'y', self.SCALE_X, self.SCALE_Y)
        )
        
        # Фон чата
        overlay = pygame.Surface((chat_rect.width, chat_rect.height), pygame.SRCALPHA)
        overlay.fill((40, 40, 40, 200))
        self.screen.blit(overlay, chat_rect)
        
        # Сообщения
        y_offset = chat_rect.top + scale_value(5, 'y', self.SCALE_X, self.SCALE_Y)
        for msg in self.chat_messages[-8:]:
            msg_text = self.SMALL_FONT.render(msg, True, self.WHITE)
            if msg_text.get_width() > chat_rect.width - 10:
                # Обрезаем слишком длинные сообщения
                msg_text = self.SMALL_FONT.render(msg[:30] + "...", True, self.WHITE)
            self.screen.blit(msg_text, (chat_rect.left + 5, y_offset))
            y_offset += scale_value(20, 'y', self.SCALE_X, self.SCALE_Y)
        
        # Поле ввода
        input_rect = pygame.Rect(chat_rect.left, chat_rect.bottom - scale_value(25, 'y', self.SCALE_X, self.SCALE_Y), 
                               chat_rect.width, scale_value(25, 'y', self.SCALE_X, self.SCALE_Y))
        
        pygame.draw.rect(self.screen, (60, 60, 60), input_rect)
        
        if self.chat_active:
            pygame.draw.rect(self.screen, self.HIGHLIGHT, input_rect, 2)
        
        # Текст в поле ввода
        display_text = self.chat_input
        if time.time() % 1 > 0.5 and self.chat_active:
            display_text += "|"
        
        input_text = self.SMALL_FONT.render(display_text, True, self.WHITE)
        self.screen.blit(input_text, (input_rect.left + 5, input_rect.top + 5))
    
    def draw_zoomed_card(self):
        """Отрисовка увеличенной карты"""
        if not self.zoomed_card:
            return
            
        # Полупрозрачный фон
        overlay = pygame.Surface((self.selected_width, self.selected_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Увеличенная карта
        image_path = self.zoomed_card.get("image_path", "")

        img_loaded = False
        zoomed_img = None

        possible_paths = [
            image_path,
            os.path.basename(image_path),  
            os.path.join("assets", os.path.basename(image_path)),
            os.path.join(os.path.dirname(__file__), "assets", os.path.basename(image_path)),
            os.path.join("assets", "cards", os.path.basename(image_path)),
        ]

        for path in possible_paths:
            try:
                if os.path.exists(path):
                    img = pygame.image.load(path)
                    zoomed_img = pygame.transform.scale(img, (self.ZOOMED_CARD_WIDTH, self.ZOOMED_CARD_HEIGHT))
                    img_loaded = True
                    break
            except:
                continue
        
        if not img_loaded:
            zoomed_img = pygame.Surface((self.ZOOMED_CARD_WIDTH, self.ZOOMED_CARD_HEIGHT))

            card_name = self.zoomed_card.get("name", "")
            color_hash = hash(card_name) % 256, (hash(card_name) // 256) % 256, (hash(card_name) // 65536) % 256
            zoomed_img.fill(color_hash)

            pygame.draw.rect(zoomed_img, (255, 255, 255), zoomed_img.get_rect(), 3)

            font = pygame.font.SysFont("arial", 24)
            name_text = font.render(card_name, True, (255, 255, 255))
            zoomed_img.blit(name_text, (self.ZOOMED_CARD_WIDTH//2 - name_text.get_width()//2, 
                                    self.ZOOMED_CARD_HEIGHT//2 - name_text.get_height()//2))
            
            print(f"[ZOOM] Создана заглушка для: {card_name}")

        card_rect = zoomed_img.get_rect(center=(self.selected_width // 2, self.selected_height // 2))
        self.screen.blit(zoomed_img, card_rect)

        info_y = card_rect.bottom + scale_value(10, 'y', self.SCALE_X, self.SCALE_Y)

        name_text = self.FONT.render(self.zoomed_card.get("name", ""), True, self.HIGHLIGHT)
        self.screen.blit(name_text, (self.selected_width // 2 - name_text.get_width() // 2, info_y))

        power = self.zoomed_card.get("power", 0)
        power_text = self.FONT.render(f"Сила: {power}", True, self.WHITE)
        self.screen.blit(power_text, (self.selected_width // 2 - power_text.get_width() // 2, 
                                    info_y + scale_value(30, 'y', self.SCALE_X, self.SCALE_Y)))

        lines = self.zoomed_card.get("allowed_lines", [])
        lines_text = self.SMALL_FONT.render(f"Линии: {', '.join(lines)}", True, self.WHITE)
        self.screen.blit(lines_text, (self.selected_width // 2 - lines_text.get_width() // 2, 
                                    info_y + scale_value(60, 'y', self.SCALE_X, self.SCALE_Y)))
        
        # Способность
        ability = self.zoomed_card.get("ability")
        if ability:
            ability_name = ability if isinstance(ability, str) else ability.__name__ if ability else "Нет"
            ability_text = self.SMALL_FONT.render(f"Способность: {ability_name}", True, (200, 200, 100))
            self.screen.blit(ability_text, (self.selected_width // 2 - ability_text.get_width() // 2, 
                                        info_y + scale_value(90, 'y', self.SCALE_X, self.SCALE_Y)))
        
        # Инструкция
        instr_text = self.SMALL_FONT.render("Нажмите ESC для закрытия", True, (150, 150, 150))
        self.screen.blit(instr_text, (self.selected_width // 2 - instr_text.get_width() // 2, 
                                    info_y + scale_value(120, 'y', self.SCALE_X, self.SCALE_Y)))
    
    def draw_game_over(self):
        """Отрисовка экрана конца игры"""
        self.screen.fill((20, 0, 0))
        
        if self.game_state and self.game_state["winner"]:
            text = self.BIG_FONT.render("ИГРА ОКОНЧЕНА", True, self.RED)
            sub = self.FONT.render(f"ПОБЕДИТЕЛЬ: {self.game_state['winner']}", True, self.WHITE)
            
            self.screen.blit(text, (self.selected_width//2 - text.get_width()//2, 
                                  self.selected_height//2 - 100))
            self.screen.blit(sub, (self.selected_width//2 - sub.get_width()//2, 
                                 self.selected_height//2))
            
            # Статистика
            stats_y = self.selected_height//2 + 50
            p1_stats = f"Игрок 1: {self.game_state['lives']['p1']} жизней, {self.game_state['score']['p1']} очков"
            p2_stats = f"Игрок 2: {self.game_state['lives']['p2']} жизней, {self.game_state['score']['p2']} очков"
            
            p1_text = self.SMALL_FONT.render(p1_stats, True, self.GREEN)
            p2_text = self.SMALL_FONT.render(p2_stats, True, self.RED)
            
            self.screen.blit(p1_text, (self.selected_width//2 - p1_text.get_width()//2, stats_y))
            self.screen.blit(p2_text, (self.selected_width//2 - p2_text.get_width()//2, stats_y + 30))
            
            # Инструкция
            instr = self.SMALL_FONT.render("Нажмите ESC для выхода", True, (150, 150, 150))
            self.screen.blit(instr, (self.selected_width//2 - instr.get_width()//2, 
                                   self.selected_height - 50))
        
        pygame.display.update()
    
    def run(self):
        """Запуск клиента"""
        if not self.connect_to_server():
            print("Нажмите Enter для выхода...")
            input()
            return
        
        clock = pygame.time.Clock()
        running = True
        
        while running:
            clock.tick(60)
            
            # Управление музыкой
            if self.game_started and not self.music_playing:
                if self.music_loaded:
                    self.play_game_music()
                else:
                    print("[CLIENT] Музыка не загружена, пропускаем воспроизведение")
            elif not self.game_started and self.music_playing:
                self.stop_music()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.connected = False
                    if self.client:
                        self.client.close()

                elif not self.game_started:
                    # Лобби
                    button_rect = self.draw_lobby()
                    
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        if button_rect.collidepoint(mouse_pos):
                            
                            user_deck = self.load_user_deck()
                            
                            if user_deck:
                                
                                self.send_action("ready", {"deck_cards": user_deck})
                            else:
                                print("[CLIENT] Ошибка: Не удалось загрузить колоду для отправки")
                                self.game_state = {"message": "Ошибка: нет файла my_deck.json!", "message_timer": time.time() + 3}
                
                elif self.game_state and self.game_state["game_over"]:
                  
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False
                
                else:
                    
                    player_key = f"p{self.player_id+1}"
                    
                    can_interact = (self.game_state["current_turn"] == self.player_id and 
                                   not self.game_state["passed"][player_key])
                    
                    # ПКМ - увеличение карты
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                        mouse_pos = pygame.mouse.get_pos()
                        
                        player_key = f"p{self.player_id+1}"
                        current_hand = self.hands.get(player_key, [])

                        card_found = None
                        
                        # 1. Проверяем карты в руке
                        if len(current_hand) > 0:
                            total_width = len(current_hand) * self.card_spacing
                            start_x = (self.selected_width - total_width) // 2
                            
                            for i, card in enumerate(current_hand):
                                card_rect = pygame.Rect(start_x + i * self.card_spacing, self.hand_y, 
                                                    self.CARD_WIDTH, self.CARD_HEIGHT)
                                
                                if card_rect.collidepoint(mouse_pos):
                                    card_found = card
                                    break
                        
                        # 2. Если не нашли в руке, проверяем карты на поле
                        if not card_found:
                            for key, cards in self.line_cards.items():
                                if cards:  
                                    for i, card in enumerate(cards):
                                        x_pos = scale_value(120, 'x', self.SCALE_X, self.SCALE_Y) + i * scale_value(120, 'x', self.SCALE_X, self.SCALE_Y)
                                        y_pos = self.LINES_Y[key] + self.LINE_HEIGHT // 2
                                        
                                        card_rect = pygame.Rect(x_pos - self.CARD_WIDTH//2, 
                                                            y_pos - self.CARD_HEIGHT//2,
                                                            self.CARD_WIDTH, self.CARD_HEIGHT)
                                        
                                        if card_rect.collidepoint(mouse_pos):
                                            card_found = card
                                            break
                                    if card_found:
                                        break

                        self.zoomed_card = card_found

                        if card_found:
                            print(f"[CLIENT] Увеличение карты: {card_found.get('name', 'Неизвестно')}")
                            print(f"[CLIENT] Путь к изображению: {card_found.get('image_path', 'Нет пути')}")
                        else:
                            self.zoomed_card = None
                    
                    # ЛКМ - взаимодействия (только если наш ход)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        
                        # Проверка кнопки ПАС
                        if (self.pass_btn_rect.collidepoint(mouse_pos) and can_interact):
                            self.send_action("pass_turn")
                            self.reset_drag_state()

                        elif can_interact:
                            current_hand = self.hands.get(player_key, [])
                            if len(current_hand) > 0:
                                total_width = len(current_hand) * self.card_spacing
                                start_x = (self.selected_width - total_width) // 2
                                
                                for i in range(len(current_hand)):
                                    card_rect = pygame.Rect(start_x + i * self.card_spacing, self.hand_y, 
                                                          self.CARD_WIDTH, self.CARD_HEIGHT)
                                    
                                    if card_rect.collidepoint(mouse_pos):
                                        self.selected_card_index = i
                                        self.dragging_card = True
                                        self.drag_offset = (mouse_pos[0] - card_rect.x, 
                                                          mouse_pos[1] - card_rect.y)
                                        break

                        chat_input_rect = pygame.Rect(
                            scale_value(10, 'x', self.SCALE_X, self.SCALE_Y),
                            self.selected_height - scale_value(25, 'y', self.SCALE_X, self.SCALE_Y),
                            scale_value(300, 'x', self.SCALE_X, self.SCALE_Y),
                            scale_value(25, 'y', self.SCALE_X, self.SCALE_Y)
                        )
                        self.chat_active = chat_input_rect.collidepoint(mouse_pos)
                        if not self.chat_active:
                            self.zoomed_card = None

                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        if (self.selected_card_index is not None and 
                            self.dragging_card and can_interact):
                            
                            mouse_pos = pygame.mouse.get_pos()
                            placed = False

                            for key, y in self.LINES_Y.items():
                                line_rect = pygame.Rect(
                                    scale_value(50, 'x', self.SCALE_X, self.SCALE_Y),
                                    y,
                                    self.selected_width - scale_value(100, 'x', self.SCALE_X, self.SCALE_Y),
                                    self.LINE_HEIGHT
                                )

                                if player_key in key and line_rect.collidepoint(mouse_pos):

                                    self.send_action("place_card", {
                                        "card_index": self.selected_card_index,
                                        "line_key": key
                                    })
                                    placed = True
                                    self.reset_drag_state()
                                    break
                            
                            if not placed:

                                self.reset_drag_state()

                    elif event.type == pygame.KEYDOWN:
                        if self.chat_active:
                            if event.key == pygame.K_RETURN:
                                if self.chat_input.strip():
                                    self.send_action("chat_message", {
                                        "message": self.chat_input
                                    })
                                    self.chat_input = ""
                            elif event.key == pygame.K_BACKSPACE:
                                self.chat_input = self.chat_input[:-1]
                            elif event.key == pygame.K_ESCAPE:
                                self.chat_active = False
                                self.chat_input = ""
                            else:
                                if len(self.chat_input) < 50 and event.unicode.isprintable():
                                    self.chat_input += event.unicode
                        else:
                            if event.key == pygame.K_ESCAPE:
                                self.reset_drag_state()
                                self.zoomed_card = None
                            elif event.key == pygame.K_c and event.mod & pygame.KMOD_CTRL:
                                self.chat_active = True
            

            if not self.game_started:
                self.draw_lobby()
            elif self.game_state and self.game_state["game_over"]:
                self.draw_game_over()
            else:
                self.draw_game()
        
        self.stop_music()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    import os
    import sys
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        client = GameClient()
        client.run()
    except Exception as e:
        print(f"Ошибка запуска клиента: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")