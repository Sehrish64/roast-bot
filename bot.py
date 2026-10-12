"""roast-bot: a Discord bot that roasts members, code, and GitHub profiles.

Setup:
    1. https://discord.com/developers/applications -> New Application -> Bot -> copy token
    2. Enable "MESSAGE CONTENT INTENT" and "SERVER MEMBERS INTENT" under Privileged Intents
    3. OAuth2 -> URL Generator -> scopes: bot + applications.commands -> open the URL to invite
    4. DISCORD_TOKEN=your-token python bot.py
"""
from __future__ import annotations

import json
import os
import urllib.request

import discord
from discord import app_commands
from discord.ext import commands

from roast_engine import analyze_member, roast_code, roast_github, roast_member

HISTORY_LIMIT = 300  # messages scanned per /roast (current channel)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class RoastBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")


bot = RoastBot()


@bot.tree.command(name="roast", description="Roast a server member based on their chat activity")
@app_commands.describe(member="Who deserves it?")
async def roast(interaction: discord.Interaction, member: discord.Member) -> None:
    await interaction.response.defer()
    try:
        raw = []
        async for msg in interaction.channel.history(limit=HISTORY_LIMIT):
            raw.append({
                "author_id": msg.author.id,
                "content": msg.content,
                "created_at": msg.created_at,
                "attachments": len(msg.attachments),
            })
    except discord.Forbidden:
        await interaction.followup.send(
            "I can't read message history in this channel. Give me 'Read Message History' permission and try again. 💀"
        )
        return
    stats = analyze_member(raw, member.id)
    await interaction.followup.send(roast_member(member.display_name, stats))


@bot.tree.command(name="roastcode", description="Roast a code snippet")
@app_commands.describe(code="Paste the code (up to ~1500 chars)")
async def roastcode(interaction: discord.Interaction, code: str) -> None:
    await interaction.response.send_message(roast_code(code[:1500]))


@bot.tree.command(name="roastgithub", description="Roast a GitHub profile")
@app_commands.describe(username="GitHub username")
async def roastgithub(interaction: discord.Interaction, username: str) -> None:
    await interaction.response.defer()
    clean = "".join(c for c in username.strip().lstrip("@") if c.isalnum() or c in "-_")
    if not clean:
        await interaction.followup.send("That's not a username, that's a cry for help. 💀")
        return
    req = urllib.request.Request(
        f"https://api.github.com/users/{clean}",
        headers={"User-Agent": "roast-bot", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            profile = json.loads(resp.read().decode())
    except Exception:
        await interaction.followup.send(
            f"Couldn't find `@{clean}` on GitHub. Either it doesn't exist or it's hiding from this roast. Both are valid strategies. 💀"
        )
        return
    await interaction.followup.send(roast_github(profile))


@bot.event
async def on_ready() -> None:
    print(f"🔥 {bot.user} is online and judging.")


if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Set DISCORD_TOKEN first. See .env.example and README.md.")
    bot.run(token)
