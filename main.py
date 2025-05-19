import os
import requests
from collections import Counter
from bs4 import BeautifulSoup
import re

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

# Funkcija vārdšķiras iegūšanai
def get_word_pos(word):
    if word in pos_lookup:
        return pos_lookup[word]

    url = f"https://tezaurs.lv/{word}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
    except requests.RequestException:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    pos_tags = soup.find_all(["span", "p", "div"], class_=re.compile(r"(part-of-speech|pos|grammatical)"))
    for tag in pos_tags:
        text = tag.get_text(strip=True).lower()
        if text:
            return text

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

# Vārdi, kurus vēlamies izslēgt no rezultāta
exclude_words = {"apvidvārds", "žargonisms", "locīšana", "frazēma", "idioma", "kolokācija", "sarunvaloda", "taksons", "piemēri", "frazeoloģisms", "tulkojumi", "vārdkoptermins"}

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
}

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

lemmas = [get_lemma(word) for word in words]
lemma_counts = Counter(lemmas)
repeated_lemmas = [lemma for lemma, count in lemma_counts.items() if count > 1 and lemma]

# Funkcija sinonīmu izvēlei
def select_synonyms(repeated_lemmas):
    lemma_to_synonym_map = {}

    while True:
        if not repeated_lemmas:
            print("Nav atkārtojošu vārdu sinonīmu izvēlei.")
            break
        
        print("\n🔁 Atkārtojošie vārdi tekstā:")
        print(", ".join(f"{i}. {lemma}" for i, lemma in enumerate(repeated_lemmas, 1)))

        selection = input("\nIevadi to vārdu numurus, kuriem meklēt sinonīmus (piemēram: 1,3,5), vai '0' lai beigtu: ").strip()
        if selection == '0':
            break

        chosen_indices = []
        try:
            chosen_indices = [int(x.strip()) for x in selection.split(",") if x.strip().isdigit()]
        except ValueError:
            print("Kļūda: Lūdzu ievadi skaitļus atdalītus ar komatu.")
            continue

        # Filtrē nederīgus indeksus
        chosen_indices = [i for i in chosen_indices if 1 <= i <= len(repeated_lemmas)]
        if not chosen_indices:
            print("Nav derīgu izvēļu.")
            continue

        for idx in chosen_indices:
            lemma = repeated_lemmas[idx-1]
            if lemma in lemma_to_synonym_map:
                print(f"Sinonīmi vārdam '{lemma}' jau ir izvēlēti.")
                continue

            pos = get_word_pos(lemma)
            if pos == "saiklis":
                print(f"Vārds '{lemma}' ir saiklis, sinonīmi netiek meklēti.")
                continue

            synonyms = extract_single_word_synonyms(get_hidden_synonyms(lemma))
            if synonyms:
                print(f"\nSinonīmi vārdam '{lemma}' ({pos if pos else 'vārdšķira nav atrasta'}):")
                for i, word in enumerate(synonyms, 1):
                    print(f"{i}. {word}")

                while True:
                    input_num = input(f"Ievadi sinonīma skaitli vārdam '{lemma}', vai 0, lai izlaistu: ")
                    if not input_num.isdigit():
                        print("Ievadiet skaitli.")
                    else:
                        input_num = int(input_num)
                        if input_num == 0:
                            break
                        elif 1 <= input_num <= len(synonyms):
                            chosen_synonym = synonyms[input_num - 1]
                            lemma_to_synonym_map[lemma] = chosen_synonym
                            break
                        else:
                            print("Skaitlis pārāk liels.")
            else:
                print(f"Sinonīmi vārdam '{lemma}' netika atrasti.")
        
        # Pēc apstrādes dod iespēju izvēlēties vēl vai beigt
        cont = input("\nVai vēlies turpināt izvēlēties citus vārdus? (j/n): ").strip().lower()
        if cont != 'j':
            break

    return lemma_to_synonym_map


print("\n🔁 Atkārtojošie vārdi tekstā:")
print(", ".join(f"{i}. {lemma}" for i, lemma in enumerate(repeated_lemmas, 1)))

lemma_to_synonym_map = select_synonyms(repeated_lemmas)

# Funkcija, lai noteiktu sufiksu (piem., locījuma galotni) vārdam
def get_suffix_from_word(word, lemma):
    word = word.lower()
    lemma = lemma.lower()
    if word == lemma or not word.startswith(lemma):
        return ''
    return word[len(lemma):]

# Teksta aizvietošana funkcija
def replace_repeated_words(text, repeated_lemmas):
    words = re.findall(r'\b\w+\b|[^\w\s]', text, re.UNICODE)
    modified_text = []
    prev_end_punct = True
    lemma_occurrence_count = {lemma: 0 for lemma in repeated_lemmas}

    for i, word in enumerate(words):
        if re.fullmatch(r'[.!?]', word):
            prev_end_punct = True
            modified_text.append(word)
            continue

        original_word = word
        word_lower = word.lower()
        lemma = get_lemma(word_lower)

        if lemma in repeated_lemmas:
            lemma_occurrence_count[lemma] += 1
            if lemma in lemma_to_synonym_map and lemma_occurrence_count[lemma] % 2 == 0:
                synonym = lemma_to_synonym_map[lemma]
                suffix = get_suffix_from_word(word_lower, lemma)
                synonym_with_suffix = synonym + suffix

                # Oriģinālais vārds + sinonīms iekavās
                replacement = f"{original_word} ({synonym_with_suffix})"

                if prev_end_punct:
                    replacement = replacement.capitalize()
                word = replacement

            elif prev_end_punct:
                word = word.capitalize()

        elif prev_end_punct and word[0].isalpha():
            word = word.capitalize()

        modified_text.append(word)
        prev_end_punct = False

    return ''.join([
        ' ' + w if not re.fullmatch(r'[,.!?;:]$', w) and i != 0 else w
        for i, w in enumerate(modified_text)
    ])

modified_text = replace_repeated_words(text, repeated_lemmas)
with open("izvade.txt", "w", encoding="utf-8") as f:
    f.write(modified_text)

print("\nAizvietotais teksts saglabāts failā 'izvade.txt'.")
