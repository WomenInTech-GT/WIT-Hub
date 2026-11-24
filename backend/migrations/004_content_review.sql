-- Publication is opt-in. Existing content becomes draft pending explicit review.
BEGIN;
INSERT INTO catalog.categories (category) VALUES
    ('conference support'), ('award'), ('recognition'), ('leadership program'),
    ('workshop series'), ('mentorship program'), ('research internship'),
    ('research directory'), ('research opportunity'), ('career event'),
    ('research advising'), ('international internship'), ('course / program'),
    ('innovation program'), ('capstone program'), ('accelerator'), ('makerspace'),
    ('seminar'), ('conference session'), ('student project showcase'), ('info session')
ON CONFLICT DO NOTHING;

ALTER TABLE catalog.content_items
    ADD COLUMN publication_status text NOT NULL DEFAULT 'draft_review'
        CHECK (publication_status IN ('draft_review', 'approved', 'rejected')),
    ADD COLUMN reviewed_by text,
    ADD COLUMN reviewed_at timestamptz,
    ADD CONSTRAINT content_approval_required CHECK (
        publication_status <> 'approved' OR
        (reviewed_by IS NOT NULL AND length(trim(reviewed_by)) > 0 AND reviewed_at IS NOT NULL)
    );

-- Incomplete source records belong here, not in the searchable content table.
CREATE TABLE catalog.content_drafts (
    id text PRIMARY KEY CHECK (length(trim(id)) > 0),
    source_payload jsonb NOT NULL CHECK (jsonb_typeof(source_payload) = 'object'),
    mapping jsonb NOT NULL CHECK (jsonb_typeof(mapping) = 'object'),
    source_digest text NOT NULL,
    validation_issues jsonb NOT NULL,
    publication_status text NOT NULL DEFAULT 'draft_review'
        CHECK (publication_status IN ('draft_review', 'approved', 'rejected')),
    imported_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A student project is a showcase artifact, not an opportunity or a resource.
CREATE TABLE catalog.student_projects (
    id text PRIMARY KEY CHECK (length(trim(id)) > 0),
    title text,
    category text,
    team text,
    year integer CHECK (year BETWEEN 1900 AND 9999),
    summary text,
    problem text,
    solution text,
    technologies text[] NOT NULL DEFAULT '{}'
        CHECK (array_position(technologies, NULL) IS NULL),
    url text CHECK (url ~* '^https?://[^[:space:]]+$'),
    publication_permission text NOT NULL DEFAULT 'unconfirmed'
        CHECK (publication_permission IN ('unconfirmed', 'granted', 'denied')),
    permission_evidence text,
    publication_status text NOT NULL DEFAULT 'draft_review'
        CHECK (publication_status IN ('draft_review', 'approved', 'rejected')),
    reviewed_by text,
    reviewed_at timestamptz,
    source_payload jsonb NOT NULL,
    source_digest text NOT NULL,
    CONSTRAINT project_approval_required CHECK (
        publication_status <> 'approved' OR
        (publication_permission = 'granted' AND
         coalesce(length(trim(permission_evidence)), 0) > 0 AND
         coalesce(length(trim(reviewed_by)), 0) > 0 AND reviewed_at IS NOT NULL AND
         coalesce(length(trim(title)), 0) > 0 AND
         coalesce(length(trim(category)), 0) > 0 AND
         coalesce(length(trim(team)), 0) > 0 AND year IS NOT NULL AND
         coalesce(length(trim(summary)), 0) > 0 AND
         coalesce(length(trim(problem)), 0) > 0 AND
         coalesce(length(trim(solution)), 0) > 0 AND url IS NOT NULL)
    )
);

CREATE VIEW catalog.published_content AS
    SELECT * FROM catalog.content_items WHERE publication_status = 'approved';
CREATE VIEW catalog.published_student_projects AS
    SELECT id, title, category, team, year, summary, problem, solution, technologies, url
    FROM catalog.student_projects
    WHERE publication_status = 'approved' AND publication_permission = 'granted';
COMMIT;
