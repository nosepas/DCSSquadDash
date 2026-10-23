# Security policy

FOX3 handles Discord logins, agent API keys and information about a squadron's servers. Please report vulnerabilities **privately**.

## Reporting

Do **not** open a public issue for a security problem. Use GitHub's *private vulnerability reporting* ("Security" tab -> "Report a
vulnerability") on this repository. Include what you found, how to reproduce it, and the impact. We aim to answer within a week.

## Scope and design assumptions

* The central server is meant to run behind a TLS-terminating proxy (Caddy) on a single host, with PostgreSQL.
* Agents only make outbound connections and authenticate with a per-agent key (stored hashed, revocable from the admin panel).
* Only the live map, the mission list and the server list are public; everything else requires a Discord login. Administrators are
  listed by Discord id.
* Secrets (Discord client secret, database URL, DCSServerBot API key) are never stored in the repository or in the web admin: they come
  from environment variables / the Windows service configuration.
* The demo login (`FOX3_DEMO_LOGIN`) is for local demos only and cannot be enabled from the production configuration file.

## Known limits

* The in-memory live-update and file-relay state requires a **single central process**.
* The project has had an automated review, not an external audit. See `docs/PLA.md` for the current status and open items.
