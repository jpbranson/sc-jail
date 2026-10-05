---
type: Drill Record
title: Restore drill, 2026-09-26
description: A rehearsal restored the daily backup into a separate local folder, verified history, and rebuilt identical projections in about 35 minutes.
tags: [backup, operations]
date: 2026-09-26
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: cloud-l445
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L445-L465
    title: docs/CLOUD.md lines 445-465, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

A rehearsal restored the [backup](backup-and-restore.md) into a separate local folder
(`data/restore-drill/2026-09-26`) with the live archive and collector untouched:

1. The backup job was enabled and its latest daily copy (September 25, 05:10 UTC)
   succeeded. Inventories by name, size, and CRC32C showed all 8,839 history objects
   written before that copy identical in the backup; the only differences were newer
   objects and six projections updated later. The lease is excluded by design.
2. `gcloud storage rsync` restored 9,117 objects (265,001,340 bytes), matching the backup
   inventory exactly (inventory SHA-256 `e27dab979d64b5e1817e48a5e0da0d2d1fc686574f1963e21d7c048ce5e0989f`).
3. With `SCJ_BUCKET` unset and `SCJ_DATA_DIR` pointing at the restored folder:
   `migrate_history.py --verify-only` verified 2,066 observations (11 minutes);
   `rebuild_index.py` rebuilt 515 IML and 543 XFER points, identical to the backed-up
   public index except the operational `attempts` and `last_attempt` fields (11 minutes);
   `update_repeat_visits.py --rebuild` reproduced all 18 public repeat-visit fields and all
   3,760 private visit records (5 minutes). A booking panel built from the restored copy
   matched all 515 archived IML populations.

A full restore and rebuild took about 35 minutes on a desktop. The drill does not
exercise restoring soft-deleted archive generations or noncurrent backup versions.
