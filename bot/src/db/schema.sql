-- SQLite schema for Votum.

-- Table storing councils.  Each council is tied to a guild and channel.
CREATE TABLE IF NOT EXISTS councils (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id        INTEGER NOT NULL,
    channel_id      INTEGER NOT NULL UNIQUE,
    name            TEXT NOT NULL
);

-- Configuration key/value pairs per council.  Values are stored as JSON strings.
CREATE TABLE IF NOT EXISTS configs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    council_id  INTEGER NOT NULL,
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    UNIQUE(council_id, key),
    FOREIGN KEY(council_id) REFERENCES councils(id) ON DELETE CASCADE
);

-- Motions proposed within councils.  The majority is stored as a numerator and
-- denominator to support fractions and percentages (e.g. 2/3).  The status can
-- be 'active', 'passed', 'failed', or 'killed'.
CREATE TABLE IF NOT EXISTS motions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    council_id      INTEGER NOT NULL,
    author_id       INTEGER NOT NULL,
    text            TEXT NOT NULL,
    majority_num    INTEGER NOT NULL,
    majority_den    INTEGER NOT NULL,
    unanimous       INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      DATETIME,
    closed_at       DATETIME,
    result          TEXT,
    transcript_id   INTEGER,
    FOREIGN KEY(council_id) REFERENCES councils(id) ON DELETE CASCADE,
    FOREIGN KEY(transcript_id) REFERENCES transcripts(id) ON DELETE SET NULL
);

-- Votes cast on motions.  `vote` is one of 'yes', 'no' or 'abstain'.  Weight is
-- stored as a floating‑point value after calculating role and user weights.
CREATE TABLE IF NOT EXISTS votes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    motion_id   INTEGER NOT NULL,
    user_id     INTEGER NOT NULL,
    vote        TEXT NOT NULL,
    reason      TEXT,
    weight      REAL NOT NULL DEFAULT 1.0,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(motion_id, user_id),
    FOREIGN KEY(motion_id) REFERENCES motions(id) ON DELETE CASCADE
);

-- Vote weights per council.  Targets may be a user or a role; target_type
-- indicates 'user' or 'role'.
CREATE TABLE IF NOT EXISTS weights (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    council_id  INTEGER NOT NULL,
    target_type TEXT NOT NULL,
    target_id   INTEGER NOT NULL,
    weight      INTEGER NOT NULL,
    UNIQUE(council_id, target_type, target_id),
    FOREIGN KEY(council_id) REFERENCES councils(id) ON DELETE CASCADE
);

-- Motion queue when `motion.queue` is enabled.  New motions are queued until
-- the current motion ends.
CREATE TABLE IF NOT EXISTS queue (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    council_id  INTEGER NOT NULL,
    motion_id   INTEGER NOT NULL,
    position    INTEGER NOT NULL,
    UNIQUE(council_id, position),
    UNIQUE(council_id, motion_id),
    FOREIGN KEY(council_id) REFERENCES councils(id) ON DELETE CASCADE,
    FOREIGN KEY(motion_id) REFERENCES motions(id) ON DELETE CASCADE
);

-- Motion transcripts when deliberation threads are saved.  The content column
-- stores raw text extracted from the discussion thread.
CREATE TABLE IF NOT EXISTS transcripts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    motion_id   INTEGER NOT NULL UNIQUE,
    content     TEXT NOT NULL,
    FOREIGN KEY(motion_id) REFERENCES motions(id) ON DELETE CASCADE
);

-- Audit log of administrative actions.  Stores the guild, user and a JSON
-- payload describing the action.
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    user_id     INTEGER NOT NULL,
    action      TEXT NOT NULL,
    details     TEXT NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table tracking applied migrations.  Currently unused but reserved for
-- future schema updates.
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY
);