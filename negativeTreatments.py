import requests
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv
import os
import time
import argparse
import re

load_dotenv()

# Function to process paragraphs and check for the presence of any negative indicators in the text. This improves speed by only passing potentially relevant paragraphs to chatGPT.

# Filters through all paragraphs, collecting paragraphs that have negative indicators.
def process_paragraphs(soup, indicators):
    paragraphs = soup.find_all("p")
    return [
        p.get_text()
        for p in paragraphs
        if any(indicator in p.get_text() for indicator in indicators)
    ]

# Function to extract treatment from a paragraph, up to 3 retries in case of errors (such as chatGPT having too many simultaneous requests)
# Interactts with OpenAI API to analyze a paragraph of legal text to extract potential negative treatment of legal cases.
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
                        "content": f"{paragraph} Does this paragraph indicate negative treatment of a legal case?  Identify which one. Structure your response like so, Negatively treated case: [case name], nature of the negative treatment: [nature], explanation for why you determined this case was negatively treated: [explanation]. Make sure the formatting is precisely as I have outlined, stating the category of information, followed by a colon, and a ',' after each explanation. For the case name, do not include any information other than the full name of the case.",
                    },
                ],
            )
            treatment = result["choices"][0]["message"]["content"]
            time.sleep(5)
            break
        except Exception as e:
            print(e)
            print("Waiting 60 seconds before retrying...")
            time.sleep(60)
            retries -= 1
    return treatment

def extract_negative_treatments(slug):
    url = f"https://casetext.com/api/search-api/doc/{slug}/html"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    case_text = soup.get_text()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # These are negative treatment indicators. If a paragraph contains these, chatGPT will analyze those paragraphs for negative treatment.
    NEGATIVE_TREATMENT_INDICATORS = [
        "overrul",
        "disagree",
        "limit",
        "unconstitutional",
        "preempt",
        "incorrect",
        "distinguish",
        "abrogat"
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
        # The below regex is meant to capture the case citation and nothing more. I do not want to extract the full text of the passage, only the case citation.
        match = re.search(r'(\b' + re.escape(case) + r'\b.*?(?=\s{2,}|\n|$))', case_text[citation_start_index:])
        if match:
          treatments[case]["citation"] = match.group(0)
        else:
          treatments[case]["citation"] = "Citation not found in the text"
      else:
        treatments[case]["citation"] = "Case not found in the text."

    if not treatments:
        return "No negative treatment found."

    formatted_treatments = []
    for case, treatment in treatments.items():
      ## the below filters out things other than cases that receive negative treatment, such as legal doctrines.
      if case not in ["Not Applicable", "No specific case mentioned", "Doctrine"] and "Case not found in the text." not in treatment["citation"]:
        formatted_treatments.append(
          f'Case: {case}\nNature: {treatment["nature"]}\nText: {treatment["text"]}\nExplanation: {treatment["explanation"]}\nCitation: {treatment["citation"]}\n---'
        )
    return "\n".join(formatted_treatments)

def parse_arguments():
  parser = argparse.ArgumentParser(
    description="Extract negative treatment of other cases from the passed-in case"
  )
  parser.add_argument(
    "slug",
    type=str,
    help="The case we are analyzing for negative treatment of other cases",
  )
  args = parser.parse_args()
  return args

def main():
    args = parse_arguments()
    print(extract_negative_treatments(args.slug))

if __name__ == "__main__":
    main()

