# 🔒 Enable 2FA to Publish npm Package

## ⚠️ Current Error

```
npm error 403 Forbidden - Two-factor authentication required to publish packages.
```

**Package is ready!** (14.8 MB, 58 files) - Just needs 2FA enabled.

---

## ⚡ Quick Fix (2 minutes)

### Step 1: Go to npm Settings

**Open this URL in your browser:**
```
https://www.npmjs.com/settings/[YOUR_NPM_USERNAME]/auth-and-security
```

**Replace `[YOUR_NPM_USERNAME]` with your actual npm username**

Or manually:
1. Go to https://www.npmjs.com
2. Click your profile icon (top right)
3. Click "Settings"
4. Click "Auth & Security" (left sidebar)

### Step 2: Enable 2FA

1. Find **"Two-Factor Authentication"** section
2. Click **"Enable 2FA"** button
3. Choose method:
   - **📱 Authenticator App** (Recommended)
   - **📱 SMS** (Alternative)

### Step 3: Setup Authenticator App

**If you don't have an authenticator app, install one:**
- **Google Authenticator** (iOS/Android)
- **Authy** (iOS/Android/Desktop)
- **Microsoft Authenticator** (iOS/Android)

**Then:**
1. Open authenticator app
2. Tap "+" or "Add Account"
3. Scan the QR code from npm website
4. Enter the 6-digit code to verify

### Step 4: Save Backup Codes

- npm will show backup codes
- **Copy and save them!**
- These are your backup if you lose your phone

### Step 5: Publish Again

```bash
npm publish --access public
```

When prompted, enter the 6-digit code from your authenticator app.

---

## ✅ Verify 2FA is Enabled

```bash
npm profile get
```

Look for `two-factor: enabled` in the output.

---

## 🎯 What Happens When Publishing

After 2FA is enabled:

1. Run: `npm publish --access public`
2. npm checks: "2FA enabled? ✅"
3. npm prompts: `Enter one-time password:`
4. You: Open authenticator app → Enter 6-digit code
5. Package publishes! ✅

---

## 📱 Getting the Code

The code changes every 30 seconds. Just:
1. Open your authenticator app
2. Find "npm" or "npmjs"
3. Copy the current 6-digit code
4. Paste when npm asks

---

## 🆘 Alternative: Access Token

If you don't want to use 2FA:

1. **Create token:** https://www.npmjs.com/settings/[USERNAME]/tokens
2. **Generate** "Automation" type token
3. **Login:** 
   ```bash
   npm login --auth-type=legacy
   # Password = your access token
   ```
4. **Publish:** `npm publish --access public`

---

## ✅ Your Package is Ready!

- ✅ Package name: `ai-bangladesh-address-parser`
- ✅ Size: 14.8 MB (within limits)
- ✅ Files: 58 files
- ✅ License: Updated with your name
- ✅ Ready to publish!

**Just enable 2FA and publish!** 🚀

---

**Follow the steps above to enable 2FA and publish your package!** 🔒
