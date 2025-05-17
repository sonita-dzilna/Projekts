import os
import requests
from collections import Counter
from bs4 import BeautifulSoup
import re

# 1. Pārbauda un izveido failu ievadei
filename = "ievade.txt"
if not os.path.exists(filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("Ievadi savu tekstu šeit...")

print(f"\nLūdzu, ievadi tekstu failā: {filename}")
input("Kad esi gatavs, nospied Enter...")

# 2. Nolasa failu un apstrādā vārdus
with open(filename, "r", encoding="utf-8") as f:
    text = f.read().lower()

words = re.findall(r'\b[a-zāčēģīķļņšūž\-]+\b', text.lower())

#noteikt lemma - vārda pamatforma
def get_lemma(word):
    url = f"https://tezaurs.lv/{word}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return word
    except requests.RequestException:
        return word

    soup = BeautifulSoup(response.text, "html.parser")

    # Mēģina atrast bloku ar tekstu "forma šķirklī"
    for div in soup.find_all("div", class_="listItem"):
        if "forma šķirklī" in div.get_text().lower():
            link = div.find("a", href=True)
            if link:
                lemma = link.get_text(strip=True).lower()
                return lemma
            
    return word

lemmas = [get_lemma(word) for word in words]
lemma_counts = Counter(lemmas)
repeated_lemmas = [lemma for lemma, count in lemma_counts.items() if count > 1 and lemma]

print("\n🔁 Atkārtojošie vārdi tekstā:")
print(", ".join(repeated_lemmas) if repeated_lemmas else "Nav atkārtojošu vārdu.")

# Vārdi, kurus vēlamies izslēgt no rezultāta
exclude_words = {"apvidvārds", "žargonisms", "locīšana", "frazēma", "idioma", "kolokācija", "sarunvaloda", "taksons", "piemēri", "frazeoloģisms", "tulkojumi", "vārdkoptermins"}

def extract_single_word_synonyms(raw_list):
    cleaned = []
    for item in raw_list:
        item = re.sub(r'\d+', '', item)
        item = item.strip().lower()
        if item in exclude_words:
            continue
        if item and (' ' not in item) and re.match(r'^[a-zāčēģīķļņšūž-]+$', item):
            cleaned.append(item)
    return sorted(set(cleaned))

# Lokāls vārdšķiru vārdnīca populārākajiem vārdiem
pos_lookup = {
    "un": "saiklis",
    "vai": "saiklis",
    "bet": "saiklis",
    "par": "prievārds",
    "ar": "prievārds",
    "uz": "prievārds",
    "es": "vietniekvārds",
    "tu": "vietniekvārds",
    "viņš": "vietniekvārds",
    "mēs": "vietniekvārds",
    "jūs": "vietniekvārds",
    "viņi": "vietniekvārds",
    "tas": "vietniekvārds",
    "šo": "vietniekvārds",
    "pie": "prievārds",
    "domāt": "darbības vārds",
    "emocijas": "lietvārds",
    "suns": "lietvārds",
    "rīts": "lietvārds",
    # papildini pēc vajadzības
}

# Funkcija vārdšķiras iegūšanai
def get_word_pos(word):
    # 1. Pārbauda lokālo vārdnīcu
    if word in pos_lookup:
        return pos_lookup[word]

    # 2. Scrapo no Tezaurs.lv
    url = f"https://tezaurs.lv/{word}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
    except requests.RequestException:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Meklē elementus, kur parasti ir vārdšķira
    # Piemēram, mēģinām atrast <p> vai <span> ar atbilstošu klasi
    pos_tags = soup.find_all(["span", "p", "div"], class_=re.compile(r"(part-of-speech|pos|grammatical)"))
    for tag in pos_tags:
        text = tag.get_text(strip=True).lower()
        if text:
            return text

    # Ja nav atrasts ar speciālu klasi, meklē tekstā vārdšķiras vārdus
    text = soup.get_text(separator="\n").lower()
    pos_words = ["lietvārds", "darbības vārds", "īpašības vārds", "skaitļa vārds", "prievārds", "saiklis", "piedēklis", "daļa", "apstākļa vārds", "vietniekvārds"]
    for pw in pos_words:
        if pw in text:
            return pw

    return None

# Funkcija sinonīmu iegūšanai
def get_hidden_synonyms(word):
    url = f"https://tezaurs.lv/{word}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    synonyms = set()

    for block in soup.find_all(["div", "ul"], class_="synonyms"):
        for item in block.find_all(["li", "span"]):
            text = item.get_text(strip=True)
            if text:
                synonyms.add(text)

    for hidden in soup.find_all(style=True):
        style = hidden['style'].replace(" ", "").lower()
        if 'display:none' in style:
            for item in hidden.find_all(["li", "span"]):
                text = item.get_text(strip=True)
                if text:
                    synonyms.add(text)

    return list(synonyms)

# 4. Iegūst vārdus ar vārdšķiru un sinonīmus, izvada tikai tos vārdus, kam ir atrasti sinonīmi
print("\n==== REZULTĀTI ====")
for lemma in repeated_lemmas:
    pos = get_word_pos(lemma)
    if pos == "saiklis":
        continue
    synonyms = extract_single_word_synonyms(get_hidden_synonyms(lemma))
    if synonyms:
        print(f"\nSinonīmi vārdam '{lemma}' ({pos if pos else 'vārdšķira nav atrasta'}):")
        print(", ".join(synonyms))
