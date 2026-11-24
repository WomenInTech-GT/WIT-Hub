-- Apply after 002_content_catalog.sql on new and existing installations.
BEGIN;
CREATE TABLE catalog.categories (
    category text PRIMARY KEY CHECK (category <> '' AND category = lower(trim(category)))
);
INSERT INTO catalog.categories (category) VALUES('internship'),
('scholarship'),
('competition'),
('job'),
('research'),
('project'),
('workshop'),
('conference'),
('hackathon'),
('event'),
('program'),
('mentorship'),
('guide'),
('tutorial');
CREATE TABLE catalog.category_aliases (
    alias text PRIMARY KEY CHECK (alias <> '' AND alias = lower(trim(alias))),
    category text NOT NULL REFERENCES catalog.categories(category)
);
-- Explicit aliases only; never guess by stripping trailing letters.
INSERT INTO catalog.category_aliases (alias, category) VALUES('internships', 'internship'),
('scholarships', 'scholarship'),
('competitions', 'competition'),
('jobs', 'job'),
('projects', 'project'),
('workshops', 'workshop'),
('conferences', 'conference'),
('hackathons', 'hackathon'),
('events', 'event'),
('programs', 'program'),
('mentorships', 'mentorship'),
('guides', 'guide'),
('tutorials', 'tutorial');
CREATE FUNCTION catalog.normalize_category(value_ text) RETURNS text
LANGUAGE sql STABLE STRICT AS $$
    SELECT coalesce((SELECT category FROM catalog.category_aliases
                     WHERE alias = lower(trim(value_))), lower(trim(value_)));
$$;
CREATE OR REPLACE FUNCTION catalog.prepare_content() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    -- Reject invalid input before normalization could hide it.
    IF array_position(NEW.experience_levels, NULL) IS NOT NULL OR
       array_position(NEW.tags, NULL) IS NOT NULL OR
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
    NEW.category := catalog.normalize_category(NEW.category);
    NEW.experience_levels := catalog.normalize_terms(NEW.experience_levels);
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

-- The trigger refreshes search vectors too. Unknown legacy categories cause
-- an atomic rollback: review and map them before retrying; never discard rows.
UPDATE catalog.content_items SET category = category,
    experience_levels = experience_levels;
ALTER TABLE catalog.content_items ADD CONSTRAINT content_category_known
    FOREIGN KEY (category) REFERENCES catalog.categories(category);
COMMIT;
