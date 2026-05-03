#!/bin/bash

# Test script - Run this from your local machine
# Replace with your actual server IPs

SERVER1="http://127.0.0.1:5001"
SERVER2="http://127.0.0.1:5002"
SERVER3="http://127.0.0.1:5003"

echo "========================================"
echo "1. Checking initial state on all servers"
echo "========================================"
curl $SERVER1/check/T101
echo ""
curl $SERVER2/check/T101
echo ""
curl $SERVER3/check/T101
echo ""

echo "========================================"
echo "2. Booking 2 seats on Train T101"
echo "========================================"
curl -X POST $SERVER1/book \
  -H "Content-Type: application/json" \
  -d '{"train_id":"T101","seats":2,"passenger":"Rahul Kumar"}'
echo ""

sleep 2

echo "========================================"
echo "3. Checking after booking (all servers)"
echo "========================================"
curl $SERVER1/check/T101
echo ""
curl $SERVER2/check/T101
echo ""
curl $SERVER3/check/T101
echo ""

echo "========================================"
echo "4. View all bookings"
echo "========================================"
curl $SERVER1/bookings
echo "" 
