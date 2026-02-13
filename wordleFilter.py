
from wordfreq import zipf_frequency
import re

words = []
with open("wordlist.txt", "r", encoding="utf-8") as f:
    for line in f:
        # split on whitespace (tabs/spaces), strip newlines
        parts = line.strip().split()
        words.extend(parts)

def parse_rules_from_string(rules_str):
    """
    Parse a single string of rules into include, exclude, forbidden, must-have lists.
    Syntax:
        - "i4"     -> include 'i' at position 4
        - "!n6"    -> exclude 'n' at position 6
        - "!z"     -> forbid 'z' anywhere
        - "*e"     -> word must contain 'e' anywhere
    """
    include_rules = []
    exclude_rules = []
    forbidden_letters = []
    must_have_letters = []

    for r in rules_str.split():
        r = r.strip()
        if not r:
            continue
        if r.startswith("!"):
            content = r[1:]
            if len(content) == 1:
                forbidden_letters.append(content)
            else:
                exclude_rules.append((content[0], int(content[1:])))
        elif r.startswith("*"):
            # must-have letter anywhere
            must_have_letters.append(r[1])
        else:
            # include at position
            include_rules.append((r[0], int(r[1:])))
    
    return include_rules, exclude_rules, forbidden_letters, must_have_letters

def filter_words(words, include_rules=None, exclude_rules=None, forbidden_letters=None, must_have_letters=None):
    """
    words: list of words
    include_rules: list of (letter, position) pairs -> must have letter at position
    exclude_rules: list of (letter, position) pairs -> exclude if letter is at position
    forbidden_letters: list of letters -> exclude if letter occurs anywhere
    must_have_letters: list of letters -> include only if word contains at least one
    """
    include_rules = include_rules or []
    exclude_rules = exclude_rules or []
    forbidden_letters = forbidden_letters or []
    must_have_letters = must_have_letters or []

    result = []
    for word in words:
        w = word.lower()
        reject = False

        # inclusion rules (must match specific positions)
        for letter, position in include_rules:
            if len(w) < position or w[position - 1] != letter.lower():
                reject = True
                break

        # exclusion rules (cannot match specific positions)
        if not reject:
            for letter, position in exclude_rules:
                if len(w) >= position and w[position - 1] == letter.lower():
                    reject = True
                    break

        # forbidden letters anywhere
        if not reject:
            for letter in forbidden_letters:
                if letter.lower() in w:
                    reject = True
                    break

        # must-have letters anywhere
        if not reject and must_have_letters:
            if not all(letter.lower() in w for letter in must_have_letters):
                reject = True

        if not reject:
            result.append(word)

    return result

# Include "i" at 4th position = i4
# Exclude "e" at 2nd position = !e2
# Exclude all words containing the letter "z" = !z
# rule_str = "!s1 !s3 !r3 !s4 s5 !r1 !o2 !c3 !k *c"
rule_str = "!g1 a2 !n3 !o3 !a5"

include, exclude, forbidden, must_have = parse_rules_from_string(rule_str)
filtered = filter_words(
    words,
    include_rules=include,
    exclude_rules=exclude,
    forbidden_letters=forbidden,
    must_have_letters=must_have
)

scored_words = [
    (w, zipf_frequency(w, "en"))
    for w in filtered
]
scored_words.sort(key=lambda x: x[1], reverse=True)

for word, freq in scored_words:
    print(f"{word:15} {freq:.2f}")