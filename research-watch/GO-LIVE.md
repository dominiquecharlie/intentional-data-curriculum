# Research Watch: go live

Seven steps. Steps 1 and 2 involve credentials, so they are yours alone. Budget about
45 minutes, most of it waiting for things to install.

---

## Step 1. Get an Anthropic API key

1. Go to <https://console.anthropic.com> and sign in.
2. Open **API keys** in the left sidebar, then **Create key**. Name it `research-watch`.
3. Copy the key. It is shown once. Paste it somewhere safe like your password manager.
4. Add a small amount of credit under **Billing**. Scoring roughly 50 items a week on
   Haiku costs cents per month, so $5 will last a long time.

Keep this key out of any file in the repo. It goes in GitHub secrets in step 5.

---

## Step 2. Get an email app password

Your address is on a custom domain, so this is most likely Google Workspace.

1. Go to <https://myaccount.google.com/apppasswords>. This page only exists once
   two-step verification is switched on, so turn that on first if prompted.
2. Create an app password named `research-watch` and copy the 16 characters.
3. Note your settings: host `smtp.gmail.com`, port `465`, user
   `dominique.charlie@intentionaldata.org`, password the app password from above.

If your mail is not Google, ask your provider for SMTP host, port, and whether they
require an app password. Everything else stays the same.

---

## Step 3. Test it locally before anything goes to GitHub

Open Terminal.

```bash
cd ~/Desktop/"Curriculum Push"/research-watch
python3 --version                      # needs 3.11 or newer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Now a real fetch. This is the one thing I could not test, because it only proves itself
against live API responses.

```bash
python -m src.fetch
```

Expect a few minutes and a line per source. Some Tier A sources will report nothing on
the first run, which is correct: it records a baseline hash and only reports on the
second run when something has changed.

Then score and read the digest:

```bash
export ANTHROPIC_API_KEY="paste-your-key-here"
python -m src.score
python -m src.digest
```

Read `output/digest.md`. If the scores look wrong, edit `config/rubric.md` and run
`python -m src.score` again. This is the part worth tuning before automating.

Send yourself one test email:

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="465"
export SMTP_USER="dominique.charlie@intentionaldata.org"
export SMTP_PASSWORD="your-app-password"
python -m src.digest --send
```

---

## Step 4. Push the code to GitHub

If you already have the repo cloned, copy this folder into it. If not:

```bash
cd ~/Desktop
git clone https://github.com/dominiquecharlie/intentional-data-curriculum.git
cp -R ~/Desktop/"Curriculum Push"/research-watch ~/Desktop/intentional-data-curriculum/
cd ~/Desktop/intentional-data-curriculum
git add research-watch
git commit -m "Add Research Watch"
git push
```

The `.gitignore` keeps `.venv` and `__pycache__` out.

---

## Step 5. Add the secrets in GitHub

1. Open <https://github.com/dominiquecharlie/intentional-data-curriculum/settings/secrets/actions>
2. Click **New repository secret** once for each of these five:

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | the key from step 1 |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | `dominique.charlie@intentionaldata.org` |
| `SMTP_PASSWORD` | the app password from step 2 |

Secrets are write-only. GitHub will never show them back to you, and they do not appear
in logs.

---

## Step 6. Run it once by hand

1. Open the **Actions** tab in the repo.
2. Select **Research Watch** in the left sidebar.
3. Click **Run workflow**, then the green **Run workflow** button.
4. Watch it run. Each step expands to show its log.

A green tick means the schedule will work. Check that the digest email arrived.

If a step fails, the log names the reason. The usual causes are a missing secret or a
typo in the SMTP host.

---

## Step 7. Wire the citation reference page

Once you have approved your first batch:

```bash
python -m src.approve
python -m src.render --inject ../intentional-data-citation-reference.html
```

The first injection adds two HTML comment markers around the foundations block. Every
run after that replaces only what sits between them, so the interactive segment map
above is never touched. Commit and push the updated page and GitHub Pages picks it up.

---

## After that

It runs Mondays at 08:00 Central and emails you. Nothing reaches the evidence base
until you run `python -m src.approve`, so a quiet week costs you nothing.

Two things worth knowing:

**The repo is public.** `data/registry.json` and `output/digest.md` get committed on
every run, so your research pipeline is visible to anyone. That suits a curriculum
whose citations are already published. Make the repo private if you would rather it
were not.

**The first two weeks will be noisy.** Tier A records baselines on run one, and the
Tier B queries are untuned. Reject freely. Every rejection is remembered in
`seen.json`, so the same item never comes back.
