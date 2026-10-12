# 🔥 roast-bot

A Discord bot that roasts server members, code snippets, and GitHub profiles.
Brutal but playful — it roasts the *behavior*, never the person. No profanity, no slurs, no hate.

## Commands

| Command | What it does |
|---|---|
| `/roast @user` | Roasts a member based on their recent chat activity: most-used emoji, most-active hour, message count, caps-lock crimes, `lol` inflation, and more. Scans the last 300 messages in the channel. |
| `/roastcode <code>` | Roasts a code snippet. Detects classic sins: `var` in 2026, `==` instead of `===`, leftover `console.log`s, TODO graveyards, empty catch blocks, onion-level nesting. |
| `/roastgithub <username>` | Roasts a public GitHub profile via the API: repo count, follower/following ratio, the missing bio, and decade-old accounts with 3 repos. |

## Setup (5 minutes, free)

1. Go to https://discord.com/developers/applications → **New Application** → name it (e.g. `Get Roasted`).
2. **Bot** → **Reset Token** → copy it. **Never share this token.**
3. Under **Privileged Gateway Intents**, enable **MESSAGE CONTENT INTENT** and **SERVER MEMBERS INTENT**, then save.
4. **OAuth2 → URL Generator** → check scopes `bot` and `applications.commands` → open the generated URL and invite the bot to your server.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env   # then put your token in .env
python bot.py
```

Or without a file: `DISCORD_TOKEN=your-token python bot.py`

The bot needs **Read Message History** permission in channels where you use `/roast`.

## Examples

`/roast @nightowl`
> 🔥 Roast for **nightowl** (based on 87 messages of evidence):
> 87 messages. Not the loudest here, but definitely the most *present*.
> Most active at 3:00. Nothing good happens after midnight, and neither does nightowl's sleep schedule.
> Most-used emoji: 💀 (34x). A whole personality in one glyph. A *small* one.
> Verdict: somehow both the comic relief and the reason we need it. 💀

`/roastcode` with `var x == 1; console.log(x); // TODO: fix later`
> 🔥 Code roast (1 line of evidence):
> `var` spotted 1x. It's not 2012 anymore. Let it go.
> `==` used 1x instead of `===`. Living dangerously — JavaScript *will* collect.
> 1 `console.log` left in. Debugging by archaeology: leave logs for future generations.
> 1 TODO/FIXME markers. 'Future me' has entered the chat and is already disappointed.
> Verdict: merge it before anyone reads it too closely. 💀

`/roastgithub octocat`
> 🔥 GitHub roast for **@octocat**:
> ...personalized based on their real public stats...

## How the roasts work

Template-based — **no API key needed**. `roast_engine.py` has zero Discord dependencies,
so you can test the roast logic without a bot token:

```bash
python - <<'EOF'
from roast_engine import roast_member
msgs = [{"author_id": 1, "content": "lol", "created_at": None, "attachments": 0}]
print(roast_member("test-user", {"count": 0}))
EOF
```

Want smarter roasts? Set `LLM_API_URL` / `LLM_API_KEY` (roadmap) — the template engine stays as the offline fallback.

## Roadmap

- [ ] Optional LLM upgrade for roasts (env-configured, off by default)
- [ ] `/roastbattle @a @b` — head-to-head
- [ ] Per-server opt-out / roast-free channels
- [ ] Leaderboard of most-roasted members

## License

MIT — see [LICENSE](LICENSE).
