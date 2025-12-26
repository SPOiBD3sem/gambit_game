from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import json
import os
import sys
import time

# Добавляем текущую директорию в путь для импорта cards.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from cards import cards_list, Card, get_asset_path
except ImportError:
    # Если не удалось импортировать, создаем заглушку
    print("[DECK_CREATOR] Ошибка импорта cards.py. Используются тестовые данные.")
    
    # Тестовые карты для демонстрации
    class Card:
        def __init__(self, name, power, image_path=None, ability=None, allowed_lines=None):
            self.name = name
            self.power = power
            self.image_path = image_path or f"{name.lower().replace(' ', '_')}.png"
            self.ability = ability
            self.allowed_lines = allowed_lines or ["front"]
    
    # Тестовый список карт
    cards_list = [
        Card("Ведьмак", 10, allowed_lines=["front"]),
        Card("Каменный голем", 8, allowed_lines=["front"]),
        Card("Элитный рыцарь", 5, allowed_lines=["front"]),
        Card("Лучник", 5, allowed_lines=["back"]),
        Card("Арбалетчик", 5, allowed_lines=["back"]),
        Card("Инженер", 1, allowed_lines=["back"]),
        Card("Огненный маг", 5, allowed_lines=["back"]),
        Card("Ледяной маг", 5, allowed_lines=["back"]),
        Card("Дракон", 8, allowed_lines=["back"]),
        Card("Гном", 1, allowed_lines=["back"]),
        Card("Мудрый дуб", 2, allowed_lines=["back"]),
        Card("Крестьянин", 6, allowed_lines=["front"]),
        Card("Зверобой", 4, allowed_lines=["front"]),
        Card("Чародейка", 7, allowed_lines=["back"]),
        Card("Нордлинг", 8, allowed_lines=["front"]),
        Card("Ручной медведь", 8, allowed_lines=["front"]),
        Card("Требушет", 8, allowed_lines=["back"]),
        Card("Драккар", 5, allowed_lines=["front"]),
        Card("Мгла", 0, allowed_lines=["back"]),
        Card("Стужа", 0, allowed_lines=["front"]),
        Card("Бард", 3, allowed_lines=["front"]),
        Card("Химик", 4, allowed_lines=["back"]),
        Card("Бродяга", 3, allowed_lines=["front"]),
        Card("Страж леса", 4, allowed_lines=["back"]),
        Card("Лучница из племени", 3, allowed_lines=["back"]),
        Card("Ворон", 4, allowed_lines=["back"]),
        Card("Луналикая", 6, allowed_lines=["back"]),
        Card("Разбойник", 7, allowed_lines=["front"]),
        Card("Химера", 4, allowed_lines=["front"]),
        Card("Сигнальные огни", 0, allowed_lines=["front"])
    ]
    
    def get_asset_path(filename):
        return os.path.join("assets", filename)

