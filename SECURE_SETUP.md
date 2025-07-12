# 🔐 Secure Telegram Setup Guide

This guide will help you set up secure Telegram integration using encrypted session files stored in GitHub secrets.

## 🎯 **How It Works**

1. **Create session file locally** (interactive login)
2. **Convert to base64** (for secure storage)
3. **Store in GitHub secrets** (encrypted)
4. **Recreate in GitHub Actions** (temporarily)
5. **Clean up after use** (no traces left)

## 🚀 **Step-by-Step Setup**

### **Step 1: Create Session File Locally**

1. **Set environment variables:**
   ```bash
   $env:API_ID="YOUR_API_ID_HERE"
   $env:API_HASH="YOUR_API_HASH_HERE"
   ```

2. **Run setup script:**
   ```bash
   python setup_session.py
   ```

3. **Enter your phone number** (with country code, e.g., +212XXXXXXXXX)

4. **Enter verification code** sent to your Telegram

5. **Verify success** - you should see "Session created successfully!"

### **Step 2: Convert Session to Base64**

1. **Run conversion script:**
   ```bash
   python convert_session.py
   ```

2. **Copy the base64 string** that appears

### **Step 3: Add GitHub Secrets**

1. Go to your repository: https://github.com/Gastordia/Leakwatch
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Add these secrets:

   **TELEGRAM_API_ID**
   - Value: `22225752`

   **TELEGRAM_API_HASH**
   - Value: `9b0977dddfd05ce874e0d4ec41001348`

   **TELEGRAM_SESSION_BASE64**
   - Value: (paste the base64 string from Step 2)

### **Step 4: Enable GitHub Actions**

1. Go to **Actions** tab in your repository
2. Click **"Fetch Telegram Channel"** workflow
3. Click **"Enable workflow"**

## 🔄 **How It Works in GitHub Actions**

1. **Every hour**, the workflow runs
2. **Creates session file** from base64 secret
3. **Connects to Telegram** using your session
4. **Fetches messages** from @breachdetector
5. **Filters Morocco-related** content
6. **Updates data.json** with new breaches
7. **Deletes session file** (cleanup)
8. **Commits changes** to repository

## 🛡️ **Security Features**

- ✅ **Session file never committed** to repository
- ✅ **Base64 stored encrypted** in GitHub secrets
- ✅ **Session file recreated** temporarily in Actions
- ✅ **Automatic cleanup** after each run
- ✅ **No sensitive data** in public repository

## 📊 **What You Get**

- **Hourly updates** from @breachdetector
- **Morocco-specific filtering**
- **Automatic data.json updates**
- **Live website** at https://gastordia.github.io/Leakwatch
- **All breach lookup tools** working

## 🔍 **Monitoring**

- **Actions tab**: Check workflow runs
- **data.json**: See latest breach data
- **Website**: View live updates

## 🚨 **Troubleshooting**

### **Session file not found**
- Run `python setup_session.py` first
- Make sure you completed the phone verification

### **Workflow fails**
- Check all 3 secrets are set correctly
- Verify the base64 string is complete
- Check Actions logs for specific errors

### **No messages found**
- Channel might be private or changed
- Check if @breachdetector still exists
- Verify Morocco keywords are working

## 🔄 **Updating Session**

If your session expires:
1. Delete the old session file
2. Run `python setup_session.py` again
3. Run `python convert_session.py` again
4. Update the `TELEGRAM_SESSION_BASE64` secret

---

**Your LeakWatch platform will now securely fetch from @breachdetector every hour!** 🎉 