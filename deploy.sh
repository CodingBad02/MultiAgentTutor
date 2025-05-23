#!/bin/bash

echo "🚀 Preparing deployment to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "⚠️ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Ensure we have all requirements
echo "📦 Checking dependencies..."
pip install -r requirements.txt

# Create .vercel directory if it doesn't exist
mkdir -p .vercel

echo "🔑 Reminder: Make sure you've added your GEMINI_API_KEY to Vercel environment variables!"
echo "   You can do this in the Vercel dashboard after your first deployment."

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment complete!"
echo "Visit your Vercel dashboard to configure environment variables if needed."
