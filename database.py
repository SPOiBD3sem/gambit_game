import sqlite3
import json
import datetime

import pathlib
DB_PATH = str(pathlib.Path(__file__).parent / "game_data.db")


def init_db():
    """Создаёт таблицы, если они ещё не существуют"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Игровые сессии
    cur.execute("""
    CREATE TABLE IF NOT EXISTS game_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time DATETIME,
        end_time DATETIME,
        player1_name TEXT,
        player2_name TEXT,
        winner TEXT,
        duration_sec INTEGER,
        rounds_played INTEGER
    )
    """)

    # Логи действий
    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        timestamp DATETIME,
        player TEXT,
        action_type TEXT,
        card_name TEXT,
        card_power INTEGER,
        line_key TEXT,
        result_state TEXT,
        round INTEGER,
        FOREIGN KEY (session_id) REFERENCES game_sessions(id)
    )
    """)

    # Общая статистика по картам
    cur.execute("""
    CREATE TABLE IF NOT EXISTS card_statistics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_name TEXT UNIQUE,
        times_used INTEGER DEFAULT 0,
        avg_power REAL DEFAULT 0,
        ability_activations INTEGER DEFAULT 0,
        win_rate REAL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def insert_game_session(start_time, p1, p2):
    """Создаёт новую запись игровой сессии"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO game_sessions (start_time, player1_name, player2_name)
        VALUES (?, ?, ?)
    """, (start_time, p1, p2))
    conn.commit()
    session_id = cur.lastrowid
    conn.close()
    return session_id


def end_game_session(session_id, winner, rounds_played, duration_sec):
    """Обновляет запись после завершения сессии"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        UPDATE game_sessions
        SET end_time = ?, winner = ?, rounds_played = ?, duration_sec = ?
        WHERE id = ?
    """, (datetime.datetime.now(), winner, rounds_played, duration_sec, session_id))
    conn.commit()
    conn.close()


def log_action(session_id, player, action_type, card_name=None, card_power=None,
               line_key=None, game_state=None, round_num=1):
    """Сохраняет ход игрока"""
    if session_id is None:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO player_actions
        (session_id, timestamp, player, action_type, card_name, card_power, line_key, result_state, round)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id,
          datetime.datetime.now(),
          player,
          action_type,
          card_name,
          card_power,
          line_key,
          json.dumps(game_state, ensure_ascii=False),
          round_num))
    conn.commit()
    conn.close()


def update_card_statistics(card_name, power, ability_used=False, win=False):
    """Обновляет агрегированную статистику карт"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Проверяем, есть ли карта
    cur.execute("SELECT times_used, avg_power, ability_activations, win_rate FROM card_statistics WHERE card_name = ?", (card_name,))
    row = cur.fetchone()

    if row:
        times_used, avg_power, ability_activations, win_rate = row
        new_times = times_used + 1
        new_avg = (avg_power * times_used + power) / new_times
        new_ability = ability_activations + (1 if ability_used else 0)
        new_winrate = (win_rate * times_used + (1 if win else 0)) / new_times

        cur.execute("""
            UPDATE card_statistics
            SET times_used=?, avg_power=?, ability_activations=?, win_rate=?
            WHERE card_name=?
        """, (new_times, new_avg, new_ability, new_winrate, card_name))
    else:
        cur.execute("""
            INSERT INTO card_statistics (card_name, times_used, avg_power, ability_activations, win_rate)
            VALUES (?, ?, ?, ?, ?)
        """, (card_name, 1, power, 1 if ability_used else 0, 1 if win else 0))

    conn.commit()
    conn.close()
