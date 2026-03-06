# uptime

Website uptime monitor that runs on GitHub Actions cron. Pings a list of URLs every 5 minutes and sends email + SMS alerts when a site goes down or comes back up. Zero cost to run.

## How it works

1. GitHub Actions triggers `monitor.py` on a cron schedule (every 5 minutes)
2. The script reads URLs and config from `sites.json`
3. For each site, it sends an HTTP GET and checks for a 200 response
4. Sites with `check_body` set must also have that string in the response body
5. On status change (up → down or down → up), one alert is sent
6. `state.json` tracks last known status per URL and is committed back to the repo

## Setup

### 1. Fork or clone this repo to your GitHub account

### 2. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `GMAIL_ADDRESS` | Gmail address used to send alerts |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not your account password) |
| `ALERT_EMAIL` | Email address to receive alerts |
| `ALERT_SMS` | Carrier SMS gateway address (e.g. `5551234567@mymetropcs.com`) |

### 3. Edit sites.json

Replace the example entries with your actual URLs and tuning values:

```json
[
  {
    "url": "https://your-site.com",
    "timeout": 10,
    "retries": 1
  }
]
```

Per-site options:

| Field | Default | Description |
|---|---|---|
| `url` | required | URL to ping |
| `timeout` | `10` | Request timeout in seconds |
| `retries` | `1` | Attempts before declaring down (5s delay between) |
| `check_body` | — | String that must appear in response body to count as up |

### Platform guidance

| Platform | Timeout | Retries | Notes |
|---|---|---|---|
| GitHub Pages | 10 | 1 | Static, always on |
| AWS | 10 | 1 | Reliable, no special handling |
| Azure Container Apps (free) | 60 | 2 | Cold starts; needs retry |
| Hugging Face Spaces (free) | 60 | 2 | Use `check_body` — returns 200 while waking up |

## Gmail setup

The sender Gmail account must have:
- **2-Step Verification** enabled
- An **App Password** generated: Google Account → Security → App Passwords

Use the App Password as `GMAIL_APP_PASSWORD`, not your regular Gmail password.

## Common SMS gateways

| Carrier | Gateway |
|---|---|
| Metro PCS | `number@mymetropcs.com` |
| AT&T | `number@txt.att.net` |
| T-Mobile | `number@tmomail.net` |
| Verizon | `number@vtext.com` |
| Sprint | `number@messaging.sprintpcs.com` |
