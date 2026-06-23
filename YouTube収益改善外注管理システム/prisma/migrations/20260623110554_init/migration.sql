-- CreateTable
CREATE TABLE "Outsourcer" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "serviceName" TEXT,
    "contact" TEXT,
    "availableTasks" TEXT,
    "longVideoPrice" INTEGER,
    "shortsPrice" INTEGER,
    "thumbnailPrice" INTEGER,
    "deliveryDays" INTEGER,
    "software" TEXT,
    "voicevoxCapable" BOOLEAN NOT NULL DEFAULT false,
    "materialCapable" BOOLEAN NOT NULL DEFAULT false,
    "thumbnailCapable" BOOLEAN NOT NULL DEFAULT false,
    "continuationOk" BOOLEAN NOT NULL DEFAULT true,
    "continuationStatus" TEXT NOT NULL DEFAULT 'テスト継続',
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "Video" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "projectName" TEXT NOT NULL,
    "title" TEXT,
    "videoType" TEXT NOT NULL DEFAULT '長尺',
    "seriesName" TEXT,
    "theme" TEXT,
    "outsourcerId" TEXT,
    "requestDate" DATETIME,
    "firstDraftDue" DATETIME,
    "deliveryDue" DATETIME,
    "postDate" DATETIME,
    "publicUrl" TEXT,
    "status" TEXT NOT NULL DEFAULT '企画中',
    "scriptCost" INTEGER NOT NULL DEFAULT 0,
    "editingCost" INTEGER NOT NULL DEFAULT 0,
    "shortsEditCost" INTEGER NOT NULL DEFAULT 0,
    "thumbnailCost" INTEGER NOT NULL DEFAULT 0,
    "materialCost" INTEGER NOT NULL DEFAULT 0,
    "bgmCost" INTEGER NOT NULL DEFAULT 0,
    "otherCost" INTEGER NOT NULL DEFAULT 0,
    "totalCost" INTEGER NOT NULL DEFAULT 0,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "Video_outsourcerId_fkey" FOREIGN KEY ("outsourcerId") REFERENCES "Outsourcer" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "VideoMetrics" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "videoId" TEXT NOT NULL,
    "views24h" INTEGER,
    "views48h" INTEGER,
    "views7d" INTEGER,
    "views30d" INTEGER,
    "totalViews" INTEGER,
    "impressions" INTEGER,
    "ctr" REAL,
    "avgWatchTime" REAL,
    "avgRetention" REAL,
    "likes" INTEGER,
    "comments" INTEGER,
    "subscribersGained" INTEGER,
    "estimatedRevenue" REAL,
    "rpm" REAL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "VideoMetrics_videoId_fkey" FOREIGN KEY ("videoId") REFERENCES "Video" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "VideoShortsMetrics" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "videoId" TEXT NOT NULL,
    "feedImpressions" INTEGER,
    "selectRate" REAL,
    "swipeAwayRate" REAL,
    "avgPlayRate" REAL,
    "hasLoopViews" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "VideoShortsMetrics_videoId_fkey" FOREIGN KEY ("videoId") REFERENCES "Video" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "VideoQuality" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "videoId" TEXT NOT NULL,
    "firstDraftRevisions" INTEGER NOT NULL DEFAULT 0,
    "majorRevisions" INTEGER NOT NULL DEFAULT 0,
    "minorRevisions" INTEGER NOT NULL DEFAULT 0,
    "typoErrors" INTEGER NOT NULL DEFAULT 0,
    "voiceMisreads" INTEGER NOT NULL DEFAULT 0,
    "subtitleMismatch" INTEGER NOT NULL DEFAULT 0,
    "materialMismatch" INTEGER NOT NULL DEFAULT 0,
    "aiGeneratedImages" BOOLEAN NOT NULL DEFAULT false,
    "unknownRightsMaterial" BOOLEAN NOT NULL DEFAULT false,
    "bgmIssues" INTEGER NOT NULL DEFAULT 0,
    "deliveryDelay" BOOLEAN NOT NULL DEFAULT false,
    "communicationDelay" BOOLEAN NOT NULL DEFAULT false,
    "reviewTime" REAL,
    "finalScore" REAL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "VideoQuality_videoId_fkey" FOREIGN KEY ("videoId") REFERENCES "Video" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "VideoRisk" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "videoId" TEXT NOT NULL,
    "aiGeneratedRoyal" BOOLEAN NOT NULL DEFAULT false,
    "faceModification" BOOLEAN NOT NULL DEFAULT false,
    "unknownRightsPhoto" BOOLEAN NOT NULL DEFAULT false,
    "tvFootage" BOOLEAN NOT NULL DEFAULT false,
    "longNewsFootage" BOOLEAN NOT NULL DEFAULT false,
    "otherChannelReuse" BOOLEAN NOT NULL DEFAULT false,
    "watermarkedMaterial" BOOLEAN NOT NULL DEFAULT false,
    "unknownSourceMaterial" BOOLEAN NOT NULL DEFAULT false,
    "reuseContentRisk" BOOLEAN NOT NULL DEFAULT false,
    "exaggeration" BOOLEAN NOT NULL DEFAULT false,
    "innerThoughtClaim" BOOLEAN NOT NULL DEFAULT false,
    "politicalClaim" BOOLEAN NOT NULL DEFAULT false,
    "adSuitabilityRisk" BOOLEAN NOT NULL DEFAULT false,
    "riskLevel" TEXT NOT NULL DEFAULT '低',
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "VideoRisk_videoId_fkey" FOREIGN KEY ("videoId") REFERENCES "Video" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Order" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "videoId" TEXT,
    "outsourcerId" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "deliverable" TEXT NOT NULL,
    "price" INTEGER NOT NULL,
    "deadline" DATETIME,
    "instructionUrl" TEXT,
    "referenceUrl" TEXT,
    "bgmUrl" TEXT,
    "startDate" DATETIME,
    "firstDraftDue" DATETIME,
    "revisionDate" DATETIME,
    "deliveryDate" DATETIME,
    "paymentStatus" TEXT NOT NULL DEFAULT '未払い',
    "reviewStatus" TEXT NOT NULL DEFAULT '未検収',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "Order_videoId_fkey" FOREIGN KEY ("videoId") REFERENCES "Video" ("id") ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "Order_outsourcerId_fkey" FOREIGN KEY ("outsourcerId") REFERENCES "Outsourcer" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Setting" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "key" TEXT NOT NULL,
    "value" TEXT NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "VideoMetrics_videoId_key" ON "VideoMetrics"("videoId");

-- CreateIndex
CREATE UNIQUE INDEX "VideoShortsMetrics_videoId_key" ON "VideoShortsMetrics"("videoId");

-- CreateIndex
CREATE UNIQUE INDEX "VideoQuality_videoId_key" ON "VideoQuality"("videoId");

-- CreateIndex
CREATE UNIQUE INDEX "Setting_key_key" ON "Setting"("key");
