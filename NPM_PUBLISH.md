# NPM Publish Guide

Simple step-by-step guide to publish `ai-bangladesh-address-parser` to npm.

## Quick Publish

```bash
# 1. Login to npm
npm login

# 2. Build TypeScript
npm run build

# 3. Verify README.md is included
npm pack --dry-run | grep README.md

# 4. Publish
npm publish

# 5. Verify
npm view ai-bangladesh-address-parser version

# 6. Check package page (README should appear automatically)
# Visit: https://www.npmjs.com/package/ai-bangladesh-address-parser
```

## Troubleshooting: README.md Not Showing

If README.md doesn't appear on npm package page:

1. **Verify it's in the package:**
   ```bash
   npm pack --dry-run | grep README.md
   ```
   Should show: `npm notice 25.1kB README.md` ✅

2. **Check package.json files array:**
   Make sure `README.md` is in the `files` array (it is ✅)

3. **Wait a few minutes:**
   npm sometimes takes 2-5 minutes to update the package page

4. **Clear browser cache:**
   Hard refresh the npm package page (Ctrl+Shift+R or Cmd+Shift+R)

5. **Republish if needed:**
   ```bash
   npm version patch  # Bump version
   npm publish
   ```

6. **Check directly:**
   Visit: `https://www.npmjs.com/package/ai-bangladesh-address-parser`
   The README should appear automatically at the top of the page

**Note:** npm automatically displays README.md from the package root. It's already configured correctly in `package.json`.

---

## Detailed Steps

### Step 1: Login to npm

```bash
npm login
```

You'll be prompted for:
- **Username**: Your npm username
- **Password**: Your npm password (hidden)
- **Email**: Your npm email
- **OTP**: One-time password (if 2FA enabled)

**Verify login:**
```bash
npm whoami
```
Should show your username.

### Step 2: Build

```bash
npm run build
```

This compiles TypeScript from `api/node/` to `dist/`.

**Verify build:**
```bash
test -f dist/index.js && echo "✓ Build successful" || echo "✗ Build failed"
```

### Step 3: Test Package (Optional)

```bash
# Test import
node -e "const { AddressExtractor } = require('./dist/index.js'); console.log('✓ Import successful')"

# Check package contents
npm pack --dry-run
```

### Step 4: Publish

```bash
npm publish
```

The `prepublishOnly` script automatically runs `npm run build` before publishing.

### Step 5: Verify Publication

```bash
# Check published version
npm view ai-bangladesh-address-parser version

# View full package info
npm view ai-bangladesh-address-parser
```

## Update Version

Before publishing, update version in `package.json`:

```bash
# Patch version (1.0.2 → 1.0.3)
npm version patch

# Minor version (1.0.2 → 1.1.0)
npm version minor

# Major version (1.0.2 → 2.0.0)
npm version major
```

Or manually edit `package.json`:
```json
{
  "version": "1.0.3"
}
```

## Troubleshooting

### Error: "401 Unauthorized"
**Solution:** You're not logged in. Run `npm login`.

### Error: "404 Not Found"
**Solution:** 
1. Make sure you're logged in: `npm whoami`
2. Check you own the package: `npm owner ls ai-bangladesh-address-parser`
3. If not owner, you need to be added by current owner

### Error: "Build failed"
**Solution:**
```bash
# Install dependencies
npm install

# Try building again
npm run build
```

### Error: "Version already exists"
**Solution:** Update version number in `package.json` to a higher version.

## Package Contents

The published package includes:
- `dist/` - Compiled TypeScript (main entry)
- `src/` - Python source code
- `api/` - API files
- `tools/` - Utility scripts
- `data/` - Geographic data
- `models/` - ML models (production)
- `config/` - Configuration files
- `requirements.txt` - Python dependencies
- `README.md` - Documentation
- `LICENSE` - License file

## After Publishing

Your package will be available at:
- **NPM**: https://www.npmjs.com/package/ai-bangladesh-address-parser
- **Install**: `npm install ai-bangladesh-address-parser`

## One-Liner

```bash
npm login && npm run build && npm publish && npm view ai-bangladesh-address-parser version
```
