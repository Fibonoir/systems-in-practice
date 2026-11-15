# Workshop Shelf runtime observations

Date: 15 November 2026. Core fixture: version 1, followed by version 2 migration.
Environment: isolated Ubuntu 24.04 amd64 virtual machine, native ext4 filesystem,
Linux 6.8.0-147, Docker Engine 29.1.3, Compose 2.40.3, Python 3.12.3 for helpers.
The guest used CPU emulation. Container image selections are pinned in images.env.

Observed checks passed:

- First service accessible through guest loopback.
- Secret parent directory 0700, secret file 0644; unrelated host identity denied.
- App running as UID 10001 could read its mounted secret; proxy had no secret grant.
- Valid insert accepted; negative input and duplicate records rejected.
- Exact records survived container recreation.
- Database outage returned readiness 503 while liveness remained 200; restart recovered readiness.
- Stopped-writer backup copied outside the guest, retrieved under a new filename,
  and verified byte-for-byte. The source containers remained stopped.
- Retrieved backup restored exact rows into a distinct fresh Compose project.
- Restore refused a database containing existing public tables.
- Version 2 migration preserved records and added an empty note field.
- Version 1 returned readiness 503 against schema 2.
- All test containers stopped after acceptance.

The original five-second app healthcheck process timeout was too short under
emulation. The distributed Compose file now uses a twenty-second timeout and
startup grace period; the HTTP probe still uses a four-second timeout. An early
HTTP check and a three-second post-recreation check also raced startup. Those
test harness checks were repeated after bounded waits for the service to listen;
the expected status codes and data assertions were unchanged.

This is an off-guest backup transfer and fresh-project recovery test, not loss
of the physical host, whole-machine recovery, a load benchmark, or a public
deployment. No external TLS, arm64, or disk-exhaustion result is claimed.
The 3 November baseline separately checked FreshRSS CLI installation, HTTP
access, a stopped-writer archive, and restored user/SQLite/witness state.
FreshRSS browser login and external feed refresh were not evaluated.

Use fictional data and an isolated local environment. The application has no
authentication. Review the book's scope before adapting it to valuable data.
