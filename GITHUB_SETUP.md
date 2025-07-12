# 🚀 GitHub Integration Guide for LeakWatch

This guide will help you integrate your LeakWatch breach monitoring platform with GitHub for automatic deployment and data updates.

## 📋 Prerequisites

- GitHub account
- Git installed on your computer
- Python 3.8+ (for local testing)

## 🔧 Step-by-Step Setup

### 1. Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Name your repository: `leakwatch` (or your preferred name)
5. Make it **Public** (required for GitHub Pages)
6. **Don't** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

### 2. Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Run these in your terminal:

```bash
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/leakwatch.git

# Push your code to GitHub
git branch -M main
git push -u origin main
```

### 3. Set Up GitHub Pages

1. Go to your repository on GitHub
2. Click on "Settings" tab
3. Scroll down to "Pages" section (in the left sidebar)
4. Under "Source", select "Deploy from a branch"
5. Choose "main" branch and "/ (root)" folder
6. Click "Save"
7. Your site will be available at: `https://YOUR_USERNAME.github.io/leakwatch`

### 4. Configure Telegram API Secrets

For the automated data fetching to work, you need to set up Telegram API credentials:

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application:
   - App title: `LeakWatch`
   - Short name: `leakwatch`
   - Platform: `Desktop`
   - Description: `Breach monitoring platform`
5. Note down your `api_id` and `api_hash`

### 5. Add GitHub Secrets

1. In your GitHub repository, go to "Settings" → "Secrets and variables" → "Actions"
2. Click "New repository secret"
3. Add these secrets:
   - **Name**: `TELEGRAM_API_ID`
   - **Value**: Your Telegram API ID (number)
4. Click "Add secret"
5. Repeat for:
   - **Name**: `TELEGRAM_API_HASH`
   - **Value**: Your Telegram API Hash (string)

### 6. Enable GitHub Actions

1. Go to "Actions" tab in your repository
2. You should see the "Fetch Telegram Channel" workflow
3. Click on it and then "Enable workflow"
4. The workflow will run automatically every 3 hours

## 🔄 Workflow Overview

### Automated Data Fetching
- **Schedule**: Every 3 hours
- **Manual Trigger**: Available via GitHub Actions
- **Process**: 
  1. Fetches messages from @breachdetector channel
  2. Filters for Morocco-related breaches
  3. Updates `data.json` file
  4. Commits and pushes changes

### File Structure
```
leakwatch/
├── index.html          # Main website
├── data.json           # Breach data (auto-updated)
├── fetch.py            # Telegram fetching script
├── requirements.txt    # Python dependencies
├── .github/
│   └── workflows/
│       └── fetch-telegram.yml  # GitHub Actions workflow
├── README.md           # Project documentation
├── LOCAL_SETUP.md      # Local development guide
└── .gitignore          # Git ignore rules
```

## 🌐 Deployment

### GitHub Pages (Automatic)
- Your site is automatically deployed when you push to the main branch
- URL: `https://YOUR_USERNAME.github.io/leakwatch`
- Updates automatically when data.json is updated

### Custom Domain (Optional)
1. Buy a domain (e.g., from Namecheap, GoDaddy)
2. In repository Settings → Pages:
   - Enter your custom domain
   - Enable "Enforce HTTPS"
3. Add CNAME record in your domain provider:
   - Type: CNAME
   - Name: @ (or www)
   - Value: `YOUR_USERNAME.github.io`

## 🔍 Monitoring & Maintenance

### Check Workflow Status
1. Go to "Actions" tab in your repository
2. Click on "Fetch Telegram Channel"
3. View recent runs and their status

### Manual Data Update
1. Go to "Actions" tab
2. Click "Fetch Telegram Channel"
3. Click "Run workflow" → "Run workflow"

### Troubleshooting
- **Workflow fails**: Check if API secrets are correctly set
- **No data updates**: Verify @breachdetector channel is accessible
- **Site not updating**: Check GitHub Pages settings

## 📊 Features Available

### Website Features
- ✅ Latest Morocco-related breaches
- ✅ Email security check (XposedOrNot API)
- ✅ Domain search
- ✅ All breaches database
- ✅ Password security check
- ✅ Comprehensive security analysis

### Automation Features
- ✅ Automatic data fetching every 3 hours
- ✅ GitHub Pages deployment
- ✅ Manual workflow triggers
- ✅ Error handling and logging

## 🔐 Security Notes

- Telegram API credentials are stored as GitHub secrets (encrypted)
- No sensitive data is exposed in the client-side code
- All API calls are made directly from the browser
- Rate limiting is handled gracefully

## 📞 Support

If you encounter issues:
1. Check the Actions tab for workflow errors
2. Verify your API credentials
3. Ensure the repository is public for GitHub Pages
4. Check the browser console for client-side errors

## 🎉 Next Steps

After setup:
1. Test your website at the GitHub Pages URL
2. Try the email check feature
3. Monitor the Actions tab for successful data updates
4. Consider adding a custom domain
5. Share your breach monitoring platform!

---

**Your LeakWatch platform is now fully integrated with GitHub and will automatically stay updated with the latest breach information!** 🚀 