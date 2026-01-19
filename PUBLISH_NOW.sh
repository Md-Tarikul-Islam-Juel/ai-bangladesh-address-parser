#!/bin/bash
# Quick publish script for ai-bangladesh-address-parser

echo "================================================================================
📦 NPM PUBLISH SCRIPT
================================================================================
"

# Check if logged in
echo "1. Checking npm login status..."
if npm whoami > /dev/null 2>&1; then
    echo "   ✓ Already logged in as: $(npm whoami)"
else
    echo "   ✗ Not logged in. Please login first:"
    echo "     npm login"
    exit 1
fi

# Build
echo ""
echo "2. Building TypeScript..."
npm run build
if [ $? -ne 0 ]; then
    echo "   ✗ Build failed!"
    exit 1
fi
echo "   ✓ Build successful"

# Verify package
echo ""
echo "3. Verifying package..."
if [ ! -f "dist/index.js" ]; then
    echo "   ✗ dist/index.js not found!"
    exit 1
fi
echo "   ✓ Package ready"

# Show what will be published
echo ""
echo "4. Package conte"
npm pack --dry-run 2>&1 | grep -E "(package size|total files)" | head -2

# Confirm
echo ""
read -p "5. Publish version $(node -p "require('./package.json').version") to npm? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "   Cancelled."
    exit 0
fi

# Publish
echo ""
echo "6. Publishing to npm..."
npm publish

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================================================
   ✓ SUCCESS! Published to npm
================================================================================
"
    echo "Package: https://www.npmjs.com/package/ai-bangladesh-address-parser"
    echo "Version: $(node -p "require('./package.json').version")"
    echo ""
    echo "Verify with: npm view ai-bangladesh-address-parser version"
else
    echo ""
    echo "================================================================================
   ✗ PUBLISH FAILED
============================================================================
"
    exit 1
fi
