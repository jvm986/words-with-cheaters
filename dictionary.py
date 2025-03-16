from typing import Dict, List, Optional


class TrieNode:
    def __init__(self) -> None:
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end_of_word: bool = False


class Dictionary:
    def __init__(self, filename: Optional[str] = None) -> None:
        self.root: TrieNode = TrieNode()
        self.word_length_buckets: Dict[int, List[str]] = {}
        if filename:
            self.load_from_file(filename)

        self.matches: Dict[str, List[str]] = {}

    def load_from_file(self, filename: str) -> None:
        with open(filename, "r") as file:
            for line in file:
                self.insert(line.strip())

    def insert(self, word: str) -> None:
        node: TrieNode = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

        word_length: int = len(word)
        if word_length not in self.word_length_buckets:
            self.word_length_buckets[word_length] = []
        self.word_length_buckets[word_length].append(word)

    def search(self, word: str) -> bool:
        node: TrieNode = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word

    def search_with_pattern(self, pattern: str) -> List[str]:
        if pattern in self.matches:
            return self.matches[pattern]

        pattern_length: int = len(pattern)
        if pattern_length not in self.word_length_buckets:
            return []

        results: List[str] = []
        for word in self.word_length_buckets[pattern_length]:
            if self._match_pattern(word, pattern):
                results.append(word)

        self.matches[pattern] = results
        return results

    def _match_pattern(self, word: str, pattern: str) -> bool:
        for w_char, p_char in zip(word, pattern):
            if p_char != "-" and w_char != p_char:
                return False
        return True
