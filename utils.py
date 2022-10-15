import json
import math
from pathlib import Path
import chess.pgn
import requests
from time import perf_counter
import uuid
import os
import random

def read_games_from_pgn_file(username):
    path = 'pgn_files/{username}'
    games = []

    # iterate through all file
    for file in os.listdir(path):
        # Check whether file is in text format or not:
        file_path = f"{path}/{file}"
        pgn = open(file_path, 'r', encoding='utf-8')
        temp_games = []
        while True:
            game = chess.pgn.read_game(pgn)
            if game is not None:
                temp_games.append(game)
            else:
                break
        games = games + random.sample(temp_games, 5)
    return games


def fetch_chesscom_games(username):
    print("Fetching games - In progress...")
    start_time = perf_counter()
    games = []
    for month in range(1, 11):
        res = requests.get(
            f"https://api.chess.com/pub/player/{username}/games/2022/{str(month).zfill(2)}")
        data = res.json()

        games = games + data["games"]

    json_games = json.dumps(games)
    with open(f"games/{username}/{username}.json", "w") as outfile:
        outfile.write(json_games)

    pgns = [game['pgn'] for game in games]
    with open(f"games/{username}/{username}.pgn", "w") as outfile:
        for pgn in pgns:
            outfile.write(pgn + "\n")

    end_time = perf_counter()

    print(f"Number of games found: {len(pgns)}")
    print(
        f"Fetching games - Done! Elapsed time: {end_time - start_time:0.4f} seconds")
    print("---------------------------------")

    return games


def get_games(username):
    #fetch_chesscom_games(username)
    Path(f"games/{username}/").mkdir(parents=True, exist_ok=True)
    games = read_games_from_pgn_file(username)

    return games


def get_game_info(game, username):
    date = game.headers.get("Date")
    site = game.headers.get("Site")
    event = game.headers.get("Event")
    round = game.headers.get("Round")
    white = game.headers.get("White")
    black = game.headers.get("Black")
    result = game.headers.get("Result")
    white_elo = game.headers.get("WhiteElo")
    black_elo = game.headers.get("BlackElo")
    eco = game.headers.get("ECO")

    is_user_white = white == username

    player_result = "draw"
    if (is_user_white and result == "1-0") or (not is_user_white and result == "0-1"):
        player_result = "win"
    elif (is_user_white and result == "0-1") or (not is_user_white and result == "1-0"):
        player_result = "lose"

    info = {
        "game_id": uuid.uuid4(),
        "date": date,
        "site": site,
        "event": event,
        "round": round,
        "player": white if is_user_white else black,
        "opponent": black if is_user_white else white,
        "player_color": "white" if is_user_white else "black",
        "result": result,
        "player_result": player_result,
        "player_elo":  white_elo if is_user_white else black_elo,
        "opponent_elo": black_elo if is_user_white else white_elo,
        "eco": eco,
    }

    for key, value in info.items():
        print(f"{key.capitalize().replace('_',' ')}: {value}")

    print("")
    return info


def process_game(game, username, stockfish):
    info = get_game_info(game, username)
    is_user_white = info["player_color"] == "white"

    board = game.board()
    moves = game.mainline_moves()
    mainline_data = list(game.mainline())

    no_moves = math.floor(len(list(moves)) / 2) + 1

    fen = board.fen()
    stockfish.set_fen_position(fen)

    data = []
    start_time = perf_counter()
    for i, move in enumerate(moves):
        is_turn_white = i % 2 == 0

        if (is_user_white and not is_turn_white) or (not is_user_white and is_turn_white):
            board.push(move)
        else:
            move_number = math.floor(i / 2) + 1
            move_start_time = perf_counter()
            fen = board.fen()
            stockfish.set_fen_position(fen)
            best_move = stockfish.get_top_moves(1)

            board.push(move)
            same_move = move.uci() == best_move[0]["Move"]
            if same_move:
                a_move = {
                    "move_number": move_number,
                    "human_move": move.uci(),
                    "human_centipawn": best_move[0]["Centipawn"],
                    "engine_move": best_move[0]["Move"],
                    "engine_centipawn": best_move[0]["Centipawn"],
                    "centipawn_loss": 0,
                    "engine_mate": best_move[0]["Mate"],
                    "human_mate": best_move[0]["Mate"],
                    "remaining_clock": mainline_data[i].clock(),
                    "stockfish_depth": stockfish.depth
                }
            else:
                fen = board.fen()
                stockfish.set_fen_position(fen)
                eval = stockfish.get_evaluation()

                a_move = {
                    "move_number": move_number,
                    "human_move": move.uci(),
                    "human_centipawn": eval["value"] if eval["type"] == "cp" else None,
                    "engine_move": best_move[0]["Move"],
                    "engine_centipawn": best_move[0]["Centipawn"],
                    "centipawn_loss": best_move[0]["Centipawn"] - eval["value"] if eval["type"] == "cp" and best_move[0]["Centipawn"] is not None else None,
                    "engine_mate": best_move[0]["Mate"],
                    "human_mate": eval["value"] if eval["type"] == "mate" else None,
                    "remaining_clock": mainline_data[i].clock(),
                    "stockfish_depth": stockfish.depth
                }

            row = dict(info, **a_move)
            data.append(row)

            move_end_time = perf_counter()
            print(
                f"Move {move_number}/{no_moves}, Elapsed time: {move_end_time - move_start_time:0.4f} seconds")

    end_time = perf_counter()
    print("Game processed!")
    print(f"Elapsed time: {end_time - start_time:0.4f} seconds")
    print("---------------------------------\n")

    return
