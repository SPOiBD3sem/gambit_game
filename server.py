import socket
import threading
import json
import random
import time
import struct
import datetime
from cards import cards_list, Card, get_card_by_name
from database import init_db, insert_game_session, end_game_session, log_action, update_card_statistics
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "game_data.db")

class GameServer:
    def __init__(self, host='localhost', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', port))
        self.server.listen(2)

        self.clients = []
        self.names = ["Игрок 1", "Игрок 2"]
        self.ready_players = 0

        # Инициализация базы данных
        init_db()
        self.session_id = None
        self.session_start_time = None

        # Состояние игры
        self.game_state = {
            "players": {},
            "current_turn": 0,
            "game_started": False,
            "lives": {"p1": 2, "p2": 2},
            "passed": {"p1": False, "p2": False},
            "score": {"p1": 0, "p2": 0},
            "round": 1,
            "game_over": False,
            "winner": None,
            "message": "",
            "message_timer": 0
        }

        self.line_cards = {key: [] for key in ["p1_back", "p1_front", "p2_front", "p2_back"]}

        self.decks = {"p1": [], "p2": []}
        self.hands = {"p1": [], "p2": []}

        print(f"[SERVER] Сервер запущен на 127.0.0.1:{port}" if host == 'localhost' else f"[SERVER] Сервер запущен на {host}:{port}")

    def send_message(self, client, message):
        try:
            data = json.dumps(message, default=self.serialize_card).encode('utf-8')
            client.send(struct.pack('!I', len(data)))
            client.send(data)
        except Exception as e:
            print(f"[SERVER] Ошибка отправки: {e}")

    def serialize_card(self, obj):
        if isinstance(obj, Card):
            return {
                "name": obj.name,
                "power": obj.power,
                "allowed_lines": obj.allowed_lines,
                "image_path": obj.image_path,
                "ability": obj.ability.__name__ if obj.ability else None
            }
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def broadcast(self, message, exclude=None):
        for i, client in enumerate(self.clients):
            if exclude != i:
                self.send_message(client, message)

    def receive_message(self, client):
        try:
            raw_msglen = client.recv(4)
            if not raw_msglen:
                return None
            msglen = struct.unpack('!I', raw_msglen)[0]
            data = b''
            while len(data) < msglen:
                packet = client.recv(min(4096, msglen - len(data)))
                if not packet:
                    return None
                data += packet
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"[SERVER] Ошибка получения: {e}")
            return None
        
    def check_and_apply_mage_synergy(self, newly_placed_card=None):
        """Проверяет и применяет синергию магов"""
        all_cards = []
        for key, cards in self.line_cards.items():
            all_cards.extend(cards)
        
        has_fire_mage = any(card.get("name") == "Огненный маг" for card in all_cards)
        has_ice_mage = any(card.get("name") == "Ледяной маг" for card in all_cards)
        
        if not has_fire_mage or not has_ice_mage:
            return False
        
        fire_mage = None
        ice_mage = None
        
        for card in all_cards:
            if card.get("name") == "Огненный маг":
                fire_mage = card
            elif card.get("name") == "Ледяной маг":
                ice_mage = card
        
        if not fire_mage or not ice_mage:
            return False
        
        if fire_mage.get("mage_buffed") or ice_mage.get("mage_buffed"):
            return False
        
        fire_mage["power"] += 2
        ice_mage["power"] += 2
        fire_mage["mage_buffed"] = True
        ice_mage["mage_buffed"] = True
        
        print(f"[SERVER] Активирована синергия магов: оба получают +2")
        return True

    def handle_client(self, client, player_id):
        while True:
            try:
                message = self.receive_message(client)
                if message is None:
                    break
                self.handle_game_action(message, player_id)
            except Exception as e:
                print(f"[SERVER] Ошибка клиента {player_id}: {e}")
                break
        self.disconnect_client(client, player_id)

    def disconnect_client(self, client, player_id):
        if client in self.clients:
            self.clients.remove(client)
            client.close()
            print(f"[SERVER] Игрок {player_id+1} отключился")

            if not self.game_state["game_started"]:
                player_key = f"p{player_id+1}"
                if player_key in self.game_state["players"]:
                    self.game_state["players"][player_key]["ready"] = False
                    self.ready_players = max(0, self.ready_players - 1)
            
            if len(self.clients) > 0:
                self.broadcast({"type": "player_disconnected", "player": player_id+1})

    def handle_game_action(self, data, player_id):
        action = data.get("action")
        player_key = f"p{player_id+1}"

        if action == "ready":
            # ЛОГИКА ЗАГРУЗКИ КОЛОДЫ
            deck_names = data.get("deck_cards", [])
            
            # 1. Проверяем размер колоды (должно быть строго 20 карт)
            if len(deck_names) != 20:
                print(f"[SERVER] Игрок {player_id+1} прислал некорректную колоду ({len(deck_names)} карт). Требуется ровно 20 карт.")
                self.send_message(self.clients[player_id], {
                    "type": "game_update",
                    "game_state": {**self.game_state, "message": "В колоде должно быть ровно 20 карт!", "message_timer": time.time() + 4}
                })
                return

            # 2. Конвертируем имена карт в объекты
            player_deck_objects = []
            for name in deck_names:
                card_obj = get_card_by_name(name)
                if card_obj:
                    player_deck_objects.append(card_obj)
                else:
                    print(f"[SERVER] Неизвестная карта '{name}' в колоде игрока {player_id+1}")
            
            # Проверяем, что после конвертации осталось ровно 20 карт
            if len(player_deck_objects) != 20:
                 self.send_message(self.clients[player_id], {
                    "type": "game_update",
                    "game_state": {**self.game_state, "message": "Ошибка валидации карт!", "message_timer": time.time() + 4}
                })
                 return

            # 3. Перемешиваем и сохраняем колоду для этого игрока
            random.shuffle(player_deck_objects)
            self.decks[player_key] = player_deck_objects
            print(f"[SERVER] Колода игрока {player_id+1} загружена: {len(self.decks[player_key])} карт")

            # Ставим статус "Готов"
            if not self.game_state["players"].get(player_key, {}).get("ready"):
                self.ready_players += 1
                self.game_state["players"][player_key] = {"name": self.names[player_id], "ready": True}
                self.broadcast({"type": "player_ready", "player": player_id+1, "ready_players": self.ready_players})
                
                if self.ready_players == 2 and not self.game_state["game_started"]:
                    self.start_game()

        elif action == "place_card":
            if self.game_state["current_turn"] != player_id:
                return
            card_index = data["card_index"]
            line_key = data["line_key"]

            if card_index < len(self.hands[player_key]):
                card_obj = self.hands[player_key][card_index]
                line_type = "front" if "front" in line_key else "back"

                if line_type in card_obj.allowed_lines:
                    placed_card = self.hands[player_key].pop(card_index)
                    card_data = {
                        "data": placed_card,
                        "name": placed_card.name,
                        "power": placed_card.power,
                        "ability": placed_card.ability.__name__ if placed_card.ability else None,
                        "image_path": placed_card.image_path,
                        "player": player_key,
                        "placed": True
                    }
                    self.line_cards[line_key].append(card_data)

                    synergy_applied = self.check_and_apply_mage_synergy(card_data)
                    
                    if placed_card.ability:
                        try:
                            placed_card.ability(self.line_cards, card_data, line_key)
                        except Exception as e:
                            print(f"[SERVER] Ошибка при активации способности {placed_card.name}: {e}")
                    
                    if placed_card.ability or synergy_applied:
                        self.show_message(f"{card_data['name']} активировал способность!", 2)

                    self.recalc_scores()
                    log_action(self.session_id, player_key, "place_card",
                               placed_card.name, placed_card.power, line_key,
                               self.game_state, self.game_state["round"])

                    update_card_statistics(placed_card.name, placed_card.power,
                                           ability_used=bool(placed_card.ability))

                    other_player_id = 1 - player_id
                    other_player_key = f"p{other_player_id+1}"
                    if not self.game_state["passed"][other_player_key]:
                        self.game_state["current_turn"] = other_player_id

                    self.game_state["passed"][player_key] = False
                    self.update_all_clients()
                else:
                    self.show_message("Нельзя разместить здесь!", 2)
                    self.update_client(player_id)

        elif action == "pass_turn":
            self.game_state["passed"][player_key] = True
            self.show_message(f"Игрок {player_id+1} пасует до конца раунда", 2)
            
            log_action(self.session_id, player_key, "pass_turn",
                       None, None, None, self.game_state, self.game_state["round"])
            
            # Проверка, спасовали ли оба
            if self.game_state["passed"]["p1"] and self.game_state["passed"]["p2"]:
                time.sleep(1)
                self.end_round()
            else:
                other_player_id = 1 - player_id
                other_player_key = f"p{other_player_id+1}"
                # Проверяем, пасовал ли уже другой игрок
                if not self.game_state["passed"][other_player_key]:
                    self.game_state["current_turn"] = other_player_id
            
            self.update_all_clients()

        elif action == "chat_message":
            self.broadcast({
                "type": "chat_message",
                "player": player_id+1,
                "message": data["message"],
                "player_name": self.names[player_id]
            })

    def show_message(self, text, duration=2):
        self.game_state["message"] = text
        self.game_state["message_timer"] = time.time() + duration

    def start_game(self):
        self.game_state["game_started"] = True
        self.draw_cards("p1", 10)
        self.draw_cards("p2", 10)
        self.session_start_time = time.time()
        self.session_id = insert_game_session(datetime.datetime.now(),
                                              self.names[0], self.names[1])
        print(f"[SERVER] Игра началась! (Сессия #{self.session_id})")
        self.update_all_clients()

    def draw_cards(self, player, count):
        """
        Выдает игроку карты из его персональной колоды.
        Карты удаляются из колоды (не повторяются).
        Если карт не хватает, выдает все оставшиеся.
        """
        cards_drawn = 0
        while cards_drawn < count:
            if len(self.decks[player]) > 0:
                card_data = self.decks[player].pop(0)
                self.hands[player].append(card_data)
                cards_drawn += 1
            else:
                print(f"[SERVER] У игрока {player} закончились карты в колоде!")
                self.show_message(f"У {player} закончились карты!", 2)
                break
        
        print(f"[SERVER] Игрок {player} получил {cards_drawn} карт. Осталось в колоде: {len(self.decks[player])}")

    def recalc_scores(self):
        self.game_state["score"]["p1"] = 0
        self.game_state["score"]["p2"] = 0
        for key, cards in self.line_cards.items():
            player = "p1" if "p1" in key else "p2"
            for card in cards:
                self.game_state["score"][player] += card["power"]

    def end_round(self):
        p1_score = self.game_state["score"]["p1"]
        p2_score = self.game_state["score"]["p2"]

        if p1_score > p2_score:
            self.game_state["lives"]["p2"] -= 1
            round_winner = "Игрок 1"
        elif p2_score > p1_score:
            self.game_state["lives"]["p1"] -= 1
            round_winner = "Игрок 2"
        else:
            self.game_state["lives"]["p1"] -= 1
            self.game_state["lives"]["p2"] -= 1
            round_winner = "Ничья"

        self.show_message(f"Раунд {self.game_state['round']} за {round_winner}", 3)

        for key, cards in self.line_cards.items():
            for c in cards:
                update_card_statistics(c["name"], c["power"], ability_used=bool(c.get("ability")))

        if self.game_state["lives"]["p1"] <= 0 or self.game_state["lives"]["p2"] <= 0:
            self.game_state["game_over"] = True
            if self.game_state["lives"]["p1"] == self.game_state["lives"]["p2"]:
                self.game_state["winner"] = "Ничья"
            else:
                self.game_state["winner"] = "Игрок 1" if self.game_state["lives"]["p1"] > 0 else "Игрок 2"

            duration = int(time.time() - self.session_start_time)
            end_game_session(self.session_id, self.game_state["winner"],
                             self.game_state["round"], duration)
            print(f"[SERVER] Игра окончена. Сессия #{self.session_id} сохранена в базу.")
        else:
            self.game_state["round"] += 1
            # СБРАСЫВАЕМ ФЛАГИ ПАСА ТОЛЬКО ЗДЕСЬ - В НАЧАЛЕ НОВОГО РАУНДА
            self.game_state["passed"] = {"p1": False, "p2": False}
            
            # Очистка поля
            for key in self.line_cards:
                # Сбрасываем флаги баффов
                for card in self.line_cards[key]:
                    card.pop("mage_buffed", None)
                self.line_cards[key].clear()
                
            # Выдаем следующие 5 случайных карт из оставшейся колоды
            print(f"[SERVER] Начало раунда {self.game_state['round']}. Раздача 5 карт.")
            self.draw_cards("p1", 5)
            self.draw_cards("p2", 5)
            
            # Определяем первого ходящего в новом раунде
            self.game_state["current_turn"] = 0 if self.game_state["round"] % 2 != 0 else 1

        self.recalc_scores()
        self.update_all_clients()

    def update_client(self, player_id):
        game_data = self.get_game_data()
        self.send_message(self.clients[player_id], game_data)

    def update_all_clients(self):
        game_data = self.get_game_data()
        self.broadcast(game_data)

    def get_game_data(self):
        game_data = {"type": "game_update", "game_state": self.game_state,
                     "line_cards": {}, "hands": {}}
        for key, cards in self.line_cards.items():
            game_data["line_cards"][key] = [{"name": c["name"],
                                             "power": c["power"],
                                             "image_path": c["image_path"],
                                             "player": c["player"]} for c in cards]
        for player in ["p1", "p2"]:
            game_data["hands"][player] = [{"name": c.name,
                                           "power": c.power,
                                           "allowed_lines": c.allowed_lines,
                                           "image_path": c.image_path,
                                           "ability": c.ability.__name__ if c.ability else None} for c in self.hands[player]]
        return game_data

    def run(self):
        print("[SERVER] Ожидание подключений...")
        while len(self.clients) < 2:
            try:
                client, address = self.server.accept()
                print(f"[SERVER] Новое подключение: {address}")
                self.clients.append(client)
                player_id = len(self.clients) - 1
                self.send_message(client, {"type": "welcome",
                                           "player_id": player_id,
                                           "player_name": self.names[player_id]})
                thread = threading.Thread(target=self.handle_client, args=(client, player_id))
                thread.daemon = True
                thread.start()
            except KeyboardInterrupt:
                print("\n[SERVER] Сервер остановлен")
                break
            except Exception as e:
                print(f"[SERVER] Ошибка подключения: {e}")

        try:
            while True:
                if self.game_state["game_over"]:
                    print(f"[SERVER] Победитель: {self.game_state['winner']}")
                    time.sleep(10)
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[SERVER] Сервер остановлен")


if __name__ == "__main__":
    server = GameServer()
    server.run()