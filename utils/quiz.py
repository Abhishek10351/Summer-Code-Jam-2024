import csv
import random
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


# defaultdict(<class 'dict'>, {'General Knowledge': 9, 'Entertainment': {'Books': 10, 'Film': 11, 'Music': 12, 'Musicals & Theatres': 13, 'Television': 14, 'Video Games': 15, 'Board Games': 16, 'Comics': 29, 'Japanese Anime & Manga': 31, 'Cartoon & Animations': 32}, 'Science & Nature': 17, 'Science': {'Computers': 18, 'Mathematics': 19, 'Gadgets': 30}, 'Mythology': 20, 'Sports': 21, 'Geography': 22, 'History': 23, 'Politics': 24, 'Art': 25, 'Celebrities': 26, 'Animals': 27, 'Vehicles': 28})  # noqa: E501


def get_id_from_topic(topic: str) -> int:
    """Return opentdb's topic id from name."""
    topics = fetch_categories()

    if topic == "Random":
        topic = random.choice(list(topics.keys()))  # noqa: S311

    if isinstance(topics[topic], int):
        return topics[topic]
    return random.choice(list(topics[topic].values()))  # noqa: S311


def fetch_quizzes(
    number_of_q: int,
    category: int | None = None,
    difficulty: str | None = None,
    type: str | None = None,
) -> dict:
    """Return list of quizzes based on parameters."""
    url = f"https://opentdb.com/api.php?amount={number_of_q}"
    if category:
        url += f"&category={category}"
    if difficulty:
        url += f"&difficulty={difficulty}"
    if type:
        url += f"&type={type}"

    try:
        response = requests.get(url, timeout=(3, 5))
    except requests.exceptions.Timeout:
        print("Timed out")

    return response.json()["results"]


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
