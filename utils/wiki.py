import os
import random

import discord
import google.generativeai as genai
import wikipedia
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")

bot = commands.Bot(command_prefix=".", intents=discord.Intents.default())

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def get_wiki_results(prompt: str, number: int = 5) -> list:
    """Return {number} amount of facts based on {prompt}."""
    #splitting the summary into sentences. Checks for garbage sentences
    page_list = [str(i) for i in wikipedia.summary(prompt, auto_suggest=False).split(".") if len(i) in range(50, 500)]

    facts = []
    for _ in range(number):
        random_fact = random.choice(page_list)  # noqa: S311
        while random_fact in facts:
            random_fact = random.choice(page_list)  # noqa: S311
        facts.append(random_fact+".")

    return facts

def get_false_fact(fact: str) -> str:
    """Get a false fact based on a true fact."""
    prompt = f"Create a false fact for a True False quiz based on this fact: {fact} in one line. Answer directly."
    response = model.generate_content(prompt)
    return response.text
