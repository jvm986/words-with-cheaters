import sys

DICTIONARY_FILE = "dictionary.txt"


def add_word_to_dictionary(new_word: str) -> None:
    if not new_word.isalpha():
        print("Word must contain only letters")
        sys.exit(1)

    word: str = new_word.upper()

    try:
        with open(DICTIONARY_FILE, "r") as f:
            words = set(f.read().splitlines())
    except FileNotFoundError:
        raise FileNotFoundError("Dictionary file not found. Please create a dictionary.txt file.")

    if word in words:
        print(f"'{word}' is already in the dictionary.")
        return

    words.add(word)
    sorted_words = sorted(words)

    with open(DICTIONARY_FILE, "w") as f:
        f.write("\n".join(sorted_words))

    print(f"Added '{word}' to the dictionary.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <word>")
        sys.exit(1)

    add_word_to_dictionary(sys.argv[1])
