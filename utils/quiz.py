import csv
from collections import defaultdict

# TODO: Convert to MongoDB
from pathlib import Path

import requests

# Setup paths
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
CSV_FILE = CACHE_DIR / "active_quizzes.csv"

number_of_q = 10
category = 16
difficulty = "easy"
type = "multiple"


def fetch_categories() -> dict:
    """Create structured categories."""
    response = requests.get("https://opentdb.com/api_category.php", timeout=(3, 5))
    raw_categories = response.json()["trivia_categories"]

    structured_categories = defaultdict(dict)

    for category in raw_categories:
        name: str = category["name"]
        id = category["id"]

        if ":" in name:
            name, subname = name.split(": ")
            structured_categories[name][subname] = id
        else:
            structured_categories[name] = id

    return structured_categories


def fetch_quizzes() -> dict:
    """Return list of quizzes based on parameters."""
    url = f"https://opentdb.com/api.php?amount={number_of_q}&category={category}&difficulty={difficulty}&type={type}"

    try:
        response = requests.get(url, timeout=(3, 5))
    except requests.exceptions.Timeout:
        print("Timed out")

    return response.json()["results"]


# for i, quiz in enumerate(fetch_quizzes()):
#     answers = [quiz["correct_answer"]] + quiz["incorrect_answers"]  # noqa: ERA001
#     shuffle(answers)  # noqa: ERA001

#     print(f"{i+1}. {quiz["question"]}")  # noqa: ERA001
#     print("\t".join(answers))  # noqa: ERA001
#     print()  # noqa: ERA001


def read_active_quizzes() -> list:
    """Return all currently active quizzes."""
    active_quizzes = []
    try:
        with Path.open(CSV_FILE) as file:
            reader = csv.reader(file)
            active_quizzes = [int(rows[0]) for rows in reader]
    except FileNotFoundError:
        pass
    return active_quizzes


def write_active_quizzes(active_quizzes: list) -> None:
    """Write all currently active quizzes to csv."""
    with Path.open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        for channel_id in active_quizzes:
            writer.writerow([channel_id])


def is_quiz_active(channel_id: int) -> bool:
    """Check if a quiz is active in channel."""
    active_quizzes = read_active_quizzes()
    return channel_id in active_quizzes


def set_quiz_active(channel_id: int) -> None:
    """Mark a channel as having active quiz."""
    active_quizzes = read_active_quizzes()
    active_quizzes.append(channel_id)
    write_active_quizzes(active_quizzes)


def set_quiz_ended(channel_id: int) -> None:
    """Remove quiz from active list."""
    active_quizzes = read_active_quizzes()
    active_quizzes.remove(channel_id)
    write_active_quizzes(active_quizzes)
