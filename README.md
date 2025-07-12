# 🚨 Morocco Breach Watch

A comprehensive data breach monitoring and lookup tool specifically designed to track Morocco-related data breaches from the @breachdetector Telegram channel, with additional breach lookup capabilities powered by the XposedOrNot API.

## 🌟 Features

### 📊 Morocco Breach Monitoring
- **Real-time Monitoring**: Automatically fetches and displays Morocco-related breaches from @breachdetector
- **Smart Filtering**: Uses comprehensive Morocco keywords to identify relevant breaches
- **Search & Filter**: Search through breaches and filter by date, relevance, and type
- **Statistics Dashboard**: Real-time statistics showing total breaches, Morocco-related breaches, and recent activity

### 🔍 Comprehensive Breach Lookup Tools
Powered by the XposedOrNot API, the app provides multiple breach checking capabilities:

#### 📧 Email Breach Check
- Check if your email address has been exposed in data breaches
- Real-time risk assessment with detailed breach information
- Shows breach count, dates, and affected services

#### 🌐 Domain Search
- Search for breaches related to specific domains
- Get detailed information about domain-specific data exposures
- Risk assessment based on breach severity and frequency

#### 📊 Breach Analytics
- Detailed analytics for email addresses
- Risk scoring and password strength analysis
- Industry-wise breach distribution
- Yearly breach trends and patterns

#### 📋 All Known Breaches
- Browse the complete database of known data breaches
- Search and filter through thousands of breach records
- Detailed information about each breach including:
  - Breach date and description
  - Number of exposed records
  - Types of data exposed
  - Password risk assessment
  - Industry classification

#### 🔐 Password Security Check
- **Anonymous Password Checking**: Check if a password has been exposed without revealing the actual password
- **SHA3-Keccak-512 Hashing**: Uses secure hashing for privacy protection
- **Password Strength Analysis**: Provides character breakdown and exposure count
- **Security Recommendations**: Offers actionable advice for compromised passwords

### 🛡️ Security Features
- **Rate Limit Handling**: Proper error handling for API rate limits with user-friendly messages
- **Privacy Protection**: Password checking uses anonymous hashing
- **No Data Storage**: All checks are performed in real-time without storing sensitive data
- **Secure API Integration**: Direct integration with XposedOrNot API

## 🚀 Quick Start

### Option 1: Deploy to GitHub Pages (Recommended)

For complete setup with automatic data updates, follow the [GitHub Integration Guide](GITHUB_SETUP.md).

**Quick Setup:**
1. **Fork this repository** to your GitHub account
2. **Set up GitHub Actions** (optional for automatic data updates):
   - Go to Settings → Secrets and variables → Actions
   - Add your Telegram API credentials:
     - `TELEGRAM_API_ID`: Your Telegram API ID
     - `TELEGRAM_API_HASH`: Your Telegram API Hash
3. **Enable GitHub Pages**:
   - Go to Settings → Pages
   - Set source to "Deploy from a branch"
   - Select "main" branch and "/ (root)" folder
4. **Access your app** at `https://yourusername.github.io/leakwatch`

### Option 2: Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/leakwatch.git
   cd leakwatch
   ```

2. **Set up Python environment** (for data fetching):
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Telegram API** (optional):
   - Get your API credentials from https://my.telegram.org
   - Update the credentials in `fetch.py`

4. **Run the data fetcher** (optional):
   ```bash
   python fetch.py
   ```

5. **Start a local server** (IMPORTANT - required to avoid CORS errors):
   ```bash
   # Using Python (recommended)
   python -m http.server 8000
   
   # Using Node.js
   npx serve .
   
   # Using PHP
   php -S localhost:8000
   ```

6. **Open your browser** and navigate to `http://localhost:8000`

**⚠️ Important**: Don't open `index.html` directly in the browser. You must use a local server to avoid CORS errors. See `LOCAL_SETUP.md` for detailed instructions.

## 📁 Project Structure

