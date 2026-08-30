# Posting the brief to Discord

Each morning, once the daily job has written and validated the new edition, a second
workflow posts it to a channel in the club's Discord.

**Discord is the publication.** It gets the edition *whole* — every item's background,
glossary with definitions, dek, why-it-matters, fab angle, go-deeper tier and full
source list, plus all of Foundations. Nothing is held back and nothing links out,
because there is nowhere to link to: GitHub Pages was removed deliberately in favour of
one surface, read where people already are.

That makes an edition **around 17 messages**, not two. Read the channel setup below with
that in mind — this needs a channel of its own, and ideally a forum channel.

If you never set this up nothing crashes: the workflow logs a notice and exits, and the
edition is still written and committed. It is simply never read by anyone.

## One-time setup (about five minutes, needs a Discord admin and a repo admin)

**1. Make the channel.** In the club server, create the channel you want the brief in —
`#daily-brief` is the obvious name. A channel of its own is **required in practice**, not
a nicety: a full edition is about 17 messages and would obliterate conversation anywhere
else.

**Strongly recommended: make it a forum channel.** A webhook can only open a thread by
itself in a forum or media channel, so a forum channel is the one setup where each day's
edition collapses into a single titled thread instead of 17 loose messages in a scroll.
In a normal text channel the posts still read fine — every item leads with a colored
embed naming its layer and title — but the day is not a unit you can collapse or link to.

To use it, create a **Forum** channel, put the webhook on it, and pass `--thread` (see
below). To do the same in an ordinary text channel you would need a Discord **bot token**
with `CREATE_PUBLIC_THREADS`, which this repo does not have and does not want — a webhook
URL is the only credential here.

**2. Create the webhook.** In Discord: right-click the channel → **Edit Channel** →
**Integrations** → **Webhooks** → **New Webhook**. Name it `MNF Brief`, give it an
avatar if you like, then click **Copy Webhook URL**.

You need **Manage Webhooks** permission on the channel to see this menu.

**3. Add it to the repo.** On GitHub, in this repository: **Settings** → **Secrets and
variables** → **Actions** → **New repository secret**.

- Name: `DISCORD_WEBHOOK_URL`
- Value: the URL you copied

Save it. GitHub will never show the value again, which is fine — you can always
regenerate the webhook in Discord.

**4. Test it.** Go to **Actions** → **Post to Discord** → **Run workflow**. Leave the
date blank, tick **dry run**, and run it. Read the log: it prints the exact JSON it would
send, and posts nothing. If that looks right, run it again with dry run unticked and
check the channel.

That's it. From then on it fires automatically whenever the daily brief workflow
succeeds.

## Running it by hand

From a clone of the repo:

```bash
# See what would be posted, without posting. Prints message count, the largest
# message against each cap, and the coverage check.
python3 scripts/post_discord.py --dry-run

# Post a specific edition
export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/...'
python3 scripts/post_discord.py --date 2026-08-20

# Forum channel only: open a new thread named after the edition and post into it
python3 scripts/post_discord.py --thread

# Post into a thread that already exists, in any channel type
python3 scripts/post_discord.py --thread-id 1234567890123456789

# Point it at a test server while you're fiddling with the format
python3 scripts/post_discord.py --webhook "$TEST_WEBHOOK" --brief briefs/2026-08-20.json
```

With no arguments it posts today's edition, falling back to the most recent one.

**Always `--dry-run` first.** Seventeen messages is a lot to take back by hand, and
Discord has no bulk delete for webhook posts.

To turn threading on for the nightly run, add `--thread` to the `post_discord.py` command
in `.github/workflows/discord.yml` — but only once the webhook lives on a forum channel,
or the first call fails with a 400.

## What the post looks like

1. A header message: the date, the headline, the item count and the Foundations topic.
2. Then, bottom of the stack upward — Energy, Silicon, Chips, Computing, Infrastructure,
   Models, Applications — a small colored header embed naming each layer and its scope,
   followed by one embed per item. An item carries, in the same order as the reading app:
   **Before the news** (the background), the dek, **Why it matters**, **Fab angle** where
   present, **Go deeper**, **Terms** (the glossary with definitions), and a numbered
   source list. Confidence is spelled out in the footer — `confirmed`, `reported` or
   `rumored` — rather than signalled by a marker, since Discord has no tooltip.
3. Foundations as its own colored run: an opener with the subtitle and tl;dr, one embed
   per section including its deeper tier, then the glossary, "try this", and sources.

A full edition is about **17 messages and 36 embeds**, roughly 74,000 characters. Discord
caps a message at 10 embeds and 6,000 characters across them, and a single embed
description at 4,096 — so long prose is split across embeds at paragraph, then line, then
sentence, then word boundaries, in that order, and never mid-word.

**Nothing is ever silently dropped.** Before it posts anything, the script re-derives
every field the reader is owed, flattens the finished payloads, and refuses to send if
anything is missing — naming the exact field, e.g. `pulse.layers[1].items[0].deeper_md`.
A truncated edition is treated as a bug, not as an acceptable outcome.

Mentions are suppressed two ways: `allowed_mentions` is set to parse nothing, and any
`@everyone`, `@here`, or role mention appearing anywhere in the content is defanged with
a zero-width space before sending. A brief cannot ping the server.

Mentions are suppressed two ways: `allowed_mentions` is set to parse nothing, and any
`@everyone`, `@here`, or role mention appearing in a headline or source title is defanged
with a zero-width space before sending. A brief can't ping the server.

## Changing or turning it off

- **Different channel:** make a webhook on the new channel and replace the secret. The
  old webhook keeps existing until you delete it in Discord — delete it.
- **Stop posting:** delete the `DISCORD_WEBHOOK_URL` secret, or disable the **Post to
  Discord** workflow from the Actions tab. Deleting the secret is the safer one; it
  leaves the workflow in place and it will simply skip.
- **Change the format:** everything is in `scripts/post_discord.py`. It is built in
  three separate stages — render an item's full body, split it to fit, pack messages —
  and the renderer never cuts anything. Keep that separation if you edit it; it is what
  makes the "nothing is dropped" guarantee checkable. Use `--dry-run` against a real
  edition to iterate without spamming the channel.

## Security

**A webhook URL is a credential.** Anyone who has it can post anything into that channel,
under that webhook's name, with no account and no audit trail. Treat it like a password:

- Never paste it in a message, an issue, a commit, or a screenshot.
- It lives in exactly two places — Discord's own settings, and the GitHub Actions secret.
- The script never prints it, and GitHub masks secrets in logs, but a URL pasted into a
  workflow file by hand would be public forever.

**If it leaks:** delete the webhook in Discord immediately (Edit Channel → Integrations →
Webhooks → the webhook → Delete). That instantly invalidates it. Then create a new one and
update the repo secret. There is nothing else to revoke — the URL *is* the credential.
