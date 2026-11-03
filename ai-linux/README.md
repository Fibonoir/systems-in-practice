# AI-Assisted Linux Automation — companion labs

Original educational lab source accompanying the book by Martin J. Ellis. The scripts are readable Bash files and one awk program, not an installer.

From this extracted directory in Linux Bash:

```bash
LAB=$(bash labs/setup.sh)
status=$?
if [[ $status -eq 0 ]]; then
    printf 'fixture=%s\n' "$LAB"
    bash labs/inventory.sh "$LAB/incoming"
fi
```

The original fixture yields `files=4 bytes=19`. Setup creates a private directory under the Linux home and retains earlier fixtures. Keep its path to resume; create a fresh fixture to reset. Do not source the scripts into your interactive shell.

Run `bash labs/verify.sh` for 45 acceptance checks. Run the printed chapter steps separately, observing intentional failures and expected results. If your Linux system has a reachable systemd user manager, `bash labs/schedule-demo.sh "$LAB"` tests one transient timer and stops its units afterward. It installs no permanent schedule.

Named environment: Ubuntu 26.04 LTS on WSL2, Bash 5.3.9, findutils 4.10.0, GNU Awk 5.3.2, GNU tar 1.35, util-linux 2.41.3, systemd 259; mixed core command implementations include uutils 0.8.0 and GNU mv 9.7. Test the actual implementations on another environment rather than assuming compatibility from command names.

All data is synthetic. Core labs require no root, network or paid model. Read the book's contracts before adapting paths to real data. The snapshot is a same-machine teaching archive; the quarantine workflow moves only eligible empty top-level `.tmp` files and can leave a partial batch after failure. The daily runner does not call quarantine. The strict configuration parser is a standalone extension, not automatically connected to the runner.

Permission: readers may copy, modify and use this original lab code for learning and their own automation, with no warranty. Third-party tools retain their own licences. These permissions do not grant rights to redistribute the book manuscript. The text/code were AI-generated under publisher direction and checked through source review and Linux execution; no captured model response or learner trial is implied.
