# Posting the brief to Discord

Each morning, once the daily job has written and validated the new edition, a second
workflow posts it to a channel in the club's Discord. Discord gets the **member tier**
only — the headline, each item's title and one-sentence dek, and the Foundations topic —
with links back to the site for the technical tier and the sources. That keeps the
channel readable on a phone and keeps the site the place you actually go to learn.

If you never set this up, nothing breaks. The workflow logs a notice and exits.

## One-time setup (about five minutes, needs a Discord admin and a repo admin)

**1. Make the channel.** In the club server, create the channel you want the brief in —
`#daily-brief` is the obvious name. A channel of its own is better than posting into
`#general`; the brief is 2–3 messages and will bury conversation otherwise.

**2. Create the webhook.** In Discord: right-click the channel → **Edit Channel** →
**Integrations** → **Webhooks** → **New Webhook**. Name it `GopherFab Brief`, give it an
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
# See what would be posted, without posting
python3 scripts/post_discord.py --dry-run

# Post a specific edition
export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/...'
python3 scripts/post_discord.py --date 2026-08-20

# Point it at a test server while you're fiddling with the format
python3 scripts/post_discord.py --webhook "$TEST_WEBHOOK" --brief briefs/2026-08-20.json
```

With no arguments it posts today's edition, falling back to the most recent one.

## What the post looks like

1. A header message: the date, the headline, the item count, the Foundations topic, and
   a link to the day's page.
2. One embed per layer, colored to match the site's layer accents, bottom of the cake
   upward — Energy, Chips, Infrastructure, Models, Applications. Each item is a field:
   title, dek, the primary source link, and a "go deeper" link that jumps straight to
   that item on the site. Items that aren't `confirmed` are marked `· reported` or
   `· rumored` in the title.
3. A Foundations embed: topic, subtitle, the tl;dr, and the "try this".

A normal edition is two messages. A very heavy one splits into more, because Discord caps
a single message at 10 embeds and 6,000 characters across them.

Mentions are suppressed two ways: `allowed_mentions` is set to parse nothing, and any
`@everyone`, `@here`, or role mention appearing in a headline or source title is defanged
with a zero-width space before sending. A brief can't ping the server.

## Changing or turning it off

- **Different channel:** make a webhook on the new channel and replace the secret. The
  old webhook keeps existing until you delete it in Discord — delete it.
- **Stop posting:** delete the `DISCORD_WEBHOOK_URL` secret, or disable the **Post to
  Discord** workflow from the Actions tab. Deleting the secret is the safer one; it
  leaves the workflow in place and it will simply skip.
- **Change the format:** everything is in `scripts/post_discord.py`. Use `--dry-run`
  against a real edition to iterate without spamming the channel.

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
