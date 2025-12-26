from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import sys
import subprocess
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

class GameLauncher:
    def __init__(self):
        pygame.init()
        
        self.WIDTH = 600
        self.HEIGHT = 700 
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Гамбит - Лаунчер")
        
        # Цвета
        self.BG_COLOR = (34, 34, 34)
        self.BUTTON_COLOR = (50, 100, 150)
        self.BUTTON_HOVER = (70, 130, 180)
        self.TEXT_COLOR = (255, 255, 255)
        self.INPUT_BG = (60, 60, 60)
        self.INPUT_BORDER = (100, 150, 200)
        self.SETTINGS_COLOR = (150, 100, 50)
        self.SETTINGS_HOVER = (180, 130, 80)
        self.DECK_COLOR = (80, 150, 80)
        self.DECK_HOVER = (100, 180, 100)
        self.AUDIO_COLOR = (100, 50, 150)      
        self.AUDIO_HOVER = (130, 80, 180)      
        self.WARNING_COLOR = (200, 100, 50)
        
        # Шрифты
        try:
            font_path = os.path.join("fonts", "OFONT.RU_VINQUE RG.TTF")
            if not os.path.exists(font_path):
                font_path = os.path.join(current_dir, "fonts", "OFONT.RU_VINQUE RG.TTF")
            
            if os.path.exists(font_path):
                self.title_font = pygame.font.Font(font_path, 48)
                self.button_font = pygame.font.Font(font_path, 28)
                self.input_font = pygame.font.Font(font_path, 24)
                self.small_font = pygame.font.Font(font_path, 18)
                self.info_font = pygame.font.Font(font_path, 16)
                print(f"[LAUNCHER] Шрифт Vinque загружен: {font_path}")
            else:
                raise FileNotFoundError("Шрифт Vinque не найден")
        except Exception as e:
            print(f"[LAUNCHER] Ошибка загрузки шрифта Vinque: {e}. Используются стандартные шрифты.")
            self.title_font = pygame.font.SysFont("arial", 48, bold=True)
            self.button_font = pygame.font.SysFont("arial", 28)
            self.input_font = pygame.font.SysFont("arial", 24)
            self.small_font = pygame.font.SysFont("arial", 18)
            self.info_font = pygame.font.SysFont("arial", 16)
        
        # Состояние
        self.show_ip_input = False
        self.ip_address = "localhost"
        self.input_active = False
        self.server_started = False
        
        # Кнопки (расположены вертикально с промежутками)
        button_width = 300
        button_height = 50
        button_spacing = 60
        start_y = 100
        
        self.host_button = pygame.Rect(self.WIDTH//2 - button_width//2, start_y, button_width, button_height)
        self.join_button = pygame.Rect(self.WIDTH//2 - button_width//2, start_y + button_spacing, button_width, button_height)
        self.deck_button = pygame.Rect(self.WIDTH//2 - button_width//2, start_y + button_spacing*2, button_width, button_height)
        self.settings_button = pygame.Rect(self.WIDTH//2 - button_width//2, start_y + button_spacing*3, button_width, button_height)
        self.audio_button = pygame.Rect(self.WIDTH//2 - button_width//2, start_y + button_spacing*4, button_width, button_height)
        
        # Поле ввода IP
        self.ip_input_rect = pygame.Rect(self.WIDTH//2 - 150, 370, 300, 40)
        self.connect_button = pygame.Rect(self.WIDTH//2 - 75, 430, 150, 40)
        
        # Кнопка назад
        self.back_button = pygame.Rect(20, 20, 80, 40)
        
        # Информация о колоде
        self.deck_status = self.check_deck_status()
    
    def check_deck_status(self):
        """Проверка состояния колоды"""
        deck_path = os.path.join(current_dir, "my_deck.json")
        
        if not os.path.exists(deck_path):
            return {
                "exists": False,
                "count": 0,
                "valid": False,
                "message": "Колода не создана"
            }
        
        try:
            with open(deck_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Проверяем разные форматы
            if isinstance(data, dict) and "cards" in data:
                cards = data["cards"]
            elif isinstance(data, list):
                cards = data
            else:
                return {
                    "exists": True,
                    "count": 0,
                    "valid": False,
                    "message": "Неверный формат колоды"
                }
            
            count = len(cards)
            valid = (count == 20)
            
            return {
                "exists": True,
                "count": count,
                "valid": valid,
                "message": f"Карт: {count}/20"
            }
            
        except Exception as e:
            print(f"[LAUNCHER] Ошибка чтения колоды: {e}")
            return {
                "exists": True,
                "count": 0,
                "valid": False,
                "message": "Ошибка чтения файла"
            }
    
    def run_deck_creator(self):
        """Запуск конструктора колоды"""
        try:
            pygame.quit()
            
            from deck_creator import DeckCreator
            creator = DeckCreator()
            cards_count = creator.run()
            
            self.deck_status = self.check_deck_status()

            self.__init__()
            self.run()
            
        except Exception as e:
            print(f"[LAUNCHER] Ошибка запуска конструктора колоды: {e}")
            import traceback
            traceback.print_exc()
            self.__init__()
            self.run()
    
    def draw(self):
        """Отрисовка интерфейса лаунчера"""
        self.screen.fill(self.BG_COLOR)
        
        # Заголовок
        title = self.title_font.render("Гамбит", True, (220, 220, 60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 10))
        
        # Подзаголовок
        subtitle = self.info_font.render("Карточная стратегия", True, (180, 180, 220))
        self.screen.blit(subtitle, (self.WIDTH//2 - subtitle.get_width()//2, 70))
        
        if not self.show_ip_input:
            # Основное меню
            mouse_pos = pygame.mouse.get_pos()
            
            # Кнопка "Хост сервера"
            host_color = self.BUTTON_HOVER if self.host_button.collidepoint(mouse_pos) else self.BUTTON_COLOR
            pygame.draw.rect(self.screen, host_color, self.host_button, border_radius=8)
            pygame.draw.rect(self.screen, (100, 150, 200), self.host_button, 3, border_radius=8)
            
            host_text = self.button_font.render("Хост сервера", True, self.TEXT_COLOR)
            self.screen.blit(host_text, (self.host_button.centerx - host_text.get_width()//2,
                                       self.host_button.centery - host_text.get_height()//2))
            
            # Кнопка "Присоединиться к игре"
            join_color = self.BUTTON_HOVER if self.join_button.collidepoint(mouse_pos) else self.BUTTON_COLOR
            pygame.draw.rect(self.screen, join_color, self.join_button, border_radius=8)
            pygame.draw.rect(self.screen, (100, 150, 200), self.join_button, 3, border_radius=8)
            
            join_text = self.button_font.render("Присоединиться к игре", True, self.TEXT_COLOR)
            self.screen.blit(join_text, (self.join_button.centerx - join_text.get_width()//2,
                                       self.join_button.centery - join_text.get_height()//2))
            
            # Кнопка "Конструктор колоды"
            deck_color = self.DECK_HOVER if self.deck_button.collidepoint(mouse_pos) else self.DECK_COLOR
            pygame.draw.rect(self.screen, deck_color, self.deck_button, border_radius=8)
            pygame.draw.rect(self.screen, (120, 190, 120), self.deck_button, 3, border_radius=8)
            
            deck_text = self.button_font.render("Конструктор колоды", True, self.TEXT_COLOR)
            self.screen.blit(deck_text, (self.deck_button.centerx - deck_text.get_width()//2,
                                       self.deck_button.centery - deck_text.get_height()//2))
            
            # Кнопка "Настройки отображения"
            settings_color = self.SETTINGS_HOVER if self.settings_button.collidepoint(mouse_pos) else self.SETTINGS_COLOR
            pygame.draw.rect(self.screen, settings_color, self.settings_button, border_radius=8)
            pygame.draw.rect(self.screen, (180, 150, 100), self.settings_button, 2, border_radius=8)
            
            settings_text = self.button_font.render("Настройки отображения", True, self.TEXT_COLOR)
            self.screen.blit(settings_text, (self.settings_button.centerx - settings_text.get_width()//2,
                                           self.settings_button.centery - settings_text.get_height()//2))
            
            # Кнопка "Настройки звука"
            audio_color = self.AUDIO_HOVER if self.audio_button.collidepoint(mouse_pos) else self.AUDIO_COLOR
            pygame.draw.rect(self.screen, audio_color, self.audio_button, border_radius=8)
            pygame.draw.rect(self.screen, (150, 100, 200), self.audio_button, 2, border_radius=8)
            
            audio_text = self.button_font.render("Настройки звука", True, self.TEXT_COLOR)
            self.screen.blit(audio_text, (self.audio_button.centerx - audio_text.get_width()//2,
                                        self.audio_button.centery - audio_text.get_height()//2))
            
            # Статус колоды
            status_y = self.audio_button.bottom + 20
            status_color = (100, 255, 100) if self.deck_status["valid"] else self.WARNING_COLOR
            status_text = self.info_font.render(f"Колода: {self.deck_status['message']}", True, status_color)
            self.screen.blit(status_text, (self.WIDTH//2 - status_text.get_width()//2, status_y))
            
            if not self.deck_status["valid"]:
                warning_y = status_y + 25
                warning_text = self.info_font.render("Нужно 20 карт для игры!", True, (255, 100, 100))
                self.screen.blit(warning_text, (self.WIDTH//2 - warning_text.get_width()//2, warning_y))
            
            # Информация о состоянии сервера
            server_y = self.HEIGHT - 60
            if self.server_started:
                status_text = self.info_font.render("Сервер запущен на localhost:5555", True, (100, 255, 100))
                self.screen.blit(status_text, (self.WIDTH//2 - status_text.get_width()//2, server_y))
            else:
                hint = self.info_font.render("Выберите действие", True, (180, 180, 220))
                self.screen.blit(hint, (self.WIDTH//2 - hint.get_width()//2, server_y))
            
        else:
            connect_title = self.button_font.render("Подключение к игре", True, (220, 220, 60))
            self.screen.blit(connect_title, (self.WIDTH//2 - connect_title.get_width()//2, 100))
            
            if not self.deck_status["valid"]:
                warning_rect = pygame.Rect(self.WIDTH//2 - 200, 200, 400, 60)
                pygame.draw.rect(self.screen, (80, 40, 40), warning_rect, border_radius=8)
                pygame.draw.rect(self.screen, (150, 80, 80), warning_rect, 2, border_radius=8)
                
                warning_text = self.button_font.render("Колода не готова!", True, (255, 200, 200))
                self.screen.blit(warning_text, (self.WIDTH//2 - warning_text.get_width()//2, 215))
                
                sub_warning = self.info_font.render("Создайте колоду из 20 карт", True, (255, 180, 180))
                self.screen.blit(sub_warning, (self.WIDTH//2 - sub_warning.get_width()//2, 245))
            
            # Поле ввода IP
            field_y = 280 if not self.deck_status["valid"] else 200
            self.ip_input_rect.y = field_y
            
            pygame.draw.rect(self.screen, self.INPUT_BG, self.ip_input_rect)
            border_color = self.INPUT_BORDER if self.input_active else (80, 80, 80)
            pygame.draw.rect(self.screen, border_color, self.ip_input_rect, 2)
            
            # Текст в поле ввода
            display_ip = self.ip_address
            if self.input_active and pygame.time.get_ticks() % 1000 > 500:
                display_ip += "|"
                
            ip_text = self.input_font.render(display_ip, True, self.TEXT_COLOR)
            self.screen.blit(ip_text, (self.ip_input_rect.x + 10, 
                                     self.ip_input_rect.y + self.ip_input_rect.height//2 - ip_text.get_height()//2))
            
            # Подсказка
            ip_hint = self.info_font.render("Введите IP-адрес сервера:", True, (200, 200, 200))
            self.screen.blit(ip_hint, (self.WIDTH//2 - ip_hint.get_width()//2, field_y - 30))
            
            # Кнопка "Подключиться"
            connect_y = field_y + 60
            self.connect_button.y = connect_y
            
            mouse_pos = pygame.mouse.get_pos()
            
            if not self.deck_status["valid"]:
                connect_color = (80, 80, 80)
                connect_border = (100, 100, 100)
                text_color = (150, 150, 150)
            else:
                connect_color = self.BUTTON_HOVER if self.connect_button.collidepoint(mouse_pos) else self.BUTTON_COLOR
                connect_border = (100, 150, 200)
                text_color = self.TEXT_COLOR
            
            pygame.draw.rect(self.screen, connect_color, self.connect_button, border_radius=8)
            pygame.draw.rect(self.screen, connect_border, self.connect_button, 2, border_radius=8)
            
            connect_text = self.input_font.render("Подключиться", True, text_color)
            self.screen.blit(connect_text, (self.connect_button.centerx - connect_text.get_width()//2,
                                          self.connect_button.centery - connect_text.get_height()//2))
            
            # Кнопка "Назад"
            back_color = (100, 100, 100) if self.back_button.collidepoint(mouse_pos) else (70, 70, 70)
            pygame.draw.rect(self.screen, back_color, self.back_button, border_radius=6)
            
            back_text = self.info_font.render("Назад", True, self.TEXT_COLOR)
            self.screen.blit(back_text, (self.back_button.centerx - back_text.get_width()//2,
                                       self.back_button.centery - back_text.get_height()//2))
            
            # Пример IP
            example = self.info_font.render("Пример: 26.143.147.118 или localhost", True, (150, 150, 180))
            self.screen.blit(example, (self.WIDTH//2 - example.get_width()//2, connect_y + 50))
            
            deck_status_y = connect_y + 80
            status_color = (100, 255, 100) if self.deck_status["valid"] else (255, 100, 100)
            deck_status_text = self.info_font.render(f"Колода: {self.deck_status['message']}", True, status_color)
            self.screen.blit(deck_status_text, (self.WIDTH//2 - deck_status_text.get_width()//2, deck_status_y))
        
        pygame.display.flip()
    
    def run_server(self):
        """Запуск сервера"""
        try:
            if not self.deck_status["valid"]:
                print("[LAUNCHER] Невозможно запустить сервер: колода не готова")
                return None
            
            env = os.environ.copy()
            env['PYTHONPATH'] = current_dir + os.pathsep + env.get('PYTHONPATH', '')

            server_process = subprocess.Popen(
                [sys.executable, "server.py"],
                cwd=current_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            print(f"[LAUNCHER] Сервер запущен с PID: {server_process.pid}")
            print(f"[LAUNCHER] Рабочая директория: {current_dir}")
            self.server_started = True
            return server_process
            
        except Exception as e:
            print(f"[LAUNCHER] Ошибка запуска сервера: {e}")
            return None
    
    def run_client(self, ip_address):
        """Запуск клиента"""
        try:
            if not self.deck_status["valid"]:
                print("[LAUNCHER] Невозможно подключиться: колода не готова")
                return
            
            pygame.quit()

            os.environ['GAME_SERVER_IP'] = ip_address

            from client import GameClient
            client = GameClient()
            client.run()
            
        except Exception as e:
            print(f"[LAUNCHER] Ошибка запуска клиента: {e}")
            import traceback
            traceback.print_exc()
            self.__init__()
            self.run()
    
    def run_settings(self):
        """Запуск настроек отображения"""
        try:
            pygame.quit()

            from settings import get_display_settings
            display_mode, resolution = get_display_settings()
            
            print(f"[LAUNCHER] Настройки отображения сохранены: {display_mode}, {resolution}")

            self.__init__()
            self.run()
            
        except Exception as e:
            print(f"[LAUNCHER] Ошибка запуска настроек: {e}")
            import traceback
            traceback.print_exc()
            self.__init__()
            self.run()
    
    def run_audio_settings(self):
        """Запуск настроек звука"""
        try:
            pygame.quit()
            
            from settings import get_audio_settings_screen
            audio_settings = get_audio_settings_screen()
            
            if audio_settings:
                print(f"[LAUNCHER] Настройки звука сохранены")

            self.__init__()
            self.run()
            
        except Exception as e:
            print(f"[LAUNCHER] Ошибка запуска настроек звука: {e}")
            import traceback
            traceback.print_exc()
            self.__init__()
            self.run()
    
    def run(self):
        """Основной цикл лаунчера"""
        clock = pygame.time.Clock()
        server_process = None
        
        while True:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if server_process:
                        server_process.terminate()
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if not self.show_ip_input:
                        # Основное меню
                        if self.host_button.collidepoint(mouse_pos):
                            if self.deck_status["valid"]:
                                server_process = self.run_server()
                            else:
                                print("[LAUNCHER] Сначала создайте колоду из 20 карт!")
                            
                        elif self.join_button.collidepoint(mouse_pos):
                            self.show_ip_input = True
                            self.input_active = True
                            
                        elif self.deck_button.collidepoint(mouse_pos):
                            self.run_deck_creator()
                            
                        elif self.settings_button.collidepoint(mouse_pos):
                            self.run_settings()
                            
                        elif self.audio_button.collidepoint(mouse_pos):
                            self.run_audio_settings()
                    
                    else:
                        # Экран подключения
                        if self.back_button.collidepoint(mouse_pos):
                            self.show_ip_input = False
                            self.input_active = False
                            
                        elif self.ip_input_rect.collidepoint(mouse_pos):
                            self.input_active = True
                            
                        elif self.connect_button.collidepoint(mouse_pos):
                            if self.ip_address.strip() and self.deck_status["valid"]:
                                self.run_client(self.ip_address.strip())
                                
                        else:
                            self.input_active = False
                
                if event.type == pygame.KEYDOWN and self.input_active:
                    if event.key == pygame.K_RETURN:
                        if self.ip_address.strip() and self.deck_status["valid"]:
                            self.run_client(self.ip_address.strip())
                            
                    elif event.key == pygame.K_BACKSPACE:
                        self.ip_address = self.ip_address[:-1]
                        
                    elif event.key == pygame.K_ESCAPE:
                        self.show_ip_input = False
                        self.input_active = False
                        
                    else:
                        if len(self.ip_address) < 20 and event.unicode.isprintable():
                            self.ip_address += event.unicode
            
            self.draw()

if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()