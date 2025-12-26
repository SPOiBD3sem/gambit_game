import os
import pathlib

class Card:
    def __init__(self, name, power, image_path, ability, allowed_lines):
        self.name = name
        self.power = power
        self.image_path = image_path
        self.ability = ability
        self.allowed_lines = allowed_lines

# Способности карт
def oak_bard_lights_ability(line_cards, card, played_line):
    """Усиливает всех союзников в ряду на +1 (включая себя)"""
    if played_line in line_cards:
        enhanced_cards = []
        
        for other_card in line_cards[played_line]:
            old_power = other_card.get("power", 0)
            other_card["power"] = old_power + 1
            enhanced_cards.append(f"{other_card.get('name', 'карта')}: {old_power}→{other_card['power']}")
            print(f"[CARDS] Бард/Дуб/Огни усилил {other_card.get('name', 'карту')} с {old_power} до {other_card['power']}")
        
        if enhanced_cards:
            print(f"[CARDS] Бард/Дуб/Огни усилил карты на линии {played_line}: {', '.join(enhanced_cards)}")
        else:
            print(f"[CARDS] Бард/Дуб/Огни: на линии {played_line} нет карт для усиления")
    else:
        print(f"[CARDS] Бард/Дуб/Огни: линия {played_line} не найдена")

def frost_ability(line_cards, card, played_line):
    """
    Ослабляет все карты противника в front-ряду на 1
    """
    enemy = "p2" if "p1" in played_line else "p1"
    enemy_front_line = f"{enemy}_front"

    if enemy_front_line in line_cards:
        for c in line_cards[enemy_front_line]:
            # Пропускаем разбойника
            if c.get("name") == "Разбойник":
                print(f"[CARDS] Мороз пропускает разбойника (иммунитет к ослаблению)")
                continue
                
            if c.get("power", 0) > 0:
                c["power"] -= 1
                print(f"[CARDS] Мороз ослабил карту {c.get('name', '')} до {c['power']}")

def fog_ability(line_cards, card, played_line):
    """
    Ослабляет все карты противника в back-ряду на 1
    """
    # определяем противника
    enemy = "p2" if "p1" in played_line else "p1"
    enemy_back_line = f"{enemy}_back"

    if enemy_back_line in line_cards:
        for c in line_cards[enemy_back_line]:
            # Используем c["power"] вместо c["data"].power
            if c.get("power", 0) > 0:
                c["power"] -= 1
                print(f"[CARDS] Мгла ослабила карту {c.get('name', '')} до {c['power']}")

def engineer_ability(line_cards, card, played_line):
    """
    Усиливает самую слабую карту в ряду на +3
    """
    cards_in_line = line_cards.get(played_line, [])

    # исключаем самого инженера
    targets = [c for c in cards_in_line if c is not card]

    if not targets:
        print(f"[CARDS] Инженер: нет других карт в ряду для усиления")
        return

    # ищем карту с минимальной силой - используем c["power"] вместо c["data"].power
    weakest = min(targets, key=lambda c: c.get("power", 0))
    
    old_power = weakest.get("power", 0)
    weakest["power"] = old_power + 3
    
    print(f"[CARDS] Инженер усилил самую слабую карту '{weakest.get('name', 'карту')}' с {old_power} до {weakest['power']}")

def mage_synergy_ability(line_cards, card, played_line):
    """
    Если на столе есть и Огненный маг, и Ледяной маг —
    оба получают +2 (один раз)
    """
    # Собираем все карты на поле (включая только что сыгранную)
    all_cards = []
    for cards in line_cards.values():
        all_cards.extend(cards)
    
    fire_mage = None
    ice_mage = None
    
    # Ищем магов среди всех карт на поле
    for c in all_cards:
        if c.get("name") == "Огненный маг":
            fire_mage = c
        elif c.get("name") == "Ледяной маг":
            ice_mage = c
    
    # Если одного из магов нет — выходим
    if not fire_mage or not ice_mage:
        return
    
    # Проверяем, был ли уже бафф применен
    # Создаем уникальные ключи для проверки
    fire_mage_id = id(fire_mage)
    ice_mage_id = id(ice_mage)
    
    # Используем флаг в самих объектах карт
    if fire_mage.get("mage_buffed") or ice_mage.get("mage_buffed"):
        return
    
    # Применяем бафф
    fire_mage["power"] += 2
    ice_mage["power"] += 2
    
    # Помечаем, что бафф применен
    fire_mage["mage_buffed"] = True
    ice_mage["mage_buffed"] = True
    
    # Выводим отладочную информацию
    print(f"[CARDS] Активирована синергия магов: {fire_mage['name']} и {ice_mage['name']} получают +2")

def dragon_ability(line_cards, card, played_line):
    """
    Дракон уничтожает самую сильную карту противника в ближнем ряду
    """
    enemy = "p2" if "p1" in played_line else "p1"
    enemy_front_line = f"{enemy}_front"
    
    if enemy_front_line in line_cards and line_cards[enemy_front_line]:
        # Исключаем разбойника из возможных целей уничтожения
        eligible_cards = [c for c in line_cards[enemy_front_line] 
                         if c.get("name") != "Разбойник"]
        
        if not eligible_cards:
            print(f"[CARDS] Дракон не нашел подходящих целей")
            return
        
        # Находим самую сильную карту среди оставшихся
        strongest_card = max(eligible_cards, key=lambda c: c["power"])
        
        # Уничтожаем её
        line_cards[enemy_front_line].remove(strongest_card)
        
        print(f"[CARDS] Дракон уничтожил {strongest_card['name']} ({strongest_card['power']} силы) на линии {enemy_front_line}")

