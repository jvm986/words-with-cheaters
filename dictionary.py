class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False


class Dictionary:
    def __init__(self, filename=None):
        self.root = TrieNode()
        if filename:
            self.load_from_file(filename)

    def load_from_file(self, filename):
        with open(filename, "r") as file:
            for line in file:
                self.insert(line.strip().lower())

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word

    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True  # Prefix exists
