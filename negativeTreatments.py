import requests
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv
import os
import spacy
import time
import argparse

load_dotenv()
nlp = spacy.load("en_core_web_sm")


def fetch_html(url):
    return requests.get(url).text


def parse_html(html):
    return BeautifulSoup(html, "html.parser")


def process_paragraphs(soup, indicators):
    paragraphs = soup.find_all("p")
    return [
        p.get_text()
        for p in paragraphs
        if any(indicator in p.get_text() for indicator in indicators)
    ]


def extract_treatment(paragraph, retries=3):
    treatment = None
    while retries > 0:
        try:
            print("Connecting to chatGPT...")
            result = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal assistant helping me identify negative treatment of other cases in this paragraph.",
                    },
                    {
                        "role": "system",
                        "content": f"{paragraph} Does this paragraph indicate negative treatment of a legal case?  Identify which one. Structure your response like so, Negatively treated case: [case name], nature of the negative treatment: [nature], explanation for why you determined this case was negatively treated: [explanation]. Make sure the formatting is precisely as I have outlined, stating the category of information, followed by a colon, and a ',' after each explanation.",
                    },
                ],
            )
            treatment = result["choices"][0]["message"]["content"]
            print(treatment)
            time.sleep(5)
            break
        except Exception as e:
            print(e)
            print("Waiting 60 seconds before retrying...")
            time.sleep(60)
            retries -= 1
    return treatment


def extract_negative_treatments(slug):
    # Fetch the HTML
    url = f"https://casetext.com/api/search-api/doc/{slug}/html"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    case_text = soup.get_text()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # assume negative treatment, update accordingly
    NEGATIVE_TREATMENT_INDICATORS = [
        "overrul",
        "disagree",
        "limit",
        "unconstitutional",
        "preempt",
        "incorrect",
        "distinguish",
    ]

    treatments = {}

    paragraphs_to_process = process_paragraphs(soup, NEGATIVE_TREATMENT_INDICATORS)

    for paragraph in paragraphs_to_process:
        treatment = extract_treatment(paragraph)
        if treatment and "negative treatment" in treatment.lower():
            split_response = treatment.split(", ")
            if len(split_response) >= 3:
              treated_case = split_response[0].split(": ")[1] if ": " in split_response[0] else "Not provided"
              nature = split_response[1].split(": ")[1] if ": " in split_response[1] else "Not provided"
              explanation = split_response[2].split(": ")[1] if ": " in split_response[2] else "Not provided"
              treatments[treated_case] = {
                    "nature": nature,
                    "text": paragraph,
                    "explanation": explanation,
                }

                # process paragraphs likely to contain indcators

    for case in treatments.keys():
        citation_start_index = case_text.find(case)
        if citation_start_index != -1:
            citation_end_index = case_text.find(".", citation_start_index)
            if citation_end_index != 0.1:
                treatments[case]["citation"] = case_text[citation_start_index]
            else:
                treatments[case]["citation"] = "Citation not found in the text"
        else:
            treatments[case]["citation"] = "Case not found in the text"

    if not treatments:
        return "No negative treatment found."

    formatted_treatments = []
    for case, treatment in treatments.items():
        # if "v." in case:
        formatted_treatments.append(
          f'Case: {case}\nNature: {treatment["nature"]}\nText: {treatment["text"]}\nExplanation: {treatment["explanation"]}\n---'
          )
    return "\n".join(formatted_treatments)
##

def main():
    parser = argparse.ArgumentParser(
        description="Extract negative treatment of other cases from the passed-in case"
    )
    parser.add_argument(
        "slug",
        type=str,
        help="The case we are analyzing for negative treatment of others",
    )
    args = parser.parse_args()

    print(extract_negative_treatments(args.slug))


if __name__ == "__main__":
    main()

# print(extract_negative_treatments("littlejohn-v-state-7"))