def get_asset_path(filename):
    import pathlib
    return str(pathlib.Path(__file__).parent / "assets" / filename)

# Список карт

cards_list = [
    Card(
        name="Ведьмак",
        power=10,
        image_path=get_asset_path("witcher.png"),
        ability=None,
        allowed_lines=["front"]
    ), #0
    Card(
        "Химик",
        4,
        get_asset_path("chemist.png"),
        None,
        ["back"]
    ), #1
    Card(
        "Мудрый дуб",
        2,
        get_asset_path("oak.png"),
        oak_bard_lights_ability,
        ["back"]
    ), #2
    Card(
        "Стужа",
        0,
        get_asset_path("frost.png"),
        frost_ability,
        ["front"]
    ), #3
    Card(
        "Гном",
        1,
        get_asset_path("gnome.png"),
        None,
        ["back"]
    ), #4
    Card(
        "Каменный голем",
        8,
        get_asset_path("rockgolem.png"),
        None,
        ["front"]
    ), #5
    Card(
        "Элитный рыцарь",
        5,
        get_asset_path("knight.png"),
        None,
        ["front"]
    ), #6
    Card(
        "Лучник",
        5,
        get_asset_path("archer.png"),
        None,
        ["back"]
    ), #7
    Card(
        "Арбалетчик",
        5,
        get_asset_path("crossbowman.png"),
        None,
        ["back"]
    ), #8
    Card(
        "Инженер",
        1,
        get_asset_path("engineer.png"),
        engineer_ability,
        ["back"]
    ), #9
    Card(
        "Бард",
        3,
        get_asset_path("bard.png"),
        oak_bard_lights_ability,
        ["front"]
    ), #10
    Card(
        "Огненный маг",
        5,
        get_asset_path("firemage.png"),
        mage_synergy_ability,
        ["back"]
    ), #11
    Card(
        "Ледяной маг",
        5,
        get_asset_path("icemage.png"),
        mage_synergy_ability,
        ["back"]
    ), #12
    Card(
        "Дракон",
        8,
        get_asset_path("dragon.png"),
        dragon_ability,
        ["back"]
    ), #13
    Card(
        "Мгла",
        0,
        get_asset_path("fog.png"),
        fog_ability,
        ["back"]
    ), #14
    Card(
        "Крестьянин",
        6,
        get_asset_path("countryman.png"),
        None,
        ["front"]
    ), #15
    Card(
        "Зверобой",
        4,
        get_asset_path("hunter.png"),
        None,
        ["front"]
    ), #16
    Card(
        "Чародейка",
        7,
        get_asset_path("witch.png"),
        None,
        ["back"]
    ), #17
    Card(
        "Нордлинг",
        8,
        get_asset_path("nordling.png"),
        None,
        ["front"]
    ), #18
    Card(
        "Ручной медведь",
        8,
        get_asset_path("bear.png"),
        None,
        ["front"]
    ), #19
    Card(
        "Драккар",
        5,
        get_asset_path("drakkar.png"),
        None,
        ["front"]
    ), #20
    Card(
        "Требушет",
        8,
        get_asset_path("trebuchet.png"),
        None,
        ["back"]
    ), #21
    Card(
        "Бродяга",
        3,
        get_asset_path("tramp.png"),
        None,
        ["front"]
    ), #22
    Card(
        "Страж леса",
        4,
        get_asset_path("forestguard.png"),
        None,
        ["back"]
    ), #23
    Card(
        "Лучница из племени",
        3,
        get_asset_path("plarch.png"),
        None,
        ["back"]
    ), #24
    Card(
        "Ворон",
        4,
        get_asset_path("crow.png"),
        None,
        ["back"]
    ), #25
    Card(
        "Луналикая",
        6,
        get_asset_path("moon.png"),
        None,
        ["back"]
    ), #26
    Card(
        "Разбойник",
        7,
        get_asset_path("bandit.png"),
        None,
        ["front"]
    ), #27
    Card(
        "Химера",
        4,
        get_asset_path("chimere.png"),
        None,
        ["front"]
    ), #28
    Card(
        "Сигнальные огни",
        0,
        get_asset_path("signal_lights.png"),
        oak_bard_lights_ability,
        ["front"]
    ) #29
]

import copy

# Создаем словарь для быстрого поиска карты по имени
# Ключ - имя карты, Значение - объект карты из списка
CARDS_DICT = {card.name: card for card in cards_list}

def get_card_by_name(name):
    """
    Возвращает глубокую копию карты по её имени.
    Если карта не найдена, возвращает None.
    """
    if name in CARDS_DICT:
        # copy.deepcopy важен, чтобы изменения силы одной карты 
        # не влияли на другую такую же карту в колоде
        return copy.deepcopy(CARDS_DICT[name])
    return None