```
leakwatch/
├── index.html                    # Main application file
├── data.json                     # Breach data (auto-generated)
├── fetch_secure_session_improved.py  # Enhanced Telegram fetcher
├── fetch_entire_history.py       # Full history fetch (one-time)
├── requirements_improved.txt     # Python dependencies
├── .github/
│   └── workflows/
│       ├── fetch-data-improved.yml    # Regular data updates
│       └── full-history-fetch.yml     # Full history fetch
├── test.html                     # Testing utility
└── README.md                     # This file
```

## 🔧 Configuration

### Telegram API Setup (Optional)

If you want to automatically fetch data from @breachdetector:

1. **Get Telegram API credentials**:
   - Visit https://my.telegram.org
   - Log in with your phone number
   - Create a new application
   - Note down the API ID and API Hash

2. **Set up environment variables**:
   ```bash
   export TELEGRAM_API_ID="your_api_id"
   export TELEGRAM_API_HASH="your_api_hash"
   export TELEGRAM_PHONE="your_phone_number"
   ```

3. **Run the fetcher**:
   ```bash
   python fetch.py
   ```

### GitHub Actions Setup

For automatic data updates every 3 hours:

1. **Add secrets to your repository**:
   - Go to Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `API_ID`: Your Telegram API ID
     - `API_HASH`: Your Telegram API Hash
     - `TELEGRAM_SESSION_BASE64`: Your session file (base64 encoded)

2. **The regular workflow will automatically**:
   - Run every 3 hours
   - Fetch new messages from @breachdetector
   - Update `data.json` with new breaches
   - Commit and push changes

### Full History Fetch (One-Time)

For comprehensive historical data:

1. **Go to Actions tab** in your repository
2. **Click "Full History Fetch (One-Time)"**
3. **Click "Run workflow"**
4. **Type "YES"** in the confirmation field
5. **Click "Run workflow"**

**This will**:
- Fetch ALL messages from @breachdetector
- Filter for JSON messages only
- Apply relevance filters
- Create comprehensive dataset
- Generate detailed summary report

## 🧪 Testing

Use the included `test.html` file to verify all functionality:

1. **Open `test.html`** in your browser
2. **Run the tests** to verify:
   - API connectivity
   - Local data loading
   - Password hashing functionality
   - All breach lookup tools

## 📊 API Rate Limits

The XposedOrNot API has the following rate limits:
- **1 request per second** per endpoint
- **Rate limit errors** are handled gracefully with user-friendly messages
- **Automatic retry suggestions** with wait times

## 🛠️ Troubleshooting

### Common Issues

1. **"Rate limit exceeded" errors**:
   - Wait a few minutes before trying again
   - The app shows the exact wait time in the error message

2. **"No breaches found" for All Breaches**:
   - This usually indicates a rate limit or API issue
   - Try again after a few minutes
   - Check the test page to verify API connectivity

3. **Local data not loading**:
   - Ensure `data.json` exists in the root directory
   - Check file permissions
   - Verify the JSON format is valid

4. **Password checking not working**:
   - Ensure you're using a modern browser with Web Crypto API support
   - Check the test page to verify hashing functionality

### Debug Mode

Enable debug logging by opening the browser console (F12) and looking for:
- API request/response logs
- Error messages
- Data loading status

## 🔒 Privacy & Security

- **No data storage**: All checks are performed in real-time
- **Anonymous password checking**: Passwords are hashed before checking
- **No API keys exposed**: All API calls are made client-side
- **Rate limiting**: Built-in protection against API abuse

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **@breachdetector** for providing breach data
- **XposedOrNot** for the comprehensive breach lookup API
- **Telethon** for Telegram API integration
- **GitHub Actions** for automated data fetching

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Run the test page to verify functionality
3. Open an issue on GitHub with detailed information

---

**⚠️ Disclaimer**: This tool is for educational and security awareness purposes only. Always use responsibly and in accordance with applicable laws and regulations. 