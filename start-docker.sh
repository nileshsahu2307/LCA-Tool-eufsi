#!/bin/bash

echo "========================================"
echo " EUFSI LCA Tool - Docker Setup"
echo "========================================"
echo ""
echo "Starting all services (MongoDB, Backend, Frontend)..."
echo "This may take a few minutes on first run."
echo ""
echo "Frontend will be available at: http://localhost:3000"
echo "Backend API will be available at: http://localhost:8000"
echo "API Docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

docker-compose up
