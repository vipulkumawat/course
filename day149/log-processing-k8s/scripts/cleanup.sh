#!/bin/bash

echo "🧹 Cleaning up..."

kubectl delete namespace log-processing --ignore-not-found=true

echo "✅ Cleanup complete"
