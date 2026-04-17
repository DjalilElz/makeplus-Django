-- Fix EmailLoginCode table - Add missing columns
-- Run this if migrations don't work

-- Add missing columns
ALTER TABLE events_emaillogincode 
ADD COLUMN IF NOT EXISTS is_used BOOLEAN DEFAULT FALSE;

ALTER TABLE events_emaillogincode 
ADD COLUMN IF NOT EXISTS used_at TIMESTAMP NULL;

ALTER TABLE events_emaillogincode 
ADD COLUMN IF NOT EXISTS ip_address INET NULL;

ALTER TABLE events_emaillogincode 
ADD COLUMN IF NOT EXISTS user_agent TEXT DEFAULT '';

-- Create index for performance
CREATE INDEX IF NOT EXISTS events_emai_user_id_b75a1f_idx 
ON events_emaillogincode (user_id, event_id, is_used);

CREATE INDEX IF NOT EXISTS events_emai_code_ha_idx 
ON events_emaillogincode (code_hash);

-- Verify the table structure
\d events_emaillogincode
