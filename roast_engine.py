"""roast-bot engine: pure functions, no discord import.

Everything here is testable without a bot token. Templates are brutal-but-playful:
roast the behavior/code, never the person. No profanity, no slurs, no hate.
"""
from __future__ import annotations

import random
import re
from collections import Counter
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# /roast : member-activity stats
# ---------------------------------------------------------------------------

_CUSTOM_EMOJI_RE = re.compile(r"<a?:\w+:(\d+)>")
# rough unicode-emoji matcher (covers the common blocks)
_UNICODE_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symbols & pictographs, emoticons, transport
    "\U00002600-\U000027BF"  # misc symbols, dingbats
    "\U00002B00-\U00002BFF"  # arrows etc
    "\U0001F000-\U0001F2FF"
    "]",
)

_LOL_WORDS = ("lol", "lmao", "rofl", "haha", "hehe", "xd")


def analyze_member(messages: list[dict], user_id: int) -> dict:
    """Compute fun stats for one user from a list of message dicts.

    Each dict: {"author_id": int, "content": str, "created_at": datetime,
                "attachments": int}
    """
    mine = [m for m in messages if m.get("author_id") == user_id]
    total = len(messages)
    n = len(mine)
    if n == 0:
        return {"count": 0}

    contents = [m.get("content", "") or "" for m in mine]
    joined = "\n".join(contents)

    custom = _CUSTOM_EMOJI_RE.findall(joined)
    uni = _UNICODE_EMOJI_RE.findall(joined)
    emoji_counter = Counter(uni)
    for e in custom:
        emoji_counter[f"<custom:{e}>"] += 1
    top_emoji, top_emoji_n = (emoji_counter.most_common(1)[0] if emoji_counter else (None, 0))

    hours = Counter()
    for m in mine:
        ts = m.get("created_at")
        if isinstance(ts, datetime):
            hours[ts.hour] += 1
    top_hour, top_hour_n = (hours.most_common(1)[0] if hours else (None, 0))

    words = re.findall(r"\w+", joined.lower())
    lol_n = sum(1 for w in words if w in _LOL_WORDS)
    q_n = joined.count("?")
    caps_chars = sum(1 for c in joined if c.isupper())
    alpha_chars = sum(1 for c in joined if c.isalpha())
    caps_ratio = (caps_chars / alpha_chars) if alpha_chars else 0.0
    avg_len = sum(len(c) for c in contents) / n
    longest = max(contents, key=len) if contents else ""
    attach_n = sum(int(m.get("attachments", 0) or 0) for m in mine)

    return {
        "count": n,
        "server_total": total,
        "share": (n / total) if total else 0.0,
        "top_emoji": top_emoji,
        "top_emoji_n": top_emoji_n,
        "top_hour": top_hour,
        "top_hour_n": top_hour_n,
        "lol_n": lol_n,
        "question_n": q_n,
        "caps_ratio": caps_ratio,
        "avg_len": avg_len,
        "longest_len": len(longest),
        "attach_n": attach_n,
    }


def _pick(rng: random.Random, templates: list[str], **kw) -> str:
    return rng.choice(templates).format(**kw)


