# SOP — Google Workspace CLI (`gwcli`)

Owner: OpenScience (for Xu Lab)

Scope: quick reference + repeatable workflows for using `gwcli` to manage **Gmail**, **Google Calendar**, and **Drive (read-only)** — especially for **group meeting emails** and **calendar events**.

This SOP is based on:
- Local `gwcli --help` output (commands + flags)
- Upstream docs (untrusted web reference): https://github.com/ianpatrickhines/google-workspace-cli

---

## 0) Quick mental model

- `gwcli` is a multi-profile CLI (similar to AWS CLI).
- Subcommands:
  - `gwcli profiles …`
  - `gwcli gmail …`
  - `gwcli calendar …`
  - `gwcli drive …` (read-only)
- Output formats:
  - `--format table` (default; human)
  - `--format json` (best for scripting/agents)
  - `--format text`

---

## 1) Profiles (authentication + account switching)

### List profiles
```bash
gwcli profiles list
# or (machine-readable)
gwcli --format json profiles list
```

### Add a profile (OAuth flow)
```bash
gwcli profiles add <name>
# (some builds also support: gwcli profiles add <name> --client <path-to-oauth-json>)
```
This will open a browser for Google OAuth and store credentials locally.

### Set default profile
```bash
gwcli profiles set-default <name>
```

### Remove a profile
```bash
gwcli profiles remove <name>
```

### Use a specific profile for a single command
```bash
gwcli --profile <name> gmail list
```

---

## 2) Gmail (read/search/reply/send)

### List recent emails
```bash
gwcli gmail list

gwcli gmail list --unread --limit 20
```

### Search (Gmail query syntax)
```bash
gwcli gmail search "from:someone@domain.com"
gwcli gmail search "subject:(group meeting) newer_than:7d"
gwcli gmail search "is:unread label:inbox"
```

### Read an email
```bash
gwcli gmail read <message-id>
```

### View an entire thread
```bash
gwcli gmail thread <thread-id>
```

### Archive / trash
```bash
gwcli gmail archive <message-id>
gwcli gmail trash <message-id>
```

### Compose + send (one-step)
```bash
gwcli gmail send --to "a@b.com" --subject "Subject" --body "Body text"
```

### Draft then send
```bash
gwcli gmail draft --to "a@b.com" --subject "Subject" --body "Body text"

gwcli gmail send <draft-id>
```

### Reply
```bash
gwcli gmail reply <message-id> --body "Thanks — …"
```

---

## 3) Calendar (events)

### List calendars
```bash
gwcli calendar list
```

### List upcoming events
```bash
gwcli calendar events

gwcli calendar events --days 14 --limit 50

gwcli calendar events --calendar primary --days 7
```

### Search events
```bash
gwcli calendar search "group meeting"
```

### Create event
```bash
gwcli calendar create "Xu Lab Group Meeting" \
  --start "2026-03-10 10:00" \
  --end   "2026-03-10 11:00" \
  --location "Ramakrishnan 101" \
  --description "Weekly group meeting" \
  --attendees "person1@domain.com,person2@domain.com"

# If --end omitted, defaults to start + 1 hour
```

### Update event
```bash
gwcli calendar update <event-id> --title "New title"
gwcli calendar update <event-id> --start "2026-03-10 10:30" --end "2026-03-10 11:30"
```

### Delete event
```bash
gwcli calendar delete <event-id>
```

---

## 4) Drive (read-only)

### List files
```bash
gwcli drive list --limit 50

gwcli drive list --folder <folder-id> --limit 100
```

### Search files (Drive query syntax)
```bash
gwcli drive search "name contains 'group meeting'" --limit 50

gwcli drive search "mimeType='application/pdf' and name contains 'agenda'" --limit 50
```

### Download a file
```bash
gwcli drive download <file-id>

gwcli drive download <file-id> --output ./downloaded_file
```

### Export Google Docs/Sheets/Slides
```bash
gwcli drive export <file-id> --format pdf

gwcli drive export <file-id> --format xlsx

gwcli drive export <file-id> --format pptx
```

---

## 5) “Group meeting” workflows (templates)

### A) Send a group meeting email (simple)
```bash
gwcli gmail send \
  --to "lab-list@domain.com" \
  --subject "Xu Lab group meeting — Tue 10:00" \
  --body $'Hi all,\n\nReminder: group meeting Tue 10:00 in Room X.\n\nAgenda:\n1) …\n2) …\n\n–OpenScience'
```

### B) Create a calendar event + email attendees
1) Create the calendar event:
```bash
gwcli calendar create "Xu Lab Group Meeting" --start "Tue 10:00" --location "Room X" --attendees "a@b.com,b@c.com"
```
2) Send the email:
```bash
gwcli gmail send --to "a@b.com,b@c.com" --subject "Invite: Xu Lab Group Meeting" --body "Calendar invite created — see details." 
```

---

## 6) Operational tips / best practices

- Prefer `--format json` whenever you plan to post-process output.
- Use `--profile <name>` explicitly when you are unsure which Google account is active.
- Avoid destructive actions (trash/delete) unless you have verified the IDs.
- For automation, keep message bodies in files and use shell substitution:
  - `--body "$(cat body.txt)"` (works if the CLI accepts multiline; if not, use `$'…'` bash quoting).

---

## 7) Known limitations (from current local help)

- Drive is **read-only** via this CLI build.
- Gmail/calendar commands are present; no Sheets/Docs/Chat/Admin in this `gwcli` build.

---

## 8) Local help reference (source of truth)

```bash
gwcli --help

gwcli profiles --help

gwcli gmail --help
# and per-command:
gwcli gmail list --help

gwcli calendar --help

gwcli drive --help
```
