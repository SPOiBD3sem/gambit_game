from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import sys
import json
import os
import pathlib

def get_display_settings():
    """Функция выбора и сохранения настроек отображения"""
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption("Выбор настроек отображения - Гамбит")
    
    monitor_info = pygame.display.Info()
    monitor_width = monitor_info.current_w
    monitor_height = monitor_info.current_h
    
    font = pygame.font.SysFont("arial", 28)
    title_font = pygame.font.SysFont("arial", 40, bold=True)
    small_font = pygame.font.SysFont("arial", 22)
    
    clock = pygame.time.Clock()
    
    # Режимы отображения
    display_modes = [
        (pygame.Rect(100, 150, 800, 60), 
         "Полноэкранный режим (Fullscreen)", 
         "fullscreen"),
        
        (pygame.Rect(100, 220, 800, 60), 
         "Оконный режим (Windowed)", 
         "windowed"),
        
        (pygame.Rect(100, 290, 800, 60), 
         "Оконный режим без рамки (Borderless)", 
         "borderless")
    ]
    
    # Разрешения
    resolutions = [
        (pygame.Rect(100, 400, 180, 60), "1280×720", (1280, 720)),
        (pygame.Rect(300, 400, 180, 60), "1366×768", (1366, 768)),
        (pygame.Rect(500, 400, 180, 60), "1920×1080", (1920, 1080)),
        (pygame.Rect(700, 400, 180, 60), "2560×1440", (2560, 1440)),
        (pygame.Rect(100, 480, 180, 60), "3840×2160", (3840, 2160)),
    ]
    
    # Загружаем сохраненные настройки для отображения текущего выбора
    saved_settings = load_display_settings()
    saved_mode = saved_settings["display_mode"]
    saved_res = (saved_settings["resolution"]["width"], 
                 saved_settings["resolution"]["height"])
    
    selected_mode = saved_mode
    selected_resolution = saved_res
    
    # Кнопка подтверждения выбора
    confirm_button = pygame.Rect(400, 580, 200, 60)
    
    while True:
        screen.fill((34, 34, 34))
        
        # Заголовки
        title = title_font.render("Выберите настройки отображения", True, (255, 255, 255))
        mode_title = font.render("Режим отображения:", True, (220, 220, 255))
        res_title = font.render("Разрешение экрана:", True, (220, 220, 255))
        
        screen.blit(title, (500 - title.get_width()//2, 30))
        screen.blit(mode_title, (100, 120))
        screen.blit(res_title, (100, 370))
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Отрисовка кнопок режимов
        for button_rect, name, mode in display_modes:
            if selected_mode == mode:
                color = (30, 180, 30)  
            elif button_rect.collidepoint(mouse_pos):
                color = (70, 130, 180)  
            else:
                color = (50, 100, 150)  
            
            pygame.draw.rect(screen, color, button_rect, border_radius=8)
            pygame.draw.rect(screen, (100, 150, 200), button_rect, 2, border_radius=8)
            
            text = font.render(name, True, (255, 255, 255))
            screen.blit(text, (button_rect.centerx - text.get_width()//2,
                             button_rect.centery - text.get_height()//2))
        
        # Отрисовка кнопок разрешений
        for button_rect, name, res in resolutions:
            if selected_resolution == res:
                color = (30, 180, 30)  
            elif button_rect.collidepoint(mouse_pos):
                color = (70, 130, 180)  
            else:
                color = (50, 100, 150)  
            
            pygame.draw.rect(screen, color, button_rect, border_radius=8)
            pygame.draw.rect(screen, (100, 150, 200), button_rect, 2, border_radius=8)
            
            text = small_font.render(name, True, (255, 255, 255))
            screen.blit(text, (button_rect.centerx - text.get_width()//2,
                             button_rect.centery - text.get_height()//2))
        
        # Отрисовка кнопки подтверждения
        confirm_enabled = selected_mode is not None and selected_resolution is not None
        confirm_color = (30, 180, 30) if confirm_enabled else (80, 80, 80)
        
        pygame.draw.rect(screen, confirm_color, confirm_button, border_radius=8)
        pygame.draw.rect(screen, (100, 200, 100), confirm_button, 2, border_radius=8)
        
        confirm_text = font.render("Подтвердить" if confirm_enabled else "Выберите оба параметра", 
                                  True, (255, 255, 255))
        screen.blit(confirm_text, (confirm_button.centerx - confirm_text.get_width()//2,
                                 confirm_button.centery - confirm_text.get_height()//2))
        
        # Текущий выбор (текст внизу)
        if selected_mode and selected_resolution:
            current_selection = f"Текущий выбор: {selected_mode}, {selected_resolution[0]}×{selected_resolution[1]}"
            selection_text = small_font.render(current_selection, True, (220, 220, 60))
            screen.blit(selection_text, (500 - selection_text.get_width()//2, 520))
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button_rect, name, mode in display_modes:
                    if button_rect.collidepoint(event.pos):
                        selected_mode = mode
                        break
                
                # Выбор разрешения
                for button_rect, name, res in resolutions:
                    if button_rect.collidepoint(event.pos):
                        selected_resolution = res
                        break
                
                # Подтверждение выбора
                if confirm_enabled and confirm_button.collidepoint(event.pos):
                    if selected_mode and selected_resolution:
                        # СОХРАНЯЕМ НАСТРОЙКИ
                        save_display_settings(selected_mode, selected_resolution)
                        pygame.quit()
                        return selected_mode, selected_resolution
        
        pygame.display.flip()
        clock.tick(60)

def scale_value(value, axis='x', scale_x=1.0, scale_y=1.0):
    """Масштабирование значений"""
    if axis == 'x': 
        return int(value * scale_x)
    elif axis == 'y': 
        return int(value * scale_y)
    return int(value * (scale_x + scale_y) / 2)

def get_settings_path():
    """Получение пути к файлу настроек"""
    # Используем папку пользователя для сохранения настроек
    if os.name == 'nt': 
        appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        settings_dir = os.path.join(appdata_dir, 'MiniGwent')
    else:  
        settings_dir = os.path.join(os.path.expanduser('~'), '.minigwent')
    
    os.makedirs(settings_dir, exist_ok=True)
   
    return os.path.join(settings_dir, "game_settings.json")

SETTINGS_FILE = get_settings_path()

def save_display_settings(display_mode, resolution):
    """Сохранение настроек в файл"""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except:
        settings = {}

    settings["display_mode"] = display_mode
    settings["resolution"] = {
        "width": resolution[0],
        "height": resolution[1]
    }
    
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print(f"[SETTINGS] Настройки сохранены в {SETTINGS_FILE}: {display_mode}, {resolution}")
        return True
    except Exception as e:
        print(f"[SETTINGS] Ошибка сохранения: {e}")
        try:
            backup_path = os.path.join(os.path.dirname(__file__), "game_settings.json")
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            print(f"[SETTINGS] Настройки сохранены в резервный файл: {backup_path}")
            return True
        except Exception as e2:
            print(f"[SETTINGS] Ошибка резервного сохранения: {e2}")
            return False

def load_display_settings():
    """Загрузка настроек из файла"""
    default_settings = {
        "display_mode": "windowed",
        "resolution": {
            "width": 1280,
            "height": 720
        }
    }
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            if ("display_mode" in settings and 
                "resolution" in settings and
                "width" in settings["resolution"] and
                "height" in settings["resolution"]):
                return settings
            else:
                print(f"[SETTINGS] Файл настроек поврежден, используются настройки по умолчанию")
        except Exception as e:
            print(f"[SETTINGS] Ошибка загрузки основного файла: {e}")

    backup_path = os.path.join(os.path.dirname(__file__), "game_settings.json")
    if os.path.exists(backup_path):
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            if ("display_mode" in settings and 
                "resolution" in settings and
                "width" in settings["resolution"] and
                "height" in settings["resolution"]):
                print(f"[SETTINGS] Загружены настройки из резервного файла")
                return settings
        except Exception as e:
            print(f"[SETTINGS] Ошибка загрузки резервного файла: {e}")
 
    print(f"[SETTINGS] Используются настройки по умолчанию")
    save_display_settings(default_settings["display_mode"], 
                         (default_settings["resolution"]["width"], 
                          default_settings["resolution"]["height"]))
    return default_settings

def save_audio_settings(music_volume=0.5, sound_volume=0.5, music_enabled=True):
    """Сохранение настроек звука"""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except:
        settings = {}
    
    # Добавляем/обновляем настройки звука
    settings["audio"] = {
        "music_volume": music_volume,
        "sound_volume": sound_volume,
        "music_enabled": music_enabled
    }
    
    # Сохраняем все настройки
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print(f"[SETTINGS] Настройки звука сохранены")
        return True
    except Exception as e:
        print(f"[SETTINGS] Ошибка сохранения настроек звука: {e}")
        return False

def load_audio_settings():
    """Загрузка настроек звука"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            if "audio" in settings:
                return settings["audio"]
    except Exception as e:
        print(f"[SETTINGS] Ошибка загрузки настроек звука: {e}")
    
    default_settings = {
        "music_volume": 0.5,
        "sound_volume": 0.5,
        "music_enabled": True
    }
    save_audio_settings(**default_settings)
    return default_settings

def get_audio_settings_screen():
    """Функция для настроек звука"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Настройки звука - Гамбит")
    
    font = pygame.font.SysFont("arial", 28)
    title_font = pygame.font.SysFont("arial", 40, bold=True)
    small_font = pygame.font.SysFont("arial", 22)
    
    clock = pygame.time.Clock()

    audio_settings = load_audio_settings()
    music_volume = audio_settings["music_volume"]
    sound_volume = audio_settings["sound_volume"]
    music_enabled = audio_settings["music_enabled"]
    
    # Кнопка включения/выключения музыки
    music_toggle_rect = pygame.Rect(200, 150, 400, 60)
    music_toggle_color = (30, 180, 30) if music_enabled else (180, 30, 30)
    
    # Ползунки громкости
    music_slider_rect = pygame.Rect(200, 250, 400, 20)
    sound_slider_rect = pygame.Rect(200, 350, 400, 20)
    
    # Кнопка сохранения
    save_button = pygame.Rect(300, 450, 200, 60)
    
    # Флаги перетаскивания
    dragging_music = False
    dragging_sound = False
    
    while True:
        screen.fill((34, 34, 34))
        
        # Заголовок
        title = title_font.render("Настройки звука", True, (255, 255, 255))
        screen.blit(title, (400 - title.get_width()//2, 30))
        
        # Кнопка включения/выключения музыки
        pygame.draw.rect(screen, music_toggle_color, music_toggle_rect, border_radius=8)
        pygame.draw.rect(screen, (100, 150, 200), music_toggle_rect, 2, border_radius=8)
        
        music_text = font.render(f"Музыка: {'ВКЛ' if music_enabled else 'ВЫКЛ'}", True, (255, 255, 255))
        screen.blit(music_text, (music_toggle_rect.centerx - music_text.get_width()//2,
                               music_toggle_rect.centery - music_text.get_height()//2))
        
        # Ползунок громкости музыки
        music_title = font.render("Громкость музыки:", True, (220, 220, 255))
        screen.blit(music_title, (200, 220))
        
        pygame.draw.rect(screen, (80, 80, 80), music_slider_rect)
        pygame.draw.rect(screen, (100, 150, 200), music_slider_rect, 2)
        
        music_handle_x = music_slider_rect.left + int(music_volume * music_slider_rect.width)
        music_handle = pygame.Rect(music_handle_x - 5, music_slider_rect.top - 5, 10, 30)
        pygame.draw.rect(screen, (30, 180, 30), music_handle, border_radius=3)
        
        music_value = small_font.render(f"{int(music_volume * 100)}%", True, (255, 255, 255))
        screen.blit(music_value, (music_slider_rect.right + 10, music_slider_rect.top - 5))
        
        # Ползунок громкости звуков
        sound_title = font.render("Громкость звуков:", True, (220, 220, 255))
        screen.blit(sound_title, (200, 320))
        
        pygame.draw.rect(screen, (80, 80, 80), sound_slider_rect)
        pygame.draw.rect(screen, (100, 150, 200), sound_slider_rect, 2)
        
        sound_handle_x = sound_slider_rect.left + int(sound_volume * sound_slider_rect.width)
        sound_handle = pygame.Rect(sound_handle_x - 5, sound_slider_rect.top - 5, 10, 30)
        pygame.draw.rect(screen, (30, 180, 30), sound_handle, border_radius=3)
        
        sound_value = small_font.render(f"{int(sound_volume * 100)}%", True, (255, 255, 255))
        screen.blit(sound_value, (sound_slider_rect.right + 10, sound_slider_rect.top - 5))
        
        # Кнопка сохранения
        save_color = (30, 180, 30)
        pygame.draw.rect(screen, save_color, save_button, border_radius=8)
        pygame.draw.rect(screen, (100, 200, 100), save_button, 2, border_radius=8)
        
        save_text = font.render("Сохранить", True, (255, 255, 255))
        screen.blit(save_text, (save_button.centerx - save_text.get_width()//2,
                              save_button.centery - save_text.get_height()//2))
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                # Переключение музыки
                if music_toggle_rect.collidepoint(mouse_pos):
                    music_enabled = not music_enabled
                    music_toggle_color = (30, 180, 30) if music_enabled else (180, 30, 30)
                
                # Начало перетаскивания ползунков
                if music_slider_rect.collidepoint(mouse_pos):
                    dragging_music = True
                if sound_slider_rect.collidepoint(mouse_pos):
                    dragging_sound = True
                
                # Сохранение
                if save_button.collidepoint(mouse_pos):
                    save_audio_settings(music_volume, sound_volume, music_enabled)
                    pygame.quit()
                    return {
                        "music_volume": music_volume,
                        "sound_volume": sound_volume,
                        "music_enabled": music_enabled
                    }
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging_music = False
                dragging_sound = False
            
            elif event.type == pygame.MOUSEMOTION:
                if dragging_music:
                    mouse_x = event.pos[0]
                    music_volume = max(0, min(1, (mouse_x - music_slider_rect.left) / music_slider_rect.width))
                
                if dragging_sound:
                    mouse_x = event.pos[0]
                    sound_volume = max(0, min(1, (mouse_x - sound_slider_rect.left) / sound_slider_rect.width))
        
        pygame.display.flip()
        clock.tick(60)

def get_saved_display_settings():
    """Получение сохраненных настроек для клиента"""
    settings = load_display_settings()
    
    display_mode = settings["display_mode"]
    resolution = (
        settings["resolution"]["width"],
        settings["resolution"]["height"]
    )
    
    return display_mode, resolution

def get_audio_settings():
    """Получение настроек звука для клиента"""
    return load_audio_settings()

if __name__ == "__main__":
    print("Загрузка настроек...")
    settings = load_display_settings()
    print(f"Текущие настройки: {settings}")
    print(f"Файл настроек: {SETTINGS_FILE}")
    
    print("\nПолучение сохраненных настроек...")
    mode, res = get_saved_display_settings()
    print(f"Режим: {mode}, Разрешение: {res}")
    
    print("\nЗагрузка настроек звука...")
    audio = get_audio_settings()
    print(f"Настройки звука: {audio}")
    
    print("\nДля изменения настроек запустите лаунчер и выберите 'Настройки отображения' или 'Настройки звука'")