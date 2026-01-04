class KMPSearcher:
    def build_lps(self,pattern: str) -> list[int]:
        lps = [0] * len(pattern)
        j = 0  # length of previous longest prefix suffix

        for i in range(1, len(pattern)):
            while j > 0 and pattern[i] != pattern[j]:
                j = lps[j - 1]

            if pattern[i] == pattern[j]:
                j += 1
                lps[i] = j

        return lps

    def kmp_search(self,text: str, pattern: str) -> list[int]:
        print("KMP Search called with text:", text, "and pattern:", pattern)
        if not pattern:
            return []

        lps = self.build_lps(pattern)
        matches = []

        j = 0  # index for pattern

        for i in range(len(text)):
            while j > 0 and text[i] != pattern[j]:
                j = lps[j - 1]

            if text[i] == pattern[j]:
                j += 1

            if j == len(pattern):
                matches.append(i - j + 1)
                j = lps[j - 1]

        return len(matches) > 0
