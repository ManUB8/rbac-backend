ALTER TABLE activities
ADD COLUMN IF NOT EXISTS target_group VARCHAR(30) NOT NULL DEFAULT 'all';

ALTER TABLE activities
DROP CONSTRAINT IF EXISTS chk_activity_target_group;

ALTER TABLE activities
ADD CONSTRAINT chk_activity_target_group
CHECK (target_group IN ('all', 'freshman', 'senior'));
