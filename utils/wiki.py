import json
import os
import random
import re

import google.generativeai as genai
import requests
import wikipedia
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
WIKI_REQUEST = "http://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles="


genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def get_wiki_facts(prompt: str, number: int = 5) -> list:
    """Return {number} amount of facts based on {prompt}."""
    return random.sample(split_into_sentences(wikipedia.summary(prompt, auto_suggest=False)), k=number)


def create_false_statement(fact: str) -> str:
    """Get a false fact based on a true fact."""
    prompt = f"Create a false fact for a True False quiz based on this fact: {fact} in one line. Answer directly."
    response = model.generate_content(prompt)
    return response.text


# Credits to https://stackoverflow.com/questions/30595918/is-there-any-api-to-get-image-from-wiki-page
def get_wiki_image(search_term: str) -> str | bool:
    """Return featured image URL of search."""
    try:
        result = wikipedia.search(search_term, results = 1)
        wikipedia.set_lang("en")
        wkpage = wikipedia.WikipediaPage(title = result[0])
        title = wkpage.title
        response  = requests.get(WIKI_REQUEST+title, timeout=3)
        json_data = json.loads(response.text)
        return next(iter(json_data["query"]["pages"].values()))["original"]["source"]
    except Exception:
        return False


# Credits to https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = r"(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"  # noqa: E501
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|edu|me)"
digits = "([0-9])"
multiple_dots = r"\.{2,}"

def split_into_sentences(text: str) -> list[str]:
    """Split the text into sentences.

    If the text contains substrings "<prd>" or "<stop>", they would lead
    to incorrect splitting because they are used as markers for splitting.

    :param text: text to be split into sentences
    :type text: str

    :return: list of sentences
    :rtype: list[str]
    """
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    text = re.sub(multiple_dots, lambda match: "<prd>" * len(match.group(0)) + "<stop>", text)
    if "Ph.D" in text:
        text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub(r"\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text:
        text = text.replace(".”","”.")
    if '"' in text:
        text = text.replace('."','".')
    if "!" in text:
        text = text.replace('!"','"!')
    if "?" in text:
        text = text.replace('?"','"?')
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences and not sentences[-1]:
        sentences = sentences[:-1]
    return sentences
