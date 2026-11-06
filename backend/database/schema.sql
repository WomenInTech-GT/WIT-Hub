-- 1. Opportunities
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY -- ensure unique
        CHECK (length(trim(id)) > 0),

    title TEXT NOT NULL
        CHECK (length(trim(title)) > 0),

    organization TEXT NOT NULL
        CHECK (length(trim(organization)) > 0),

    description TEXT NOT NULL
        CHECK (length(trim(description)) > 0),

    type TEXT NOT NULL
        CHECK (length(trim(type)) > 0),

    location TEXT,

    deadline DATE,

    eligibility TEXT[] NOT NULL
        DEFAULT ARRAY[]::TEXT[],

    tags TEXT[] NOT NULL
        DEFAULT ARRAY[]::TEXT[],

    url TEXT NOT NULL
        CHECK (url ~* '^https?://[^[:space:]]+$'),

    source TEXT NOT NULL
        CHECK (length(trim(source)) > 0),

    last_updated DATE NOT NULL
);


-- 2. Events
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY
        CHECK (length(trim(id)) > 0),

    title TEXT NOT NULL
        CHECK (length(trim(title)) > 0),

    organization TEXT NOT NULL
        CHECK (length(trim(organization)) > 0),

    description TEXT NOT NULL
        CHECK (length(trim(description)) > 0),

    date DATE NOT NULL,

    time TIME,

    location TEXT,

    eligibility TEXT[] NOT NULL
        DEFAULT ARRAY[]::TEXT[],

    tags TEXT[] NOT NULL
        DEFAULT ARRAY[]::TEXT[],

    recurrence TEXT,

    url TEXT NOT NULL
        CHECK (url ~* '^https?://[^[:space:]]+$'),

    source TEXT NOT NULL
        CHECK (length(trim(source)) > 0),

    last_updated DATE NOT NULL
);


-- 3. Programs
CREATE TABLE IF NOT EXISTS programs (
    id TEXT PRIMARY KEY
        CHECK (length(trim(id)) > 0),

    title TEXT NOT NULL
        CHECK (length(trim(title)) > 0),

    organization TEXT NOT NULL
        CHECK (length(trim(organization)) > 0),

    description TEXT NOT NULL
        CHECK (length(trim(description)) > 0),

    type TEXT NOT NULL
        CHECK (length(trim(type)) > 0),

    location TEXT,

    deadline DATE,

    eligibility TEXT[] NOT NULL
        DEFAULT ARRAY[]::TEXT[],

    tags TEXT[] NOT NULL
        DEFAULT ARRAY[]::TEXT[],

    url TEXT NOT NULL
        CHECK (url ~* '^https?://[^[:space:]]+$'),

    source TEXT NOT NULL
        CHECK (length(trim(source)) > 0),

    last_updated DATE NOT NULL
);


-- 4. Resources
CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY
        CHECK (length(trim(id)) > 0),

    title TEXT NOT NULL
        CHECK (length(trim(title)) > 0),

    description TEXT NOT NULL
        CHECK (length(trim(description)) > 0),

    type TEXT NOT NULL
        CHECK (length(trim(type)) > 0),

    tags TEXT[] NOT NULL
        DEFAULT ARRAY[]::TEXT[],

    url TEXT NOT NULL
        CHECK (url ~* '^https?://[^[:space:]]+$'),

    source TEXT NOT NULL
        CHECK (length(trim(source)) > 0),

    last_updated DATE NOT NULL
);