def roast_member(name: str, stats: dict, seed: int | None = None) -> str:
    """Build a personalized roast from activity stats."""
    rng = random.Random(seed)
    n = stats.get("count", 0)
    if n == 0:
        return (
            f"🔥 Roast for **{name}**:\n"
            f"I scanned the chat history and found... absolutely nothing. "
            f"{name} is either a ghost, a lurker, or just here for the emojis they never send."
        )

    lines = [f"🔥 Roast for **{name}** (based on {n} messages of evidence):"]
    share_pct = stats.get("share", 0) * 100

    if n >= 50:
        lines.append(_pick(rng, [
            "{n} messages. {share:.0f}% of this entire channel. Somewhere a library is missing its quiet section.",
            "{n} messages and {share:.0f}% of all chat traffic. {name} doesn't type, {name} *occupies*.",
        ], n=n, share=share_pct, name=name))
    elif n >= 15:
        lines.append(_pick(rng, [
            "{n} messages. Not the loudest here, but definitely the most *present*.",
            "{n} messages — {name} treats this server like a group chat that never asked.",
        ], n=n, name=name))
    else:
        lines.append(_pick(rng, [
            "Only {n} messages. {name} speaks rarely... and somehow it's still too often.",
            "{n} messages total. Quality over quantity? We checked. It's neither.",
        ], n=n, name=name))

    hour = stats.get("top_hour")
    if hour is not None:
        if 0 <= hour <= 5:
            lines.append(_pick(rng, [
                "Most active at {h}:00. Nothing good happens after midnight, and neither does {name}'s sleep schedule.",
                "Peak hours: {h} AM. {name}'s keyboard has seen things. Mostly typos.",
            ], h=hour, name=name))
        elif hour >= 22:
            lines.append(f"Most active at {hour}:00 — a certified night owl. The messages get worse, the confidence doesn't.")
        else:
            lines.append(f"Most active at {hour}:00 — even {name}'s prime time is mid.")

    emoji = stats.get("top_emoji")
    if emoji:
        if str(emoji).startswith("<custom:"):
            lines.append("Top emoji is a custom server emoji, used "
                         f"{stats['top_emoji_n']} times. Nothing says 'I peaked in this Discord' like it.")
        else:
            lines.append(_pick(rng, [
                'Most-used emoji: {e} ({c}x). A whole personality in one glyph. A *small* one.',
                'Says {e} {c} times. We get it. You have *one* emotion.',
            ], e=emoji, c=stats["top_emoji_n"]))

    if stats.get("lol_n", 0) >= 5:
        lines.append(f"Said some variant of 'lol' {stats['lol_n']} times. The laughter is typed. The joy is not.")
    if stats.get("question_n", 0) >= 8:
        lines.append(f"Asked {stats['question_n']} questions and answered approximately none of them.")
    if stats.get("caps_ratio", 0) > 0.35 and stats.get("avg_len", 0) > 20:
        lines.append("TYPES IN CAPS LIKE THE SHIFT KEY OWES THEM MONEY.")
    if stats.get("avg_len", 0) < 12:
        lines.append(f"Average message length: {stats['avg_len']:.0f} characters. Brevity is wit, {name}. This is just brevity.")
    elif stats.get("avg_len", 0) > 200:
        lines.append(f"Average message: {stats['avg_len']:.0f} characters. {name} doesn't send messages, {name} publishes essays nobody assigned.")
    if stats.get("longest_len", 0) > 600:
        lines.append(f"Longest single message: {stats['longest_len']} characters. Somewhere in there is a point. Archaeologists are still digging.")
    if stats.get("attach_n", 0) >= 5:
        lines.append(f"Sent {stats['attach_n']} attachments. The memes are load-bearing at this point.")

    lines.append(rng.choice([
        "Verdict: 10/10 server citizen. 2/10 typist. We keep them anyway. 💀",
        "Verdict: the server's background music — always on, rarely noticed, impossible to mute. 💀",
        "Verdict: somehow both the comic relief and the reason we need it. 💀",
    ]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# /roastcode : static-analysis sins
# ---------------------------------------------------------------------------

def analyze_code(code: str) -> dict:
    lines = code.splitlines()
    n = len(lines)
    stripped = [l.strip() for l in lines]
    joined = "\n".join(lines)
    lower = joined.lower()

    return {
        "lines": n,
        "todo": len(re.findall(r"\bTODO\b", joined)) + len(re.findall(r"\bFIXME\b", joined)),
        "console_log": len(re.findall(r"console\.log", joined)),
        "print_dbg": len(re.findall(r"(?<!\w)print\s*\(", joined)),
        "var_kw": len(re.findall(r"(?<![\w$])var\s+\w", joined)),
        "loose_eq": len(re.findall(r"(?<![=!<>])==(?!=)", joined)),
        "semicolons": joined.count(";"),
        "comments": sum(1 for l in stripped if l.startswith(("//", "#", "/*", "*", "--"))),
        "nesting": max(((len(l) - len(l.lstrip())) // 4 for l in lines if l.strip()), default=0),
        "longest_line": max((len(l) for l in lines), default=0),
        "has_function": bool(re.search(r"\b(function|def|fn|func|=>)\b", joined)),
        "empty_catch": len(re.findall(r"catch\s*\([^)]*\)\s*\{\s*\}", joined)),
        "magic_numbers": len(re.findall(r"(?<![\w.])\d{2,}(?![\w.])", joined)),
        "is_python": "def " in joined or "import " in lower,
        "is_js": ("function" in joined or "=>" in joined or "console." in joined or "const " in joined),
    }


def roast_code(code: str, seed: int | None = None) -> str:
    rng = random.Random(seed)
    s = analyze_code(code)
    n = s["lines"]
    lines = [f"🔥 Code roast ({n} line{'s' if n != 1 else ''} of evidence):"]

    if n == 0 or not code.strip():
        return "🔥 Code roast:\nYou submitted an empty snippet. Bold strategy — zero lines, zero bugs, zero functionality. 10/10, would not ship."

    if n > 150:
        lines.append(f"{n} lines in one snippet. This isn't a function, it's a *novel*. With no chapters. And no ending.")
    elif n < 5:
        lines.append(f"{n} lines. Either beautifully minimal or you gave up."
                     + ("" if s["comments"] else " The lack of comments suggests the latter."))

    sins = []
    if s["var_kw"]:
        sins.append(f"`var` spotted {s['var_kw']}x. It's not 2012 anymore. Let it go.")
    if s["loose_eq"]:
        sins.append(f"`==` used {s['loose_eq']}x instead of `===`. Living dangerously — JavaScript *will* collect.")
    if s["console_log"]:
        n = s["console_log"]
        sins.append(f"{n} `console.log`{'s' if n != 1 else ''} left in. Debugging by archaeology: leave logs for future generations.")
    if s["print_dbg"]:
        n = s["print_dbg"]
        sins.append(f"{n} stray `print()`{'s' if n != 1 else ''}. The terminal is not your diary.")
    if s["todo"]:
        n = s["todo"]
        sins.append(f"{n} TODO/FIXME marker{'s' if n != 1 else ''}. 'Future me' has entered the chat and is already disappointed.")
    if s["empty_catch"]:
        sins.append("Empty catch block found. Errors go in, nothing comes out. The void has a door now.")
    if s["nesting"] >= 4:
        sins.append(f"Nesting depth {s['nesting']}. This code has more layers than an onion and makes people cry the same way.")
    if s["comments"] == 0 and n > 20:
        lines.append("Zero comments in 20+ lines. Future-you is going to read this like ancient hieroglyphs.")
    if s["longest_line"] > 120:
        lines.append(f"Longest line: {s['longest_line']} chars. Horizontal scrolling: the final boss of code review.")

    lines.extend(sins[:4])  # keep it punchy: max 4 sin roasts
    if not sins and s["comments"] > 0:
        lines.append("Honestly? Clean-ish. Comments exist, no obvious sins. Suspicious. We're watching you. 👀")

    lines.append(rng.choice([
        "Verdict: it runs. Probably. Don't touch it. 💀",
        "Verdict: 6/10 — compiles, confuses, conquers nothing. 💀",
        "Verdict: merge it before anyone reads it too closely. 💀",
    ]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# /roastgithub : public profile stats
# ---------------------------------------------------------------------------

def roast_github(profile: dict, seed: int | None = None) -> str:
    """Roast from a GitHub /users API response dict. All fields optional."""
    rng = random.Random(seed)
    login = profile.get("login") or "mystery-dev"
    lines = [f"🔥 GitHub roast for **@{login}**:"]

    repos = profile.get("public_repos") or 0
    followers = profile.get("followers") or 0
    following = profile.get("following") or 0
    bio = (profile.get("bio") or "").strip()
    created = profile.get("created_at") or ""
    years = 0
    if created:
        try:
            years = max(0, datetime.now(timezone.utc).year - datetime.fromisoformat(
                created.replace("Z", "+00:00")).year)
        except ValueError:
            years = 0

    if repos == 0:
        lines.append("Zero public repos. A GitHub account with no code — it's just a very expensive username reservation.")
    elif repos == 1:
        lines.append("One public repo. One. It's probably a fork. Of a tutorial.")
    elif repos > 100:
        lines.append(f"{repos} public repos. Somewhere in there is actual code. Statistically, most of it is forks and 'test'.")
    elif repos > 30:
        lines.append(f"{repos} repos. Quantity has a quality all its own — unfortunately not this one.")

    if followers == 0 and following > 0:
        lines.append(f"Following {following} people, followed by nobody. The GitHub equivalent of waving at strangers.")
    elif following > 0 and followers / following < 0.2:
        lines.append(f"{followers} followers, {following} following. That ratio is doing a LOT of heavy lifting.")
    elif followers >= 1000:
        lines.append(f"{followers} followers. Okay, famous. The roast writes itself but the fans won't like it.")

    if not bio:
        lines.append("No bio. Mysterious. Or just couldn't think of anything — we've all been there, most of us recovered.")
    elif len(bio) < 20:
        lines.append(f'Bio: "{bio}". Short. Like the commit messages, probably.')

    if years >= 8 and repos < 10:
        lines.append(f"Account is {years} years old with {repos} repos. A decade of lurking. Respect the commitment to *not* committing.")
    elif years <= 1 and repos > 20:
        lines.append(f"Account is {years or '<1'} year old with {repos} repos already. Either a prodigy or someone who discovered 'commit early, commit often' yesterday.")

    company = (profile.get("company") or "").strip()
    if company:
        lines.append(f"Works at {company} — we're sure they're thrilled about this roast.")
    location = (profile.get("location") or "").strip()
    if location:
        lines.append(f"Based in {location}. The code reviews there must be *spicy*.")

    if len(lines) == 1:
        lines.append("A perfectly normal profile. No red flags found. Which is, frankly, the biggest red flag.")

    lines.append(rng.choice([
        "Verdict: ships code. Sometimes. Stars are just likes with extra steps. 💀",
        "Verdict: the README is longer than the codebase. We checked. We always check. 💀",
        "Verdict: 10/10 profile picture, 4/10 commit hygiene. 💀",
    ]))
    return "\n".join(lines)
