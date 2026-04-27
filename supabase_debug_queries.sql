-- ============================================
-- Supabase Debug Queries for Transaction Issue
-- Run these queries in Supabase SQL Editor
-- ============================================

-- 1. Check recent transactions
SELECT 
    ct.id as transaction_id,
    ct.status,
    ct.total_amount,
    ct.created_at,
    u.email as participant_email,
    u.first_name,
    u.last_name,
    (SELECT COUNT(*) FROM caisse_caissetransaction_items cti WHERE cti.caissetransaction_id = ct.id) as items_count
FROM caisse_caissetransaction ct
JOIN events_participant p ON ct.participant_id = p.id
JOIN auth_user u ON p.user_id = u.id
WHERE ct.status = 'completed'
ORDER BY ct.created_at DESC
LIMIT 10;

-- 2. Check items for each transaction
SELECT 
    ct.id as transaction_id,
    ct.created_at,
    u.email as participant_email,
    pi.id as item_id,
    pi.name as item_name,
    pi.item_type,
    pi.price,
    s.title as session_title
FROM caisse_caissetransaction ct
JOIN events_participant p ON ct.participant_id = p.id
JOIN auth_user u ON p.user_id = u.id
LEFT JOIN caisse_caissetransaction_items cti ON ct.id = cti.caissetransaction_id
LEFT JOIN caisse_payableitem pi ON cti.payableitem_id = pi.id
LEFT JOIN events_session s ON pi.session_id = s.id
WHERE ct.status = 'completed'
ORDER BY ct.created_at DESC, pi.name
LIMIT 50;

-- 3. Find orphaned transactions (transactions with NO items)
SELECT 
    ct.id as transaction_id,
    ct.status,
    ct.total_amount,
    ct.created_at,
    u.email as participant_email
FROM caisse_caissetransaction ct
JOIN events_participant p ON ct.participant_id = p.id
JOIN auth_user u ON p.user_id = u.id
LEFT JOIN caisse_caissetransaction_items cti ON ct.id = cti.caissetransaction_id
WHERE ct.status = 'completed'
AND cti.id IS NULL
ORDER BY ct.created_at DESC;

-- 4. Check the many-to-many relationship table
SELECT 
    cti.id,
    cti.caissetransaction_id,
    cti.payableitem_id,
    ct.created_at as transaction_date,
    pi.name as item_name
FROM caisse_caissetransaction_items cti
JOIN caisse_caissetransaction ct ON cti.caissetransaction_id = ct.id
JOIN caisse_payableitem pi ON cti.payableitem_id = pi.id
ORDER BY ct.created_at DESC
LIMIT 20;

-- 5. Check for a specific participant (replace email)
-- REPLACE 'participant@example.com' with actual email
SELECT 
    ct.id as transaction_id,
    ct.status,
    ct.total_amount,
    ct.created_at,
    COUNT(cti.id) as items_count
FROM caisse_caissetransaction ct
JOIN events_participant p ON ct.participant_id = p.id
JOIN auth_user u ON p.user_id = u.id
LEFT JOIN caisse_caissetransaction_items cti ON ct.id = cti.caissetransaction_id
WHERE u.email = 'participant@example.com'  -- CHANGE THIS
GROUP BY ct.id, ct.status, ct.total_amount, ct.created_at
ORDER BY ct.created_at DESC;

-- 6. Detailed view for specific participant
-- REPLACE 'participant@example.com' with actual email
SELECT 
    ct.id as transaction_id,
    ct.created_at,
    ct.total_amount,
    pi.name as item_name,
    pi.item_type,
    pi.price,
    s.title as session_title
FROM caisse_caissetransaction ct
JOIN events_participant p ON ct.participant_id = p.id
JOIN auth_user u ON p.user_id = u.id
LEFT JOIN caisse_caissetransaction_items cti ON ct.id = cti.caissetransaction_id
LEFT JOIN caisse_payableitem pi ON cti.payableitem_id = pi.id
LEFT JOIN events_session s ON pi.session_id = s.id
WHERE u.email = 'participant@example.com'  -- CHANGE THIS
AND ct.status = 'completed'
ORDER BY ct.created_at DESC;

-- 7. Check if items are being added to transactions
SELECT 
    DATE(ct.created_at) as transaction_date,
    COUNT(DISTINCT ct.id) as total_transactions,
    COUNT(cti.id) as total_items_linked,
    AVG(ct.total_amount) as avg_amount
FROM caisse_caissetransaction ct
LEFT JOIN caisse_caissetransaction_items cti ON ct.id = cti.caissetransaction_id
WHERE ct.status = 'completed'
AND ct.created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(ct.created_at)
ORDER BY transaction_date DESC;
