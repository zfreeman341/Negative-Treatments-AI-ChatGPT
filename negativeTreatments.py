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


def extract_negative_treatments(slug):
    # Fetch the HTML
    url = f"https://casetext.com/api/search-api/doc/{slug}/html"
    response = requests.get(url)
    html = response.text

    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")

    openai.api_key = os.getenv("OPENAI_API_KEY")
    print(os.getenv("OPENAI_API_KEY"))

    # assume negative treatment, update accordingly
    negative_treatment_indicators = [
        "overrul",
        "disagree",
        "limit",
        "unconstitutional",
        "preempt",
        "incorrect",
        "overrul",
    ]

    case_text = soup.get_text()

    treatments = {}

    paragraphs = soup.find_all("p")

    paragraphs_to_process = []

    for p in paragraphs:
        paragraph = p.get_text()
        if any(indicator in paragraph for indicator in negative_treatment_indicators):
            paragraphs_to_process.append(paragraph)

            # process paragraphs likely to contain indcators
    print(paragraphs_to_process)
    for paragraph in paragraphs_to_process:
        retries = 3
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
                            "content": f"{paragraph} Does this paragraph indicate negative treatment of a legal case? Identify which one. Structure your response like so, Negatively treated case: [case name], nature of the negative treatment: [nature], explanation for why you determined this case was negatively treated: [explanation]",
                        },
                    ],
                )

                response = result["choices"][0]["message"]["content"]
                print(response)
                if "negative treatment" in response.lower():
                    treated_case = "placeholder"
                    treatments[treated_case] = {
                        "nature": "placeholder",
                        "text": paragraph,
                        "explanation": response,
                    }
                time.sleep(5)
                break

            except openai.error.RateLimitError as e:
                print(e)
                print("Rate limit exceeded. Waiting for 60 seconds before retrying...")
                time.sleep(60)
                retries -= 1
    if not treatments:
        return "No negative treatment found."

    return treatments

def main():
  parser = argparse.ArgumentParser(description='Extract negative treatment of other cases from the passed-in case')
  parser.add_argument('slug', type=str, help='The case we are analyzing for negative treatment of others')
  args = parser.parse_args()

  print(extract_negative_treatments(args.slug))

if __name__ == "__main__":
  main()

# print(extract_negative_treatments("littlejohn-v-state-7"))
