-- Optional PostgreSQL target for the JSON MVP's shared content contract.
-- Additive: 001 and its consumers remain intact until the application cutover.
BEGIN;
CREATE SCHEMA catalog;

CREATE TABLE catalog.content_items (
    id text PRIMARY KEY CHECK (length(trim(id)) > 0),
    content_kind text NOT NULL
        CHECK (content_kind IN ('opportunity', 'event', 'program', 'resource')),
    category text NOT NULL CHECK (length(trim(category)) > 0),
    title text NOT NULL CHECK (length(trim(title)) > 0),
    description text NOT NULL CHECK (length(trim(description)) > 0),
    organization text CHECK (organization IS NULL OR length(trim(organization)) > 0),
    url text NOT NULL CHECK (url ~* '^https?://[^[:space:]]+$'),
    source text NOT NULL CHECK (length(trim(source)) > 0),
    last_updated date NOT NULL,
    tags text[] NOT NULL DEFAULT '{}',
    relevant_majors text[] NOT NULL DEFAULT '{}',

    -- Human-readable requirements are retained, not inferred from tags.
    eligibility text[] NOT NULL DEFAULT '{}',
    eligibility_status text NOT NULL DEFAULT 'unknown'
        CHECK (eligibility_status IN ('unknown', 'unrestricted', 'restricted')),
    eligible_majors text[] NOT NULL DEFAULT '{}',
    eligible_years integer[] NOT NULL DEFAULT '{}'
        CHECK (eligible_years <@ ARRAY[1,2,3,4]),
    experience_levels text[] NOT NULL DEFAULT '{}'
        CHECK (experience_levels <@ ARRAY['beginner','intermediate','advanced']),

    location_mode text NOT NULL DEFAULT 'unknown'
        CHECK (location_mode IN ('unknown', 'online', 'in-person', 'hybrid', 'not-applicable')),
    location text CHECK (location IS NULL OR length(trim(location)) > 0),

    -- Date-only and timed schedules are mutually exclusive. Do not invent midnight.
    schedule_precision text NOT NULL DEFAULT 'unknown'
        CHECK (schedule_precision IN ('unknown', 'date', 'time', 'not-applicable')),
    start_date date,
    end_date date,
    starts_at timestamptz,
    ends_at timestamptz,
    timezone text,
    recurrence text CHECK (recurrence IS NULL OR length(trim(recurrence)) > 0),

    -- For events, deadline means registration; for programs/opportunities, application.
    deadline_status text NOT NULL DEFAULT 'unknown'
        CHECK (deadline_status IN ('unknown', 'fixed', 'rolling', 'none')),
    deadline_date date,
    deadline_at timestamptz,
    deadline_timezone text,
    search_vector tsvector NOT NULL,

    CONSTRAINT organization_required CHECK (content_kind = 'resource' OR organization IS NOT NULL),
    CONSTRAINT arrays_have_no_nulls CHECK (
        array_position(tags, NULL) IS NULL AND
        array_position(relevant_majors, NULL) IS NULL AND
        array_position(eligibility, NULL) IS NULL AND
        array_position(eligible_majors, NULL) IS NULL AND
        array_position(eligible_years, NULL) IS NULL AND
        array_position(experience_levels, NULL) IS NULL
    ),
    CONSTRAINT eligibility_consistency CHECK (
        (eligibility_status = 'restricted' AND
            cardinality(eligibility) + cardinality(eligible_majors) +
            cardinality(eligible_years) + cardinality(experience_levels) > 0)
        OR (eligibility_status IN ('unknown', 'unrestricted') AND
            cardinality(eligibility) = 0 AND cardinality(eligible_majors) = 0 AND
            cardinality(eligible_years) = 0 AND cardinality(experience_levels) = 0)
    ),
    CONSTRAINT schedule_consistency CHECK (
        (schedule_precision IN ('unknown', 'not-applicable') AND
            start_date IS NULL AND end_date IS NULL AND starts_at IS NULL AND
            ends_at IS NULL AND timezone IS NULL)
        OR (schedule_precision = 'date' AND start_date IS NOT NULL AND
            (end_date IS NULL OR end_date >= start_date) AND
            starts_at IS NULL AND ends_at IS NULL AND timezone IS NOT NULL)
        OR (schedule_precision = 'time' AND starts_at IS NOT NULL AND
            (ends_at IS NULL OR ends_at >= starts_at) AND
            start_date IS NULL AND end_date IS NULL AND timezone IS NOT NULL)
    ),
    CONSTRAINT deadline_consistency CHECK (
        (deadline_status = 'fixed' AND
            ((deadline_date IS NOT NULL AND deadline_at IS NULL) OR
             (deadline_date IS NULL AND deadline_at IS NOT NULL)) AND
            deadline_timezone IS NOT NULL)
        OR (deadline_status <> 'fixed' AND deadline_date IS NULL AND
            deadline_at IS NULL AND deadline_timezone IS NULL)
    ),
    CONSTRAINT events_have_schedule CHECK (
        content_kind <> 'event' OR schedule_precision IN ('date', 'time')
    ),
    CONSTRAINT recurrence_is_event_only CHECK (recurrence IS NULL OR content_kind = 'event'),
    CONSTRAINT resources_have_no_schedule CHECK (
        content_kind <> 'resource' OR
        (schedule_precision = 'not-applicable' AND deadline_status = 'none' AND
         location_mode = 'not-applicable' AND location IS NULL)
    ),
    CONSTRAINT participation_schedule_applicable CHECK (
        content_kind = 'resource' OR schedule_precision <> 'not-applicable'
    )
);

