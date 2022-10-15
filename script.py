from time import perf_counter
import utils
import pandas as pd
from stockfish import Stockfish
import random

STOCKFISH_PATH = "stockfish_15_win_x64_avx2\stockfish_15_x64_avx2.exe"
STOCKFISH_DEPTH = 15
STOCKFISH_THREADS = 6
STOCKFISH_HASH = 8192

GAME_LIMIT = 5

USERNAME = "Gukesh D"

stockfish = Stockfish(
    path=STOCKFISH_PATH,
    depth=STOCKFISH_DEPTH,
    parameters={"Threads": STOCKFISH_THREADS,
                "Minimum Thinking Time": 30,
                "Hash": STOCKFISH_HASH},
)


def print_stockfish_parameters():
    parameters = stockfish.get_parameters()
    print("---------------------------------")
    print(f"Stockfish: ")
    print(f"Depth: {stockfish.depth}")
    print(f"Threads: {parameters['Threads']}")
    print(f"Hash: {parameters['Hash']}")
    print("---------------------------------")


def save_data_to_csv(data, header):
    df = pd.DataFrame(data)
    username = USERNAME.replace(" ", "").replace(",", "")
    df.to_csv(
        f"games/{username}/{username}_{STOCKFISH_DEPTH}_depth.csv", encoding='utf-8', mode="w" if header else 'a', header=header, index=False)


# Start timer
start_time = perf_counter()

# Print Stockfish details
print_stockfish_parameters()

# Get games
games = utils.get_games(USERNAME)

header = True
for i, game in enumerate(games):
    print(f"Processing game: {i + 1}/{len(games)}")
    data = utils.process_game(game, USERNAME, stockfish)
    save_data_to_csv(data, header)
    header = False

end_time = perf_counter()

print(f"Done! Games processed: {len(games)}")
print(f"Elapsed time: {end_time - start_time:0.4f} seconds")
print(
    f"Average time per game: {(end_time - start_time)/len(games):0.4f} seconds")
