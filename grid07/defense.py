"""Layered prompt-injection defense.

Layer 1 — Normalisation: undo common obfuscations (Unicode look-alikes,
          zero-width characters, leetspeak, spaced-out letters) before matching.
Layer 2 — Detection: weighted rules produce a risk score instead of a single
          boolean, so weak signals ("please apologise") don't trip the alarm on
          their own but combine with stronger ones.
Layer 3 — Spotlighting: untrusted thread text is fenced and any attempt to
          forge our own prompt delimiters is neutralised.
Layer 4 — Output guard: the generated reply is checked for persona breaks
          (apologies, assistant-speak, prompt leakage) before it is returned.

Detection quality is measured against ``tests/data/injection_corpus.jsonl``;
run ``python -m grid07.eval_defense`` to reproduce the numbers in the README.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# ── Layer 1: normalisation ──────────────────────────────────────────────────

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿­"), None)
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})
# "i g n o r e" → "ignore": collapse runs of single letters separated by spaces/dots.
_SPACED = re.compile(r"\b(?:[a-z][\s.\-_*]){3,}[a-z]\b")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_ZERO_WIDTH).lower()
    text = text.translate(_LEET)
    text = _SPACED.sub(lambda m: re.sub(r"[\s.\-_*]", "", m.group(0)), text)
    text = re.sub(r"[^\w\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ── Layer 2: weighted detection ─────────────────────────────────────────────


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    weight: float


def _r(name: str, pattern: str, weight: float) -> Rule:
    return Rule(name, re.compile(pattern), weight)


_ANY = r"(?:\w+ ){0,3}"  # allow a few filler words: "ignore all of your previous instructions"

RULES: tuple[Rule, ...] = (
    _r(
        "override",
        rf"\b(ignore|disregard|forget|override|bypass|skip) {_ANY}(previous|prior|above|earlier|all|your|the|system) {_ANY}(instructions?|rules?|prompts?|directives?|guidelines?|persona|context|programming)",
        1.0,
    ),
    _r(
        "role_reassign",
        r"\b(from now on,? you (are|will)|you will now act|act as (if you were |though you were )?(a|an|my)\b|pretend (to be|you are|you're)|roleplay as (a|an|my)\b|switch (to|into) (a|an) \w+ (mode|persona|role))",
        0.7,
    ),
    _r("you_are_now", r"\b(you are now|you're now) (a|an|my)\b", 0.45),
    _r("new_persona", r"\b(your|a) new (role|persona|identity|instructions?|task|objective)\b", 0.7),
    _r(
        "prompt_leak",
        r"\b(reveal|show|print|repeat|output|tell me|what is|what are|leak|dump) (me )?(your|the (system|hidden|initial|original)) (system |hidden |initial |original )?(prompt|instructions|rules)\b|\binstructions you were given\b",
        0.9,
    ),
    _r(
        "system_spoof",
        r"\b(system|admin|developer|operator|root) ?(message|override|note|instruction|prompt)\b|^\s*system\s|\bnew system prompt\b",
        0.8,
    ),
    _r(
        "jailbreak",
        r"\b(jailbreak|dan mode|(enable|activate|enter) (developer|god|admin) mode|(developer|god|admin) mode (is )?(activated|enabled|on)|do anything now|unfiltered|no restrictions|without (any )?restrictions)\b",
        0.9,
    ),
    _r(
        "tone_coercion",
        r"\b(apologi[sz]e|say (you'?re|you are) sorry|be (polite|nice|respectful)|customer (service|support))\b",
        0.35,
    ),
    _r("authority_claim", r"\b(i am|i'm) (your|the) (developer|creator|admin|operator|owner)\b", 0.5),
)

DEFAULT_THRESHOLD = 0.6


@dataclass(frozen=True)
class InjectionReport:
    score: float
    flagged: bool
    rules: tuple[str, ...] = field(default_factory=tuple)


def analyze(text: str, threshold: float = DEFAULT_THRESHOLD) -> InjectionReport:
    norm = normalize(text)
    hits = [rule for rule in RULES if rule.pattern.search(norm)]
    # Noisy-OR: independent weak signals combine but never exceed 1.0.
    miss = 1.0
    for rule in hits:
        miss *= 1.0 - rule.weight
    score = round(1.0 - miss, 3)
    return InjectionReport(score=score, flagged=score >= threshold, rules=tuple(r.name for r in hits))


# ── Layer 3: spotlighting ───────────────────────────────────────────────────

_DELIMITER_SPOOF = re.compile(r"(-{3,}|={3,}|\[(?:parent post|comment) by[^\]]*\])", re.IGNORECASE)


def spotlight(author: str, content: str, kind: str = "COMMENT") -> str:
    """Render one untrusted message so it cannot impersonate our prompt structure."""
    safe_author = re.sub(r"[^\w\-]", "", author)[:32] or "unknown"
    safe = _DELIMITER_SPOOF.sub("[removed]", content.replace("\r", " ").replace("\n", " "))
    return f'[{kind} by {safe_author}]: "{safe}"'


# ── Layer 4: output guard ───────────────────────────────────────────────────

_PERSONA_BREAK = re.compile(
    r"\b(i apologi[sz]e|i'?m (so )?sorry|as an ai( language model)?|how (can|may) i (help|assist)|"
    r"customer service|persona lock|security directive|system prompt)\b",
    re.IGNORECASE,
)


def validate_reply(reply: str) -> list[str]:
    """Return the persona-break phrases found in a reply (empty list = safe)."""
    return sorted({m.group(0).lower() for m in _PERSONA_BREAK.finditer(reply)})
