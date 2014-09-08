CREATE TABLE stations (
    "STATION_ID" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "STATION_NAME" TEXT NOT NULL,
    "STATION_STATE" TEXT,
    "STATION_CITY" TEXT
);
CREATE UNIQUE INDEX "STATION_ID" on stations (STATION_ID ASC);
CREATE UNIQUE INDEX "STATION_NAME" on stations (STATION_NAME ASC);

CREATE TABLE "feeds" (
    "FEED_PK" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "FEED_ID" INTEGER NOT NULL,
--    FOREIGN KEY(STATION_ID) REFERENCES stations(STATION_ID),
	"STATION_ID" INTEGER NOT NULL,
    "FEED_NAME" TEXT NOT NULL,
    "FEED_URL" TEXT NOT NULL,
    "FEED_RESOLUTION" TEXT,
    "FEED_BANDWIDTH" INTEGER,
    "FEED_CODECS" TEXT
    -- Video feed protection schemes may require the stream to be processed through
    -- an external daemon before playback is possible.
    "FEED_REQUIRES_PROXY" TEXT NOT NULL DEFAULT ('False')
);
CREATE UNIQUE INDEX "FEED_PK" on feeds (FEED_PK ASC);
CREATE UNIQUE INDEX "FEED_ID" on feeds (FEED_ID ASC);