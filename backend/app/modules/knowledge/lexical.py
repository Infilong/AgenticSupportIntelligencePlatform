"""Versioned derived search keys; never normalize citation text or source offsets."""

import re
import unicodedata
from collections import Counter

LEXICAL_VERSION = "nfkc-identifiers-cjk-bigrams-v1"
MAX_QUERY_TERMS = 128


class LexicalQueryTooLong(ValueError):
    pass


def frequencies(text):
    normalized = unicodedata.normalize("NFKC", text).casefold()
    tokens = []
    for match in re.finditer(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", normalized):
        token = match.group()
        tokens.append(token)
        if "-" in token or "_" in token:
            tokens.extend(re.split("[-_]", token))
    for match in re.finditer(r"[\u3040-\u30ff\u3400-\u9fff]+", normalized):
        run = match.group()
        tokens.extend(run[i : i + 2] for i in range(max(1, len(run) - 1)))
    return dict(Counter(tokens))


def query_terms(query):
    terms = sorted(frequencies(query))
    if len(terms) > MAX_QUERY_TERMS:
        raise LexicalQueryTooLong("Use at most 128 distinct lexical query terms")
    return terms


def default_frequencies(context):
    return frequencies(context.get_current_parameters()["text"])


def default_length(context):
    values = context.get_current_parameters()
    return sum(values["lexical_frequencies"].values())