CREATE FUNCTION catalog.normalize_terms(values_ text[]) RETURNS text[]
LANGUAGE sql IMMUTABLE STRICT AS $$
    SELECT ARRAY(SELECT DISTINCT lower(trim(value)) FROM unnest(values_) value
                 WHERE trim(value) <> '' ORDER BY 1);
$$;

CREATE FUNCTION catalog.prepare_content() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    -- Reject invalid input before normalization could hide it.
    IF array_position(NEW.tags, NULL) IS NOT NULL OR
       array_position(NEW.relevant_majors, NULL) IS NOT NULL OR
       array_position(NEW.eligible_majors, NULL) IS NOT NULL OR
       array_position(NEW.eligibility, NULL) IS NOT NULL OR
       EXISTS (SELECT 1 FROM unnest(NEW.eligibility) value WHERE trim(value) = '') THEN
        RAISE EXCEPTION 'Content arrays cannot contain nulls; eligibility text cannot be blank';
    END IF;
    IF NEW.timezone IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM pg_timezone_names WHERE name = NEW.timezone
    ) THEN
        RAISE EXCEPTION 'Unknown schedule timezone: %', NEW.timezone;
    END IF;
    IF NEW.deadline_timezone IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM pg_timezone_names WHERE name = NEW.deadline_timezone
    ) THEN
        RAISE EXCEPTION 'Unknown deadline timezone: %', NEW.deadline_timezone;
    END IF;
    NEW.category := lower(trim(NEW.category));
    NEW.tags := catalog.normalize_terms(NEW.tags);
    NEW.relevant_majors := catalog.normalize_terms(NEW.relevant_majors);
    NEW.eligible_majors := catalog.normalize_terms(NEW.eligible_majors);
    NEW.search_vector :=
        setweight(to_tsvector('english', NEW.title), 'A') ||
        setweight(to_tsvector('english', concat_ws(' ', NEW.organization, NEW.category,
            NEW.content_kind, array_to_string(NEW.tags, ' '))), 'B') ||
        setweight(to_tsvector('english', concat_ws(' ', NEW.description, NEW.location,
            array_to_string(NEW.relevant_majors, ' '))), 'C');
    RETURN NEW;
END;
$$;

CREATE TRIGGER content_prepare BEFORE INSERT OR UPDATE ON catalog.content_items
FOR EACH ROW EXECUTE FUNCTION catalog.prepare_content();

CREATE INDEX content_search_idx ON catalog.content_items USING gin(search_vector);
CREATE INDEX content_kind_category_idx ON catalog.content_items(content_kind, category);
CREATE INDEX content_deadline_at_idx ON catalog.content_items(deadline_at);
CREATE INDEX content_deadline_date_idx ON catalog.content_items(deadline_date);
CREATE INDEX content_starts_at_idx ON catalog.content_items(starts_at);
CREATE INDEX content_start_date_idx ON catalog.content_items(start_date);

-- One globally unique ID and one common search representation, four entry points.
-- Supply content_kind explicitly when inserting through a view.
CREATE VIEW catalog.opportunities AS
    SELECT * FROM catalog.content_items WHERE content_kind = 'opportunity'
    WITH CASCADED CHECK OPTION;
CREATE VIEW catalog.events AS
    SELECT * FROM catalog.content_items WHERE content_kind = 'event'
    WITH CASCADED CHECK OPTION;
CREATE VIEW catalog.programs AS
    SELECT * FROM catalog.content_items WHERE content_kind = 'program'
    WITH CASCADED CHECK OPTION;
CREATE VIEW catalog.resources AS
    SELECT * FROM catalog.content_items WHERE content_kind = 'resource'
    WITH CASCADED CHECK OPTION;
COMMIT;
