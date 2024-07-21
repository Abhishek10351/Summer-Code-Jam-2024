import csv
from collections import defaultdict

import requests

#TODO: Convert to MongoDB
CSV_FILE = "cache/active_quizzes.csv"

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

    # return response.json()["results"]


# for i, quiz in enumerate(fetch_quizzes()):
#     answers = [quiz["correct_answer"]] + quiz["incorrect_answers"]
#     shuffle(answers)

#     print(f"{i+1}. {quiz["question"]}")
#     print("\t".join(answers))
#     print()


def read_active_quizzes():
    active_quizzes = {}
    try:
        with open(CSV_FILE) as file:
            reader = csv.reader(file)
            active_quizzes = {int(rows[0]): rows[1] == "True" for rows in reader}
    except FileNotFoundError:
        pass
    return active_quizzes

def write_active_quizzes(active_quizzes):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        for channel_id, status in active_quizzes.items():
            writer.writerow([channel_id, status])

def is_quiz_active(channel_id):
    active_quizzes = read_active_quizzes()
    return active_quizzes.get(channel_id, False)

def set_quiz_status(channel_id, status):
    active_quizzes = read_active_quizzes()
    active_quizzes[channel_id] = status
    write_active_quizzes(active_quizzes)
