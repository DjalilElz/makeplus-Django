#!/bin/bash
# Deploy Transaction Items Fix to Render

echo "=========================================="
echo "Deploying Transaction Items Fix"
echo "=========================================="
echo ""

# Check git status
echo "1. Checking git status..."
git status
echo ""

# Add all changes
echo "2. Adding changes to git..."
git add makeplus_api/caisse/views.py
git add makeplus_api/events/views.py
git add TRANSACTION_FIX_SUMMARY.md
git add TEST_TRANSACTION_FIX.md
git add supabase_debug_queries.sql
echo "✅ Files added"
echo ""

# Commit changes
echo "3. Committing changes..."
git commit -m "Fix: Ensure transaction items are properly saved to database

- Wrapped transaction creation in atomic block
- Changed from items.set() to items.add() for better reliability
- Added verification to check items were actually saved
- Enhanced logging with visual indicators
- Added debug endpoint for troubleshooting
- Improved scan_participant logging

This fixes the issue where participants made payments but controllers
only saw old payments when scanning QR codes."
echo "✅ Changes committed"
echo ""

# Push to GitHub (triggers Render deployment)
echo "4. Pushing to GitHub..."
git push origin main
echo "✅ Pushed to GitHub"
echo ""

echo "=========================================="
echo "Deployment initiated!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Go to https://dashboard.render.com"
echo "2. Check deployment logs"
echo "3. Wait for deployment to complete"
echo "4. Test by creating a transaction at caisse"
echo "5. Scan participant QR code to verify fix"
echo ""
echo "See TEST_TRANSACTION_FIX.md for detailed testing instructions"
echo ""
