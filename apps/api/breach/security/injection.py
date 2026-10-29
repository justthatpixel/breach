"""Defence for untrusted player text (HANDOFF §7). Two independent layers:
input limits applied to every note before it reaches a prompt, and a
heuristic flag that backs up (never replaces) the judge's own
`injection_suspected` field — either one tripping zeroes that component's
credit (HANDOFF §7.3).
"""
import re
import unicodedata

from .. import config

_INJECTION_PATTERNS = [
    re.compile(r"ignore (all |any |previous |prior |the )*instructions", re.I),
    re.compile(r"disregard (all |any |previous |prior |the )*instructions", re.I),
    re.compile(r"\byou are now\b", re.I),
    re.compile(r"\bnew instructions\b", re.I),
    re.compile(r"\bsystem prompt\b", re.I),
    re.compile(r"\bact as (an?|the)\b", re.I),
    re.compile(r"</?(system|user|assistant)[^>]*>", re.I),
    re.compile(r"\[/?(system|user|assistant)\]", re.I),
    re.compile(r"mark (everything|this|it|all) as (secure|safe|mitigated)", re.I),
    re.compile(r"credit (all|every|each)", re.I),
    re.compile(r"\boverride\b", re.I),
    re.compile(r"\bthis is (a|the) system\b", re.I),
    # Meta-commentary aimed at whatever model reads the notes next — the
    # "instructions hidden in a plausible-looking note" case (HANDOFF
    # §8.2): a genuine security claim can still carry a trailing attempt
    # to talk directly to the judge.
    re.compile(r"\bfor the model\b", re.I),
    re.compile(r"\bparsing this note\b", re.I),
    re.compile(r"\bif you are (an? )?(ai|model|llm)\b", re.I),
    re.compile(r"\bas the (judge|model|ai|grading model)\b", re.I),
    re.compile(r"\bnote to the (grading )?model\b", re.I),
    re.compile(r"(don'?t|doesn'?t) apply to\b", re.I),
    re.compile(r"\bexempt from\b", re.I),
    re.compile(r"\bskip (your|the) (evidence|check|verification)\b", re.I),
    re.compile(r"\btreat .{0,30} as (equivalent to crediting|credited)\b", re.I),
]


def strip_control_characters(text: str) -> str:
    """Drop Unicode control characters (category C*) except newline/tab,
    which can otherwise hide instructions or break prompt formatting."""
    return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\t")


def clean_notes(text: str) -> str:
    """Input limits (HANDOFF §7.4): strip control characters, cap length."""
    return strip_control_characters(text)[: config.MAX_NOTES_LENGTH]


def heuristic_injection_suspected(text: str) -> bool:
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)
