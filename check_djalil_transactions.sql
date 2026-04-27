-- Check transactions for djalil azizi (abdeldjalil.elazizi@ensia.edu.dz)

-- 1. Find the user
SELECT id, email, first_name, last_name 
FROM auth_user 
WHERE email = 'abdeldjalil.elazizi@ensia.edu.dz';

-- 2. Find participant
SELECT p.id, p.badge_id, u.email
FROM events_participant p
JOIN auth_user u ON p.user_id = u.id
WHERE u.email = 'abdeldjalil.elazizi@ensia.edu.dz';

-- 3. Get all transactions for this participant
SELECT 
    ct.id as transaction_id,
    ct.status,
    ct.total_amount,
    ct.created_at,
    (SELECT COUNT(*) FROM caisse_caissetransaction_items cti WHERE cti.caissetransaction_id = ct.id) as items_count
FROM caisse_caissetransaction ct
JOIN events_participant p ON ct.participant_id = p.id
JOIN auth_user u ON p.user_id = u.id
WHERE u.email = 'abdeldjalil.elazizi@ensia.edu.dz'
ORDER BY ct.created_at DESC;

-- 4. Get detailed items for each transaction
SELECT 
    ct.id as transaction_id,
    ct.created_at,
    ct.total_amount,
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
WHERE u.email = 'abdeldjalil.elazizi@ensia.edu.dz'
ORDER BY ct.created_at DESC, pi.name;

-- 5. Check the many-to-many table directly
SELECT 
    cti.id,
    cti.caissetransaction_id,
    cti.payableitem_id,
    ct.total_amount,
    pi.name as item_name,
    pi.price
FROM caisse_caissetransaction_items cti
JOIN caisse_caissetransaction ct ON cti.caissetransaction_id = ct.id
JOIN caisse_payableitem pi ON cti.payableitem_id = pi.id
JOIN events_participant p ON ct.participant_id = p.id
JOIN auth_user u ON p.user_id = u.id
WHERE u.email = 'abdeldjalil.elazizi@ensia.edu.dz'
ORDER BY ct.created_at DESC;
