CREATE TABLE IF NOT EXISTS "sessions" (
    "session_id"  TEXT      NOT NULL  UNIQUE,
    "username"    TEXT      NOT NULL  UNIQUE,
    "agent"       TEXT      NOT NULL,
    "time"        NUMERIC   NOT NULL
);

CREATE TABLE IF NOT EXISTS "users" (
    "id"           INTEGER   PRIMARY KEY AUTOINCREMENT UNIQUE,
    "login"        TEXT      NOT NULL,
    "bind_token"   TEXT      NULL,
    "email2"       TEXT      NULL,
    "phone"        INT       NULL,
    "telegram"     INT       NULL,
    "otp"          INT       NULL,
    "reset_token"  INT       NULL
);
