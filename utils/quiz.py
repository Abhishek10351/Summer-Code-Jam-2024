import csv
import html
import random
import time
from collections import defaultdict

# TODO: Convert to MongoDB
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Setup paths
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
ACTIVE_QUIZZES = CACHE_DIR / "active_quizzes.csv"
QUIZ_TOKENS = CACHE_DIR / "quiz_tokens.csv"


def fetch_categories() -> dict:
    """Create structured categories."""
    response = requests.get("https://opentdb.com/api_category.php", timeout=(3, 5))
    raw_categories = response.json()["trivia_categories"]

    structured_categories = defaultdict(dict)

    for category in raw_categories:
        topic: str = category["name"]
        id = category["id"]

        if ":" in topic:
            topic, subtopic = topic.split(": ")
            structured_categories[topic][subtopic] = id
        else:
            structured_categories[topic] = id

    return structured_categories


# defaultdict(<class 'dict'>, {'General Knowledge': 9, 'Entertainment': {'Books': 10, 'Film': 11, 'Music': 12, 'Musicals & Theatres': 13, 'Television': 14, 'Video Games': 15, 'Board Games': 16, 'Comics': 29, 'Japanese Anime & Manga': 31, 'Cartoon & Animations': 32}, 'Science & Nature': 17, 'Science': {'Computers': 18, 'Mathematics': 19, 'Gadgets': 30}, 'Mythology': 20, 'Sports': 21, 'Geography': 22, 'History': 23, 'Politics': 24, 'Art': 25, 'Celebrities': 26, 'Animals': 27, 'Vehicles': 28})  # noqa: E501

TOPICS_POOL = fetch_categories()


def has_sub_topic(topic: str) -> bool:
    """Determine if the topic name has subtopics or not."""
    return not isinstance(TOPICS_POOL[topic], int)


def get_topic_id(topic: str) -> int:
    """Return opentdb's root topic id from name."""
    return TOPICS_POOL[topic]


def get_sub_topic_id(topic: str, topic_id_correct_count: dict) -> int:
    """Return subtopic id from name and possibly count of how many times the topic is correct."""
    all_topic_ids = list(TOPICS_POOL[topic].values())
    if not topic_id_correct_count:
        return random.choice(all_topic_ids)  # noqa: S311

    sorted_correct_count = [x[0] for x in sorted(topic_id_correct_count.items(), key=lambda x: x[1], reverse=True)]
    return weighted_selection(all_topic_ids, sorted_correct_count)


def weighted_selection(all_ids: list, ordered_correct_count: list) -> int:
    """Assign weights algorithm. The higher the order of correct_count, the lower the weight."""
    weights = [len(all_ids)] * len(all_ids)

    max_weight = len(ordered_correct_count)
    for weight, element in enumerate(ordered_correct_count, start=1):
        if element in all_ids:
            weights[all_ids.index(element)] -= max_weight - weight + 1

    return random.choices(all_ids, weights=weights)[0]  # noqa: S311


def create_api_call(
    number_of_q: int,
    category: int | None = None,
    difficulty: str | None = None,
    type: str | None = None,
    ) -> str:
    """Create API call."""
    url = f"https://opentdb.com/api.php?amount={number_of_q}"
    if category:
        url += f"&category={category}"
    if difficulty:
        url += f"&difficulty={difficulty}"
    if type:
        url += f"&type={type}"
    return url


def fetch_json(url: str) -> list:
    """Fetch API from opentdb. Return False if bad response code."""
    print(url)
    try:
        response = requests.get(url, timeout=(3, 5))
    except requests.exceptions.Timeout:
        print("Timed out")

    print(response.json())

    if response.json()["response_code"] != 0:
        return False

    return response.json()["results"]


def fetch_quizzes(json: list) -> list:
    """Return list of quizzes based on json."""
    quizzes = []
    for quiz in json:
        quiz["question"] = html.unescape(quiz["question"])
        quiz["correct_answer"] = html.unescape(quiz["correct_answer"])
        quiz["incorrect_answers"] = [html.unescape(answer) for answer in quiz["incorrect_answers"]]

        quizzes.append(quiz)

    return quizzes


def get_quizzes_with_token(channel_id: int, api_url: str) -> list:
    """Return list of quizzes with token check."""
    # Reading all tokens
    channel_tokens = read_tokens()

    if current_token := channel_tokens.get(channel_id, False):
        # Current token works
        print("token work")
        if json := fetch_json(api_url + f"&token={current_token}"):
            return fetch_quizzes(json)

        # Current token no longer works
        print("token no longer work")
        time.sleep(5)
        new_token = requests.get("https://opentdb.com/api_token.php?command=request", timeout=3).json()["token"]
        print(new_token)
        channel_tokens[channel_id] = new_token
        write_tokens(channel_tokens)
        return fetch_quizzes(fetch_json(api_url + f"&token={new_token}"))

    # No token yet
    print("no token yet")
    new_token = requests.get("https://opentdb.com/api_token.php?command=request", timeout=3).json()["token"]
    channel_tokens[channel_id] = new_token
    write_tokens(channel_tokens)
    return fetch_quizzes(fetch_json(api_url + f"&token={new_token}"))


def read_tokens() -> dict:
    """Return all currently tokens."""
    channel_tokens = {}
    try:
        with Path.open(QUIZ_TOKENS) as file:
            reader = csv.reader(file)
            channel_tokens = {int(row[0]): row[1] for row in reader}
    except FileNotFoundError:
        pass
    return channel_tokens


def write_tokens(channel_tokens: dict) -> None:
    """Write all currently active quizzes to csv."""
    with Path.open(QUIZ_TOKENS, mode="w", newline="") as file:
        writer = csv.writer(file)
        for channel_id in channel_tokens:
            writer.writerow([channel_id, channel_tokens[channel_id]])


def read_active_quizzes() -> list:
    """Return all currently active quizzes."""
    active_quizzes = []
    try:
        with Path.open(ACTIVE_QUIZZES) as file:
            reader = csv.reader(file)
            active_quizzes = [int(rows[0]) for rows in reader]
    except FileNotFoundError:
        pass
    return active_quizzes


def write_active_quizzes(active_quizzes: list) -> None:
    """Write all currently active quizzes to csv."""
    with Path.open(ACTIVE_QUIZZES, mode="w", newline="") as file:
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


def learn_more_url(question: str) -> str:
    """Return first wikipedia google search for the question.

    Thanks to https://www.reddit.com/r/learnpython/comments/supub9/how_to_get_url_of_the_first_google_search_result/
    """
    query = question + " site:en.wikipedia.org"

    url = "https://www.google.com/search"

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82",  # noqa: E501
    }
    parameters = {"q": query}

    content = requests.get(url, headers=headers, params=parameters, timeout=3).text
    soup = BeautifulSoup(content, "html.parser")

    search = soup.find(id="search")
    first_link = search.find("a")

    return first_link["href"]
