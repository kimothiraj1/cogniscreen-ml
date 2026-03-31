#!/bin/bash
# Test your Docker image locally before pushing to AWS
# Run from project root

echo "Building image..."
docker build -t cogniscreen-ml .

echo ""
echo "Starting container..."
docker run -d \
  --name cogniscreen_ml_test \
  -p 8000:8000 \
  --env-file .env \
  cogniscreen-ml

echo ""
echo "Waiting for server to start..."
sleep 3

# Test health endpoint
echo "Testing health endpoint..."
ML_KEY=$(grep ML_API_KEY .env | cut -d '=' -f2)
RESPONSE=$(curl -s http://localhost:8000/health -H "X-ML-API-Key: ${ML_KEY}")
echo "Response: $RESPONSE"

echo ""
echo "Test a score endpoint..."
curl -s -X POST http://localhost:8000/score/game \
  -H "X-ML-API-Key: ${ML_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test123",
    "testType": "memory_mosaic",
    "score": 0.6,
    "timeTaken": 55000,
    "errors": 2,
    "hesitationGaps": [400, 1800, 600, 2900],
    "age": 70
  }' | python3 -m json.tool

echo ""
echo "Stopping test container..."
docker stop cogniscreen_ml_test
docker rm cogniscreen_ml_test
echo "Done. If responses look correct, you are ready to push to AWS."
