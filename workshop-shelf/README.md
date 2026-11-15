# Workshop Shelf companion

Local teaching fixture for *Self-Hosting with Docker Compose*, Martin J. Ellis.
Use fictional data only. The app has no authentication and is unsuitable for public exposure.

## Files and prerequisites

Keep this directory together. Use a Linux shell in this directory, a local working Docker Engine with Compose, curl, and Python3.11+ for the helpers. Downloads need network access. This is not an offline image bundle. `images.env` records the tested upstream digests; `app/requirements.txt` records psycopg3.2.13. Authoring baseline: Engine29.9.2, Compose5.6.1, PostgreSQL17.11, Caddy2.11.7, Python3.13.18, amd64 Linux containers through Docker Desktop4.96.3. A second core run on 15 November 2026 used native ext4 storage in an isolated Ubuntu24.04 guest with Engine29.1.3 and Compose2.40.3. The nonroot app read its mounted secret; an unrelated host identity could not traverse the0700 parent directory; the proxy had no secret grant. See RUNTIME-RESULTS.md for scope and observations.

Read Chapters1–8 for mechanism and setup. First run `docker version`, `docker compose version`, `docker context show`, and inspect existing containers. Do not stop unrelated work. Copy `images.env` to `.env` only for a new local copy. Select unused loopback ports if the defaults are occupied. Never remove a volume just to repeat a setup command.

## Core sequence

1. Use `compose.first.yaml` with `-p shelf-first` to serve `hello/index.html` on loopback8087. Bring that exact project down after inspection.
2. Create `secrets/db_password.txt` once with a random value using Chapter7's exclusive-create command. On native Linux, the documented directory/file modes are700/644 so the nonroot service can read the mounted file while ordinary host users cannot traverse the secret directory. Test actual readability on your platform.
3. Validate, build `app`, and start only `db` with `-p shelf-lab up -d --wait db`.
4. Run `docker compose -p shelf-lab run --rm --no-deps app python app.py init` once against the fresh database.
5. Start the full project with `up -d --wait`. Read `/ready` and `/api/items` on loopback8088. Add a distinctive record through the API.
6. Recreate containers retaining the volume and compare rows. Stop only the project's database, observe503 readiness with continuing liveness, restart the database, and compare again.
7. Stop app/proxy writes, run `python3 ops.py backup --project shelf-lab --file backups/unique-name.dump`, then restart the source.
8. Start a distinct target database using `APP_VERSION=1 SHELF_PORT=8089 docker compose -p shelf-restore up -d --wait db`. Do not initialize it. Run `python3 ops.py restore --project shelf-restore --file backups/unique-name.dump`.
9. Start the target using the same version/port assignments and compare records through its API and `ops.py rows`. Inspect separate volume identities.
10. Rehearse Chapter11's version2 build, stopped-writer migration, and acceptance on the restored target. The old version deliberately rejects schema2. Recover version1 into another fresh project from the pre-update dump.

The commands in the chapters are the detailed procedure, including expected failures. `ops.py` performs no scheduling, deletion, retention, remote transfer, or automatic restart. Failed exclusive backup creation can leave a partial file; preserve the last good copy and choose another name after resolving the error. Restore refuses a checksum mismatch or an existing public table. That guard is specific to this fixture.

## FreshRSS transfer

Use `compose.transfer.yaml` and `-p shelf-reader`, loopback8091. Follow Chapter14's CLI install and user creation. The printed password is fictional and local-only. The data volume holds SQLite/user/configuration state; extensions are empty in the baseline.

For a durable witness before backup, enter this from a Linux shell:

```sh
docker compose -p shelf-reader -f compose.transfer.yaml \
  exec -T --user www-data reader sh -c \
  'printf "transfer witness 23\n" > data/restore-witness.txt'
```

Run `python3 transfer.py backup --project shelf-reader --file backups/reader-data.tar`. It stops the writer and leaves it stopped. Run `python3 transfer.py restore --project shelf-reader-copy --file backups/reader-data.tar --port 8092`. It refuses existing target resources. It archives data only; installed extensions would require additional coverage. After restoration, inspect the witness, `php cli/list-users.php` as www-data, and the HTTP page. Update the saved base URL through FreshRSS's supported settings before actual browser use. Browser login/external feeds were not verified in the authoring check.

Both helpers accept only explicit shelf-prefixed projects; that prefix is a targeting aid, not permission to delete arbitrary resources. Neither helper deletes a target or source. Use project-scoped `down` to stop/remove disposable containers while retaining volumes. Review exact volume identity and acceptable loss before any later manual deletion. No global prune is needed.

## Rights

Workshop Shelf and the helpers are original MIT-licensed code; see LICENSE. The book prose is separately copyrighted. Images and third-party software keep upstream licenses. FreshRSS1.30.4 is AGPL3: <https://github.com/FreshRSS/FreshRSS/blob/1.30.4/LICENSE.txt>. Its source and official Docker instructions: <https://github.com/FreshRSS/FreshRSS/tree/1.30.4>. No third-party container images are redistributed here.
