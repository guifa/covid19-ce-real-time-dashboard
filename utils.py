
from unicodedata import normalize
from Levenshtein import distance

def remove_accents(txt):
    return normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')

def remove_special_characters(text):
    a_string = text
    alphanumeric = ""

    for character in a_string:
        if character == " ":
            alphanumeric += character
        else:
            if character.isalnum():
                alphanumeric += character

    return alphanumeric

def clean_text(raw_text):
    cleaned_text = remove_special_characters(raw_text)
    cleaned_text = cleaned_text.strip()
    cleaned_text = remove_accents(cleaned_text)
    cleaned_text = cleaned_text.upper()

    return cleaned_text

def min_edit_distance(word, list_of_words):    
    if word == 'NAO INFORMADO':
        return 'NAO INFORMADO'

    word_dict = {}
    
    for aux in list_of_words:
        word_dict[aux] = distance(aux, word)

    return min(word_dict.keys(), key=(lambda k: word_dict[k]))