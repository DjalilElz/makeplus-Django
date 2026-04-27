#!/bin/bash
# Test debug endpoint for djalil azizi

echo "Testing debug endpoint for djalil azizi..."
echo ""

# You need to replace YOUR_TOKEN with an actual controller token
# Get token by logging in as a controller

curl -X POST https://makeplus-platform.onrender.com/api/events/rooms/debug-transactions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "email": "abdeldjalil.elazizi@ensia.edu.dz"
  }' | python -m json.tool

echo ""
echo "Done!"