class DeckCreator:
    def __init__(self):
        pygame.init()
        
        # Настройки окна
        self.WIDTH = 1200
        self.HEIGHT = 800
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Конструктор колоды - Гамбит")
        
        # Цвета
        self.BG_COLOR = (30, 30, 40)
        self.CARD_BG = (40, 40, 55)
        self.CARD_BORDER = (80, 80, 100)
        self.HIGHLIGHT_COLOR = (220, 220, 60)
        self.TEXT_COLOR = (255, 255, 255)
        self.STATUS_COLOR = (180, 180, 220)
        self.DECK_COLOR = (60, 80, 40)
        self.DECK_BORDER = (100, 140, 60)
        self.BUTTON_COLOR = (70, 100, 150)
        self.BUTTON_HOVER = (100, 140, 190)
        self.REMOVE_COLOR = (150, 60, 60)
        self.REMOVE_HOVER = (190, 80, 80)
        self.STAT_COLOR = (100, 200, 255)
        self.WARNING_COLOR = (255, 150, 50)
        self.SCROLLBAR_COLOR = (80, 80, 100)
        self.SCROLLBAR_HOVER = (100, 100, 120)
        self.SCROLLBAR_THUMB = (120, 120, 140)
        
        # Шрифты
        try:
            # Пробуем найти шрифт Vinque
            font_paths = [
                os.path.join("fonts", "OFONT.RU_VINQUE RG.TTF"),
                os.path.join(current_dir, "fonts", "OFONT.RU_VINQUE RG.TTF"),
                "OFONT.RU_VINQUE RG.TTF",
                os.path.join("assets", "fonts", "OFONT.RU_VINQUE RG.TTF")
            ]
            
            font_found = False
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    font_found = True
                    break
            
            if font_found:
                self.title_font = pygame.font.Font(font_path, 40)
                self.card_font = pygame.font.Font(font_path, 20)
                self.small_font = pygame.font.Font(font_path, 16)
                self.status_font = pygame.font.Font(font_path, 24)
                self.stat_font = pygame.font.Font(font_path, 14)
                print(f"[DECK_CREATOR] Шрифт Vinque загружен: {font_path}")
            else:
                raise FileNotFoundError("Шрифт Vinque не найден")
        except:
            print("[DECK_CREATOR] Используются системные шрифты")
            self.title_font = pygame.font.SysFont("arial", 40, bold=True)
            self.card_font = pygame.font.SysFont("arial", 20)
            self.small_font = pygame.font.SysFont("arial", 16)
            self.status_font = pygame.font.SysFont("arial", 24, bold=True)
            self.stat_font = pygame.font.SysFont("arial", 14)
        
        # Размеры карт
        self.CARD_WIDTH = 160
        self.CARD_HEIGHT = 220
        self.DECK_CARD_WIDTH = 280
        self.DECK_CARD_HEIGHT = 50
        self.ZOOMED_WIDTH = 400
        self.ZOOMED_HEIGHT = 550
        
        # Позиции и параметры
        self.deck_panel_width = 380
        self.cards_per_page = 6
        self.current_page = 0
        
        # Данные
        self.all_cards = cards_list
        self.deck_cards = []
        
        # Загрузка изображений карт
        self.card_images = {}
        self.original_card_images = {}
        self.load_card_images()
        
        # Загрузка существующей колоды
        self.load_existing_deck()
        
        # Состояние
        self.zoomed_card = None
        self.show_remove_hint = False
        self.selected_for_removal = None
        self.remove_confirm_time = 0
        self.last_warning_time = 0
        self.warning_message = ""
        
        # Скроллбар для колоды
        self.deck_scroll_offset = 0
        self.deck_scroll_dragging = False
        self.scrollbar_rect = None
        self.scrollbar_thumb_rect = None
        
        # Кнопки
        self.prev_button = pygame.Rect(50, self.HEIGHT - 100, 120, 40)
        self.next_button = pygame.Rect(190, self.HEIGHT - 100, 120, 40)
        self.save_button = pygame.Rect(self.WIDTH - 200, self.HEIGHT - 100, 180, 40)
        self.clear_button = pygame.Rect(self.WIDTH - 400, self.HEIGHT - 100, 180, 40)
        
        print(f"[DECK_CREATOR] Загружено {len(self.all_cards)} карт")
        print(f"[DECK_CREATOR] В колоде: {len(self.deck_cards)}/20 карт")
    
    def load_card_images(self):
        """Загрузка изображений карт"""
        print("[DECK_CREATOR] Загрузка изображений карт...")
        
        for card in self.all_cards:
            try:
                # Получаем путь к изображению
                if hasattr(card, 'image_path'):
                    image_path = card.image_path
                else:
                    image_path = get_asset_path(f"{card.name.lower().replace(' ', '_')}.png")
                
                # Пробуем разные пути
                possible_paths = [
                    image_path,
                    os.path.join("assets", os.path.basename(image_path)),
                    os.path.join(current_dir, "assets", os.path.basename(image_path)),
                    os.path.join("assets", "cards", os.path.basename(image_path)),
                    os.path.join(current_dir, "assets", "cards", os.path.basename(image_path)),
                ]
                
                img_loaded = False
                for path in possible_paths:
                    if os.path.exists(path):
                        try:
                            img = pygame.image.load(path)
                            
                            # Сохраняем оригинальное изображение для увеличения
                            self.original_card_images[card.name] = img
                            
                            # Масштабируем для галереи
                            scaled_img = pygame.transform.scale(img, (self.CARD_WIDTH, self.CARD_HEIGHT))
                            self.card_images[card.name] = scaled_img
                            
                            img_loaded = True
                            print(f"[DECK_CREATOR] Загружено: {card.name} из {path}")
                            break
                        except Exception as e:
                            print(f"[DECK_CREATOR] Ошибка загрузки {path}: {e}")
                            continue
                
                if not img_loaded:
                    # Создаем заглушку
                    print(f"[DECK_CREATOR] Создана заглушка для: {card.name}")
                    self.create_card_placeholder(card)
                    
            except Exception as e:
                print(f"[DECK_CREATOR] Ошибка обработки карты {card.name}: {e}")
                self.create_card_placeholder(card)
        
        print(f"[DECK_CREATOR] Загружено {len(self.card_images)} изображений")
    
    def create_card_placeholder(self, card):
        """Создание заглушки для карты"""
        surface = pygame.Surface((self.CARD_WIDTH, self.CARD_HEIGHT))
        
        # Цвет на основе силы карты
        if card.power >= 8:
            color = (100, 50, 50)
        elif card.power >= 5:
            color = (50, 50, 100)
        elif card.power >= 3:
            color = (50, 100, 50)
        else:
            color = (80, 80, 80)
        
        surface.fill(color)
        
        # Рамка
        pygame.draw.rect(surface, (200, 200, 200), surface.get_rect(), 3)
        
        # Название карты
        font = pygame.font.SysFont("arial", 18)
        name_text = font.render(card.name[:12], True, (255, 255, 255))
        surface.blit(name_text, (self.CARD_WIDTH//2 - name_text.get_width()//2, 
                            self.CARD_HEIGHT//2 - name_text.get_height()//2 - 20))
        
        # Сила карты
        power_text = font.render(f"Сила: {card.power}", True, (255, 255, 150))
        surface.blit(power_text, (self.CARD_WIDTH//2 - power_text.get_width()//2, 
                            self.CARD_HEIGHT//2 - power_text.get_height()//2 + 20))
        
        self.card_images[card.name] = surface
        self.original_card_images[card.name] = surface
    
    def load_existing_deck(self):
        """Загрузка существующей колоды из файла"""
        deck_path = os.path.join(current_dir, "my_deck.json")
        
        if os.path.exists(deck_path):
            try:
                with open(deck_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, dict) and "cards" in data:
                        self.deck_cards = data["cards"]
                    elif isinstance(data, list):
                        self.deck_cards = data
                    else:
                        print("[DECK_CREATOR] Неизвестный формат файла колоды")
                        self.deck_cards = []
                
                print(f"[DECK_CREATOR] Загружено {len(self.deck_cards)} карт из файла")
                
                # Проверяем, что все карты существуют
                valid_cards = []
                for card_name in self.deck_cards:
                    if any(card.name == card_name for card in self.all_cards):
                        valid_cards.append(card_name)
                    else:
                        print(f"[DECK_CREATOR] Предупреждение: карта '{card_name}' не найдена")
                
                self.deck_cards = valid_cards
                
            except Exception as e:
                print(f"[DECK_CREATOR] Ошибка загрузки колоды: {e}")
                self.deck_cards = []
        else:
            print("[DECK_CREATOR] Файл колоды не найден. Создаем новую колоду.")
    
    def save_deck(self):
        """Сохранение колоды в файл"""
        deck_path = os.path.join(current_dir, "my_deck.json")
        
        try:
            deck_data = {
                "deck_name": "Моя колода",
                "cards": self.deck_cards
            }
            
            with open(deck_path, 'w', encoding='utf-8') as f:
                json.dump(deck_data, f, ensure_ascii=False, indent=2)
            
            print(f"[DECK_CREATOR] Колода сохранена: {len(self.deck_cards)} карт")
            return True
            
        except Exception as e:
            print(f"[DECK_CREATOR] Ошибка сохранения колоды: {e}")
            return False
    
    def clear_deck(self):
        """Очистка колоды"""
        self.deck_cards = []
        self.deck_scroll_offset = 0
        print("[DECK_CREATOR] Колода очищена")
    
    def show_warning(self, message):
        """Показать предупреждение"""
        self.warning_message = message
        self.last_warning_time = time.time()
        print(f"[DECK_CREATOR] Предупреждение: {message}")
    
    def get_card_stats(self):
        """Получение статистики по колоде"""
        stats = {
            "total_cards": len(self.deck_cards),
            "total_power": 0,
            "avg_power": 0,
            "unique_cards": len(set(self.deck_cards))
        }
        
        for card_name in self.deck_cards:
            for card in self.all_cards:
                if card.name == card_name:
                    stats["total_power"] += card.power
                    break
        
        if stats["total_cards"] > 0:
            stats["avg_power"] = stats["total_power"] / stats["total_cards"]
        
        return stats
    
    def get_current_page_cards(self):
        """Получение карт для текущей страницы"""
        start_idx = self.current_page * self.cards_per_page
        end_idx = start_idx + self.cards_per_page
        return self.all_cards[start_idx:end_idx]
    
    def get_total_pages(self):
        """Получение общего количества страниц"""
        return (len(self.all_cards) + self.cards_per_page - 1) // self.cards_per_page
    
    def add_to_deck(self, card_name):
        """Добавление карты в колоду (без дубликатов)"""
        if len(self.deck_cards) >= 20:
            self.show_warning("Колода уже полна (20 карт)")
            return False
        
        if not any(card.name == card_name for card in self.all_cards):
            self.show_warning(f"Карта '{card_name}' не найдена")
            return False
        
        # ПРОВЕРКА ДУБЛИКАТОВ
        if card_name in self.deck_cards:
            self.show_warning(f"Карта '{card_name}' уже есть в колоде!")
            return False
        
        self.deck_cards.append(card_name)
        print(f"[DECK_CREATOR] Добавлена карта: {card_name} ({len(self.deck_cards)}/20)")
        return True
    
    def remove_from_deck(self, card_index):
        """Удаление карты из колоды"""
        if 0 <= card_index < len(self.deck_cards):
            removed_card = self.deck_cards.pop(card_index)
            print(f"[DECK_CREATOR] Удалена карта: {removed_card} ({len(self.deck_cards)}/20)")
            self.selected_for_removal = None
            self.show_remove_hint = False
            
            # Корректируем скролл если нужно
            visible_cards = (self.deck_panel_rect.height - 70) // self.DECK_CARD_HEIGHT
            if card_index < self.deck_scroll_offset:
                self.deck_scroll_offset = max(0, self.deck_scroll_offset - 1)
            elif card_index >= self.deck_scroll_offset + visible_cards:
                pass
            else:
                pass
            
            return True
        return False
    
    def draw_card_in_gallery(self, card, x, y):
        """Отрисовка карты в галерее"""
        mouse_pos = pygame.mouse.get_pos()
        card_rect = pygame.Rect(x, y, self.CARD_WIDTH, self.CARD_HEIGHT)
        
        # Проверяем, есть ли карта в колоде
        in_deck = card.name in self.deck_cards
        
        # Отображаем изображение карты если есть
        if card.name in self.card_images:
            card_image = self.card_images[card.name]
            self.screen.blit(card_image, card_rect)
            
            # Добавляем оверлей если в колоде
            if in_deck:
                overlay = pygame.Surface((self.CARD_WIDTH, self.CARD_HEIGHT), pygame.SRCALPHA)
                overlay.fill((100, 255, 100, 80))
                self.screen.blit(overlay, card_rect)
        else:
            # Рисуем простую карту
            color = self.DECK_COLOR if in_deck else self.CARD_BG
            pygame.draw.rect(self.screen, color, card_rect, border_radius=8)
            
            # Рамка
            border_color = self.DECK_BORDER if in_deck else self.CARD_BORDER
            if card_rect.collidepoint(mouse_pos):
                border_color = self.HIGHLIGHT_COLOR
                border_width = 3
            else:
                border_width = 2
            
            pygame.draw.rect(self.screen, border_color, card_rect, border_width, border_radius=8)
            
            # Название карты
            name_text = self.card_font.render(card.name[:12], True, self.TEXT_COLOR)
            self.screen.blit(name_text, (x + 10, y + 10))
            
            # Сила карты
            power_text = self.card_font.render(f"Сила: {card.power}", True, (255, 255, 200))
            self.screen.blit(power_text, (x + 10, y + 40))
        
        # Если карта в колоде, показываем зеленую галочку
        if in_deck:
            check_size = 30
            check_rect = pygame.Rect(x + self.CARD_WIDTH - check_size - 5, y + 5, check_size, check_size)
            pygame.draw.rect(self.screen, (50, 150, 50), check_rect, border_radius=15)
            pygame.draw.rect(self.screen, (100, 255, 100), check_rect, 2, border_radius=15)
            
            # Галочка
            check_points = [
                (check_rect.left + 8, check_rect.centery),
                (check_rect.left + 13, check_rect.centery + 5),
                (check_rect.right - 8, check_rect.top + 8)
            ]
            pygame.draw.lines(self.screen, (255, 255, 200), False, check_points, 3)
        
        return card_rect
    
    def draw_card_in_deck_list(self, card_name, x, y, index):
        """Отрисовка карты в списке колоды (только текст)"""
        mouse_pos = pygame.mouse.get_pos()
        card_rect = pygame.Rect(x, y, self.DECK_CARD_WIDTH, self.DECK_CARD_HEIGHT)
        
        # Ищем объект карты
        card_obj = None
        for card in self.all_cards:
            if card.name == card_name:
                card_obj = card
                break
        
        # Фон элемента списка
        if index == self.selected_for_removal:
            bg_color = (100, 40, 40)
        elif card_rect.collidepoint(mouse_pos):
            bg_color = (70, 90, 50)
        else:
            bg_color = (50, 70, 30)
        
        pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=6)
        pygame.draw.rect(self.screen, (100, 140, 60), card_rect, 2, border_radius=6)
        
        # Номер карты
        index_text = self.small_font.render(f"#{index + 1}", True, (255, 255, 150))
        self.screen.blit(index_text, (x + 10, y + self.DECK_CARD_HEIGHT//2 - index_text.get_height()//2))
        
        # Название карты (обрезаем если длинное)
        max_name_width = self.DECK_CARD_WIDTH - 120  # Оставляем место для силы и крестика
        name_display = card_name
        name_text = self.card_font.render(name_display, True, self.TEXT_COLOR)
        
        # Если текст слишком длинный, обрезаем
        if name_text.get_width() > max_name_width:
            # Пробуем найти подходящую длину
            for length in range(len(card_name), 0, -1):
                test_name = card_name[:length] + "..."
                test_text = self.card_font.render(test_name, True, self.TEXT_COLOR)
                if test_text.get_width() <= max_name_width:
                    name_display = test_name
                    break
            else:
                name_display = card_name[:10] + "..."
        
        name_text = self.card_font.render(name_display, True, self.TEXT_COLOR)
        name_x = x + 50
        self.screen.blit(name_text, (name_x, y + self.DECK_CARD_HEIGHT//2 - name_text.get_height()//2))
        
        # Сила карты
        if card_obj:
            power_x = x + self.DECK_CARD_WIDTH - 60
            power_text = self.card_font.render(f"{card_obj.power}", True, (255, 255, 200))
            self.screen.blit(power_text, (power_x, y + self.DECK_CARD_HEIGHT//2 - power_text.get_height()//2))
        
        # Кнопка удаления (крестик)
        remove_rect = pygame.Rect(x + self.DECK_CARD_WIDTH - 30, y + 15, 20, 20)
        
        if index == self.selected_for_removal:
            pygame.draw.rect(self.screen, (255, 100, 100), remove_rect, border_radius=4)
            pygame.draw.rect(self.screen, (255, 200, 200), remove_rect, 2, border_radius=4)
        else:
            remove_color = self.REMOVE_HOVER if remove_rect.collidepoint(mouse_pos) else self.REMOVE_COLOR
            pygame.draw.rect(self.screen, remove_color, remove_rect, border_radius=4)
        
        # Крестик
        pygame.draw.line(self.screen, (255, 255, 255), 
                        (remove_rect.left + 5, remove_rect.top + 5),
                        (remove_rect.right - 5, remove_rect.bottom - 5), 2)
        pygame.draw.line(self.screen, (255, 255, 255),
                        (remove_rect.right - 5, remove_rect.top + 5),
                        (remove_rect.left + 5, remove_rect.bottom - 5), 2)
        
        return card_rect, remove_rect
    
    def update_scrollbar(self, deck_panel_rect):
        """Обновление скроллбара"""
        # Вычисляем видимое количество карт
        visible_height = deck_panel_rect.height - 70
        max_visible_cards = visible_height // self.DECK_CARD_HEIGHT
        total_cards = len(self.deck_cards)
        
        if total_cards <= max_visible_cards:
            # Все карты видны, скроллбар не нужен
            self.scrollbar_rect = None
            self.scrollbar_thumb_rect = None
            self.deck_scroll_offset = 0
            return
        
        # Ограничиваем скролл
        max_scroll = total_cards - max_visible_cards
        self.deck_scroll_offset = max(0, min(self.deck_scroll_offset, max_scroll))
        
        # Создаем скроллбар
        scrollbar_width = 10
        scrollbar_x = deck_panel_rect.right - scrollbar_width - 5
        self.scrollbar_rect = pygame.Rect(
            scrollbar_x,
            deck_panel_rect.top + 50,
            scrollbar_width,
            visible_height
        )
        
        # Вычисляем размер и положение бегунка
        thumb_height = max(30, visible_height * max_visible_cards // total_cards)
        thumb_y = self.scrollbar_rect.top + (self.deck_scroll_offset * (visible_height - thumb_height) // max_scroll)
        
        self.scrollbar_thumb_rect = pygame.Rect(
            scrollbar_x,
            thumb_y,
            scrollbar_width,
            thumb_height
        )
    
    def draw_scrollbar(self):
        """Отрисовка скроллбара"""
        if self.scrollbar_rect:
            # Фон скроллбара
            pygame.draw.rect(self.screen, self.SCROLLBAR_COLOR, self.scrollbar_rect, border_radius=5)
            
            # Бегунок
            mouse_pos = pygame.mouse.get_pos()
            thumb_color = self.SCROLLBAR_HOVER if self.scrollbar_thumb_rect.collidepoint(mouse_pos) else self.SCROLLBAR_THUMB
            pygame.draw.rect(self.screen, thumb_color, self.scrollbar_thumb_rect, border_radius=5)
            
            # Края бегунка
            pygame.draw.rect(self.screen, (150, 150, 170), self.scrollbar_thumb_rect, 2, border_radius=5)
    
    def draw_zoomed_card(self):
        """Отрисовка увеличенной карты (оригинальное качество)"""
        if not self.zoomed_card:
            return
        
        # Полупрозрачный фон
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Центральная панель
        panel_width = self.ZOOMED_WIDTH + 100
        panel_height = self.ZOOMED_HEIGHT + 150
        panel_rect = pygame.Rect(
            self.WIDTH // 2 - panel_width // 2,
            self.HEIGHT // 2 - panel_height // 2,
            panel_width,
            panel_height
        )
        
        pygame.draw.rect(self.screen, (50, 50, 70), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 140), panel_rect, 3, border_radius=10)
        
        # Увеличенная карта - используем оригинальное изображение
        if isinstance(self.zoomed_card, Card) and self.zoomed_card.name in self.original_card_images:
            original_img = self.original_card_images[self.zoomed_card.name]
            
            # Рассчитываем размеры для сохранения пропорций
            img_width, img_height = original_img.get_size()
            ratio = min(self.ZOOMED_WIDTH / img_width, self.ZOOMED_HEIGHT / img_height)
            display_width = int(img_width * ratio)
            display_height = int(img_height * ratio)
            
            # Масштабируем с сохранением пропорций
            display_img = pygame.transform.scale(original_img, (display_width, display_height))
            
            # Центрируем
            card_x = self.WIDTH // 2 - display_width // 2
            card_y = panel_rect.top + 40
            
            self.screen.blit(display_img, (card_x, card_y))
            
            # Сохраняем прямоугольник для кликов
            card_rect = pygame.Rect(card_x, card_y, display_width, display_height)
        else:
            # Рисуем простую карту если нет изображения
            card_x = self.WIDTH // 2 - self.ZOOMED_WIDTH // 2
            card_y = panel_rect.top + 40
            card_rect = pygame.Rect(card_x, card_y, self.ZOOMED_WIDTH, self.ZOOMED_HEIGHT)
            
            pygame.draw.rect(self.screen, self.CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(self.screen, self.HIGHLIGHT_COLOR, card_rect, 3, border_radius=8)
            
            name = self.zoomed_card if isinstance(self.zoomed_card, str) else self.zoomed_card.name
            name_text = self.card_font.render(name, True, self.HIGHLIGHT_COLOR)
            self.screen.blit(name_text, (card_rect.centerx - name_text.get_width() // 2, 
                                       card_rect.centery - 20))
        
        # Информация о карте
        name = self.zoomed_card if isinstance(self.zoomed_card, str) else self.zoomed_card.name
        
        # Название (вверху панели)
        name_text = self.title_font.render(name, True, self.HIGHLIGHT_COLOR)
        self.screen.blit(name_text, (self.WIDTH // 2 - name_text.get_width() // 2, 
                                   panel_rect.top + 10))
        
        # Детали (только для объектов Card)
        if isinstance(self.zoomed_card, Card):
            info_y = card_rect.bottom + 20
            
            # Сила
            power_text = self.card_font.render(f"Сила: {self.zoomed_card.power}", True, (255, 255, 200))
            self.screen.blit(power_text, (self.WIDTH // 2 - power_text.get_width() // 2, info_y))
            info_y += 30
            
            # Разрешенные линии
            lines_text = self.card_font.render(f"Линии: {', '.join(self.zoomed_card.allowed_lines)}", 
                                             True, (200, 200, 255))
            self.screen.blit(lines_text, (self.WIDTH // 2 - lines_text.get_width() // 2, info_y))
            info_y += 30
            
            # Способность
            if self.zoomed_card.ability:
                ability_text = self.card_font.render("Имеет способность", True, (255, 200, 200))
            else:
                ability_text = self.card_font.render("Без способности", True, (200, 200, 200))
            self.screen.blit(ability_text, (self.WIDTH // 2 - ability_text.get_width() // 2, info_y))
        
        # Инструкция
        instr_text = self.small_font.render("Нажмите ESC или кликните для закрытия", True, (150, 150, 180))
        self.screen.blit(instr_text, (self.WIDTH // 2 - instr_text.get_width() // 2, 
                                    panel_rect.bottom - 30))
        
        return card_rect
    
    def draw(self):
        """Отрисовка всего интерфейса"""
        self.screen.fill(self.BG_COLOR)
        
        # Заголовок
        title = self.title_font.render("КОНСТРУКТОР КОЛОДЫ", True, self.HIGHLIGHT_COLOR)
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 20))
        
        # Статистика колоды (УБРАЛ "Передние карты")
        stats = self.get_card_stats()
        deck_status = f"КОЛОДА: {stats['total_cards']}/20 карт"
        status_color = (100, 255, 100) if stats['total_cards'] == 20 else self.STATUS_COLOR
        status_text = self.status_font.render(deck_status, True, status_color)
        self.screen.blit(status_text, (self.WIDTH - self.deck_panel_width // 2 - status_text.get_width() // 2, 80))
        
        # Упрощенная статистика
        if stats['total_cards'] > 0:
            stat_y = 110
            stat_texts = [
                f"Уникальных: {stats['unique_cards']}",
                f"Ср. сила: {stats['avg_power']:.1f}"
            ]
            
            for i, text in enumerate(stat_texts):
                stat_text = self.stat_font.render(text, True, self.STAT_COLOR)
                stat_x = self.WIDTH - self.deck_panel_width + 20 + i * 180
                self.screen.blit(stat_text, (stat_x, stat_y))
        
        # Панель колоды (правая часть) - ТОЛЬКО ТЕКСТ со скроллбаром
        self.deck_panel_rect = pygame.Rect(
            self.WIDTH - self.deck_panel_width,
            140 if stats['total_cards'] > 0 else 120,
            self.deck_panel_width - 20,
            self.HEIGHT - 260  # Увеличил высоту для подсказок
        )
        
        pygame.draw.rect(self.screen, (40, 50, 60), self.deck_panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (80, 100, 120), self.deck_panel_rect, 2, border_radius=10)
        
        # Заголовок панели колоды
        deck_title = self.card_font.render("ВАША КОЛОДА", True, (200, 220, 150))
        self.screen.blit(deck_title, (self.deck_panel_rect.centerx - deck_title.get_width() // 2, 
                                    self.deck_panel_rect.top + 10))
        
        # Обновляем скроллбар
        self.update_scrollbar(self.deck_panel_rect)
        
        # Список карт в колоде (ТОЛЬКО ТЕКСТ, со скроллом)
        if self.deck_cards:
            visible_height = self.deck_panel_rect.height - 70
            max_visible_cards = visible_height // self.DECK_CARD_HEIGHT
            
            # Определяем какие карты показывать
            start_index = self.deck_scroll_offset
            end_index = min(start_index + max_visible_cards, len(self.deck_cards))
            
            start_y = self.deck_panel_rect.top + 50
            
            for i in range(start_index, end_index):
                card_name = self.deck_cards[i]
                y_pos = start_y + (i - start_index) * self.DECK_CARD_HEIGHT
                
                # Отрисовываем карту как текстовый элемент
                self.draw_card_in_deck_list(
                    card_name, 
                    self.deck_panel_rect.left + 20, 
                    y_pos, 
                    i
                )
            
            # Если есть скроллбар, отрисовываем его
            self.draw_scrollbar()
            
            # Показываем сколько карт всего
            if len(self.deck_cards) > max_visible_cards:
                showing_text = self.small_font.render(
                    f"Показано {end_index - start_index} из {len(self.deck_cards)}", 
                    True, (180, 180, 180)
                )
                self.screen.blit(showing_text, (
                    self.deck_panel_rect.centerx - showing_text.get_width() // 2, 
                    self.deck_panel_rect.bottom - 25
                ))
        else:
            # Сообщение о пустой колоде
            empty_text = self.card_font.render("Колода пуста", True, (150, 150, 150))
            self.screen.blit(empty_text, (self.deck_panel_rect.centerx - empty_text.get_width() // 2, 
                                        self.deck_panel_rect.centery - empty_text.get_height() // 2))
            
            hint_text = self.small_font.render("Кликните по картам слева для добавления", True, (180, 180, 220))
            self.screen.blit(hint_text, (self.deck_panel_rect.centerx - hint_text.get_width() // 2, 
                                       self.deck_panel_rect.centery + 20))
        
        # Галерея карт (левая часть) - С ИЗОБРАЖЕНИЯМИ
        gallery_rect = pygame.Rect(
            20,
            120,
            self.WIDTH - self.deck_panel_width - 40,
            self.HEIGHT - 240
        )
        
        pygame.draw.rect(self.screen, (40, 50, 60), gallery_rect, border_radius=10)
        pygame.draw.rect(self.screen, (80, 100, 120), gallery_rect, 2, border_radius=10)
        
        # Заголовок галереи
        gallery_title = self.card_font.render("ВСЕ КАРТЫ", True, (150, 200, 255))
        self.screen.blit(gallery_title, (gallery_rect.centerx - gallery_title.get_width() // 2, 
                                       gallery_rect.top + 10))
        
        # Отображение карт текущей страницы (с изображениями)
        page_cards = self.get_current_page_cards()
        cards_per_row = 3
        card_spacing_x = (gallery_rect.width - cards_per_row * self.CARD_WIDTH) // (cards_per_row + 1)
        card_spacing_y = 30
        
        self.card_rects = []  # Сохраняем прямоугольники карт для обработки кликов
        
        for i, card in enumerate(page_cards):
            row = i // cards_per_row
            col = i % cards_per_row
            
            x = gallery_rect.left + card_spacing_x + col * (self.CARD_WIDTH + card_spacing_x)
            y = gallery_rect.top + 50 + row * (self.CARD_HEIGHT + card_spacing_y)
            
            # Отрисовываем карту с изображением
            card_rect = self.draw_card_in_gallery(card, x, y)
            self.card_rects.append((card_rect, card))
        
        # Пагинация
        page_text = self.small_font.render(f"Страница {self.current_page + 1} из {self.get_total_pages()}", 
                                         True, self.STATUS_COLOR)
        self.screen.blit(page_text, (gallery_rect.centerx - page_text.get_width() // 2, 
                                   gallery_rect.bottom + 10))
        
        # Кнопки навигации
        mouse_pos = pygame.mouse.get_pos()
        
        # Кнопка "Назад"
        prev_enabled = self.current_page > 0
        prev_color = self.BUTTON_HOVER if self.prev_button.collidepoint(mouse_pos) and prev_enabled else self.BUTTON_COLOR
        if not prev_enabled:
            prev_color = (80, 80, 80)
        
        pygame.draw.rect(self.screen, prev_color, self.prev_button, border_radius=6)
        pygame.draw.rect(self.screen, (100, 150, 200), self.prev_button, 2, border_radius=6)
        
        prev_text = self.card_font.render("Назад", True, self.TEXT_COLOR if prev_enabled else (120, 120, 120))
        self.screen.blit(prev_text, (self.prev_button.centerx - prev_text.get_width() // 2,
                                   self.prev_button.centery - prev_text.get_height() // 2))
        
        # Кнопка "Вперед"
        next_enabled = self.current_page < self.get_total_pages() - 1
        next_color = self.BUTTON_HOVER if self.next_button.collidepoint(mouse_pos) and next_enabled else self.BUTTON_COLOR
        if not next_enabled:
            next_color = (80, 80, 80)
        
        pygame.draw.rect(self.screen, next_color, self.next_button, border_radius=6)
        pygame.draw.rect(self.screen, (100, 150, 200), self.next_button, 2, border_radius=6)
        
        next_text = self.card_font.render("Вперед", True, self.TEXT_COLOR if next_enabled else (120, 120, 120))
        self.screen.blit(next_text, (self.next_button.centerx - next_text.get_width() // 2,
                                   self.next_button.centery - next_text.get_height() // 2))
        
        # Кнопка "Очистить колоду"
        clear_color = self.REMOVE_HOVER if self.clear_button.collidepoint(mouse_pos) else self.REMOVE_COLOR
        pygame.draw.rect(self.screen, clear_color, self.clear_button, border_radius=6)
        pygame.draw.rect(self.screen, (180, 100, 100), self.clear_button, 2, border_radius=6)
        
        clear_text = self.card_font.render("Очистить колоду", True, self.TEXT_COLOR)
        self.screen.blit(clear_text, (self.clear_button.centerx - clear_text.get_width() // 2,
                                    self.clear_button.centery - clear_text.get_height() // 2))
        
        # Кнопка "Сохранить и выйти"
        save_enabled = stats['total_cards'] == 20
        save_color = self.BUTTON_HOVER if self.save_button.collidepoint(mouse_pos) and save_enabled else self.BUTTON_COLOR
        if not save_enabled:
            save_color = (80, 80, 80)
        
        pygame.draw.rect(self.screen, save_color, self.save_button, border_radius=6)
        pygame.draw.rect(self.screen, (100, 150, 200), self.save_button, 2, border_radius=6)
        
        save_text = self.card_font.render("Сохранить и выйти", True, self.TEXT_COLOR if save_enabled else (120, 120, 120))
        self.screen.blit(save_text, (self.save_button.centerx - save_text.get_width() // 2,
                                   self.save_button.centery - save_text.get_height() // 2))
        
        # Подсказка об удалении
        if self.show_remove_hint and self.selected_for_removal is not None:
            hint_text = self.small_font.render("Нажмите еще раз для удаления карты", True, (255, 200, 100))
            self.screen.blit(hint_text, (self.WIDTH // 2 - hint_text.get_width() // 2, 
                                       self.HEIGHT - 130))
        
        # Показ предупреждений
        if time.time() - self.last_warning_time < 3:
            warning_bg = pygame.Surface((500, 40), pygame.SRCALPHA)
            warning_bg.fill((200, 100, 50, 200))
            warning_rect = warning_bg.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 160))
            self.screen.blit(warning_bg, warning_rect)
            
            warning_text = self.card_font.render(self.warning_message, True, (255, 255, 200))
            self.screen.blit(warning_text, (warning_rect.centerx - warning_text.get_width() // 2,
                                          warning_rect.centery - warning_text.get_height() // 2))
    
        hints_y = self.HEIGHT - 40
        
        hints = [
            "ЛКМ по карте - добавить в колоду",
            "ПКМ по карте - увеличить",
            "Клик по крестику - удалить из колоды"
        ]
        
        for i, hint in enumerate(hints):
            hint_text = self.small_font.render(hint, True, (180, 180, 180))
            hint_x = 20 + i * (self.WIDTH // 3)
            self.screen.blit(hint_text, (hint_x, hints_y))
        
        # Отображение увеличенной карты (поверх всего)
        if self.zoomed_card:
            self.draw_zoomed_card()
        
        pygame.display.flip()
    
    def run(self):
        """Основной цикл конструктора колоды"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            clock.tick(60)
            
            # Сброс подсказки об удалении через 2 секунды
            if self.show_remove_hint and time.time() - self.remove_confirm_time > 2:
                self.show_remove_hint = False
                self.selected_for_removal = None
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.zoomed_card:
                            self.zoomed_card = None
                        else:
                            running = False
                    elif event.key == pygame.K_LEFT:
                        if self.current_page > 0:
                            self.current_page -= 1
                    elif event.key == pygame.K_RIGHT:
                        if self.current_page < self.get_total_pages() - 1:
                            self.current_page += 1
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Проверка увеличенной карты
                    if self.zoomed_card:
                        if event.button == 1 or event.button == 3:
                            self.zoomed_card = None
                        continue
                    
                    # Обработка скроллбара
                    if event.button == 1 and self.scrollbar_thumb_rect and self.scrollbar_thumb_rect.collidepoint(mouse_pos):
                        self.deck_scroll_dragging = True
                        self.drag_start_y = mouse_pos[1]
                        self.drag_start_scroll = self.deck_scroll_offset
                        continue
                    
                    # Обработка клика по области скроллбара (но не по бегунку)
                    if event.button == 1 and self.scrollbar_rect and self.scrollbar_rect.collidepoint(mouse_pos):
                        if not self.scrollbar_thumb_rect.collidepoint(mouse_pos):
                            # Клик выше бегунка - прокрутка вверх
                            if mouse_pos[1] < self.scrollbar_thumb_rect.top:
                                visible_height = self.deck_panel_rect.height - 70
                                max_visible_cards = visible_height // self.DECK_CARD_HEIGHT
                                self.deck_scroll_offset = max(0, self.deck_scroll_offset - max_visible_cards)
                            # Клик ниже бегунка - прокрутка вниз
                            else:
                                visible_height = self.deck_panel_rect.height - 70
                                max_visible_cards = visible_height // self.DECK_CARD_HEIGHT
                                total_cards = len(self.deck_cards)
                                max_scroll = total_cards - max_visible_cards
                                self.deck_scroll_offset = min(max_scroll, self.deck_scroll_offset + max_visible_cards)
                        continue
                    
                    # ЛКМ
                    if event.button == 1:
                        # Проверка кнопок навигации
                        if self.prev_button.collidepoint(mouse_pos) and self.current_page > 0:
                            self.current_page -= 1
                        
                        elif self.next_button.collidepoint(mouse_pos) and self.current_page < self.get_total_pages() - 1:
                            self.current_page += 1
                        
                        # Проверка кнопки очистки
                        elif self.clear_button.collidepoint(mouse_pos):
                            if self.deck_cards:
                                self.clear_deck()
                        
                        # Проверка кнопки сохранения
                        elif self.save_button.collidepoint(mouse_pos):
                            if len(self.deck_cards) == 20:
                                if self.save_deck():
                                    running = False
                            else:
                                self.show_warning("Колода должна содержать ровно 20 карт!")
                        
                        # Проверка удаления карт из колоды
                        elif self.deck_panel_rect.collidepoint(mouse_pos) and self.deck_cards:
                            visible_height = self.deck_panel_rect.height - 70
                            max_visible_cards = visible_height // self.DECK_CARD_HEIGHT
                            start_index = self.deck_scroll_offset
                            end_index = min(start_index + max_visible_cards, len(self.deck_cards))
                            start_y = self.deck_panel_rect.top + 50
                            
                            for i in range(start_index, end_index):
                                y_pos = start_y + (i - start_index) * self.DECK_CARD_HEIGHT
                                # Позиция кнопки удаления
                                remove_x = self.deck_panel_rect.left + self.DECK_CARD_WIDTH - 30 + 20
                                remove_rect = pygame.Rect(remove_x, y_pos + 15, 20, 20)
                                
                                if remove_rect.collidepoint(mouse_pos):
                                    # Если уже выбрана для удаления - удаляем
                                    if self.selected_for_removal == i:
                                        self.remove_from_deck(i)
                                    else:
                                        # Иначе выбираем для удаления
                                        self.selected_for_removal = i
                                        self.show_remove_hint = True
                                        self.remove_confirm_time = time.time()
                                    break
                            else:
                                # Если кликнули не по кнопке удаления, сбрасываем выбор
                                self.selected_for_removal = None
                                self.show_remove_hint = False
                        
                        # Проверка карт в галерее (добавление в колоду)
                        else:
                            for card_rect, card in self.card_rects:
                                if card_rect.collidepoint(mouse_pos):
                                    if len(self.deck_cards) < 20:
                                        if not self.add_to_deck(card.name):
                                            pass
                                        self.selected_for_removal = None
                                        self.show_remove_hint = False
                                    else:
                                        self.show_warning("Колода полна! Удалите карту перед добавлением новой.")
                                    break
                    
                    # ПКМ - увеличение карты
                    elif event.button == 3:
                        for card_rect, card in self.card_rects:
                            if card_rect.collidepoint(mouse_pos):
                                self.zoomed_card = card
                                break
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.deck_scroll_dragging = False
                
                elif event.type == pygame.MOUSEMOTION:
                    # Обработка перетаскивания скроллбара
                    if self.deck_scroll_dragging:
                        mouse_y = event.pos[1]
                        delta_y = mouse_y - self.drag_start_y
                        
                        visible_height = self.deck_panel_rect.height - 70
                        max_visible_cards = visible_height // self.DECK_CARD_HEIGHT
                        total_cards = len(self.deck_cards)
                        
                        if total_cards > max_visible_cards:
                            max_scroll = total_cards - max_visible_cards
                            scroll_range = visible_height - self.scrollbar_thumb_rect.height
                            
                            if scroll_range > 0:
                                delta_scroll = int(delta_y * max_scroll / scroll_range)
                                new_scroll = self.drag_start_scroll + delta_scroll
                                self.deck_scroll_offset = max(0, min(new_scroll, max_scroll))
            
            self.draw()
        
        pygame.quit()
        print(f"[DECK_CREATOR] Выход из конструктора колоды. Карт в колоде: {len(self.deck_cards)}")
        return len(self.deck_cards)

def main():
    """Точка входа для самостоятельного запуска конструктора"""
    creator = DeckCreator()
    cards_count = creator.run()
    print(f"Колода создана с {cards_count} картами")
    
    return cards_count

if __name__ == "__main__":
    main()