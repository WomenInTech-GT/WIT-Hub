BEGIN;
CREATE TABLE opportunities (
    id text PRIMARY KEY,
    title text NOT NULL CHECK (length(trim(title)) > 0),
    description text NOT NULL DEFAULT '',
    source_url text NOT NULL,
    opportunity_type text NOT NULL,
    eligible_majors text[] NOT NULL DEFAULT '{}',
    eligible_years integer[] NOT NULL DEFAULT '{}'
        CHECK (eligible_years <@ ARRAY[1,2,3,4]),
    experience_levels text[] NOT NULL DEFAULT '{}'
        CHECK (experience_levels <@ ARRAY['beginner','intermediate','advanced']),
    tags text[] NOT NULL DEFAULT '{}',
    location_mode text NOT NULL CHECK (location_mode IN ('online','in-person')),
    location_name text NOT NULL DEFAULT '',
    starts_at timestamptz,
    ends_at timestamptz,
    application_deadline timestamptz,
    search_vector tsvector NOT NULL,
    CHECK (ends_at IS NULL OR (starts_at IS NOT NULL AND ends_at >= starts_at))
);

CREATE FUNCTION update_opportunity_search() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.opportunity_type := lower(trim(NEW.opportunity_type));
    NEW.eligible_majors := ARRAY(SELECT DISTINCT lower(trim(v)) FROM unnest(NEW.eligible_majors) v WHERE trim(v) <> '');
    NEW.tags := ARRAY(SELECT DISTINCT lower(trim(v)) FROM unnest(NEW.tags) v WHERE trim(v) <> '');
    NEW.search_vector :=
        setweight(to_tsvector('english', NEW.title), 'A') ||
        setweight(to_tsvector('english', array_to_string(NEW.tags, ' ') || ' ' || NEW.opportunity_type), 'B') ||
        setweight(to_tsvector('english', NEW.description || ' ' || NEW.location_name), 'C');
    RETURN NEW;
END;
$$;
CREATE TRIGGER opportunities_search_update BEFORE INSERT OR UPDATE ON opportunities
FOR EACH ROW EXECUTE FUNCTION update_opportunity_search();
CREATE INDEX opportunities_search_idx ON opportunities USING gin(search_vector);
CREATE INDEX opportunities_deadline_idx ON opportunities(application_deadline);
CREATE INDEX opportunities_start_idx ON opportunities(starts_at);
COMMIT;
