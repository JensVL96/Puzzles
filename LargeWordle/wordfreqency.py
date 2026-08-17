from wordfreq import zipf_frequency
import re

# Read the word list
with open("wordlist.txt", "r") as f:
    text = f.read()

words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

words = [
    w for w in re.findall(r"\b[a-zA-Z]+\b", text)
    if w.islower()
]

word_frequencies = {
    word: zipf_frequency(word, 'en')
    for word in set(words)
}

most_common_globally = max(word_frequencies, key=word_frequencies.get)

print(most_common_globally, word_frequencies[most_common_globally])