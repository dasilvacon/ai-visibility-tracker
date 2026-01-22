# Streamlit Dashboard Deployment Guide

## 🚀 Overview

Your Streamlit dashboard provides an interactive web interface for clients to explore their AI visibility analysis. It includes:

- **📊 Overview**: Key metrics, competitive landscape, top priorities
- **🎯 Sources & Citations**: Interactive PR target list with opportunity matrix
- **✅ Action Plan**: Task management with filters and checkboxes
- **🏆 Competitor Analysis**: Detailed competitive positioning with charts

---

## 🎨 Features

### Interactive Components
- Multi-page navigation with sidebar
- Filters and sorting for all data views
- Interactive charts (Plotly)
- Downloadable CSV/PDF exports
- Task management checkboxes
- Opportunity matrix visualization

### DaSilva Branding
- Branded color scheme (Deep Plum, Dusty Rose, Accent Pink)
- Professional styling
- Consistent fonts and layouts

---

## 🏃 Quick Start (Local Testing)

### 1. Install Dependencies

```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker

# Install Streamlit requirements
pip install -r requirements_streamlit.txt
```

### 2. Run Locally

```bash
streamlit run streamlit_app.py
```

The dashboard will open at `http://localhost:8501`

### 3. Test with Your Data

Make sure you have generated reports first:
```bash
python main.py --analyze --brand-config data/natasha_denona_brand_config_no_web.json
```

---

## ☁️ Deploy to Streamlit Cloud (FREE)

### Option 1: Direct Deployment (Easiest)

1. **Create GitHub Repository**
   ```bash
   cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ai-visibility-tracker.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your GitHub repo
   - Main file path: `streamlit_app.py`
   - Click "Deploy"

3. **Add Data Files**
   - Upload your `data/reports` folder to GitHub
   - Or use Streamlit secrets for dynamic data loading

### Option 2: With Authentication (Recommended for Clients)

#### Step 1: Add Authentication

Create `streamlit_auth_app.py`:

```python
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Load config
with open('config_auth.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Login widget
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{name}*')

    # Load your main dashboard
    exec(open('streamlit_app.py').read())

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
```

#### Step 2: Create Auth Config

Create `config_auth.yaml`:

```yaml
credentials:
  usernames:
    client1:
      email: client@example.com
      name: Client Name
      password: $2b$12$... # hashed password

    # Add more clients as needed

cookie:
  expiry_days: 30
  key: some_random_key_change_this
  name: ai_visibility_cookie
```

Generate hashed passwords:

```python
import streamlit_authenticator as stauth

# Generate hashed password
hashed_password = stauth.Hasher(['your_password']).generate()[0]
print(hashed_password)
```

#### Step 3: Deploy with Authentication

- Use `streamlit_auth_app.py` as your main file
- Add `config_auth.yaml` to `.gitignore`
- Store credentials in Streamlit secrets instead

### Option 3: Multi-Client Dashboard

For multiple clients, modify the sidebar:

```python
# In streamlit_app.py, replace brand selector with:

if st.session_state.get('authenticated'):
    # Show only their brand
    allowed_brands = st.session_state.get('allowed_brands', [])
    selected_brand = st.selectbox("Select Brand", allowed_brands)
```

---

## 🔐 Security & Access Control

### Option 1: Password Protection (Basic)

Add to Streamlit Cloud settings:
- Settings → Secrets
- Add password requirement

### Option 2: OAuth (Google, GitHub)

```python
# Use streamlit-oauth
pip install streamlit-oauth

import streamlit_oauth as oauth

# Configure OAuth
auth = oauth.OAuth2(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    redirect_uri="YOUR_REDIRECT_URI"
)
```

### Option 3: Custom Authentication

Use `streamlit-authenticator` (shown above) with:
- Individual client logins
- Session management
- Logout functionality

---

## 📊 Loading Client-Specific Data

### Method 1: File-Based (Current)

Dashboard reads from `data/reports/*.csv` files.

### Method 2: Database

```python
import sqlite3

@st.cache_resource
def get_database_connection():
    return sqlite3.connect('reports.db')

@st.cache_data
def load_brand_data(brand_name):
    conn = get_database_connection()
    return pd.read_sql(f"SELECT * FROM reports WHERE brand='{brand_name}'", conn)
```

### Method 3: API

```python
import requests

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_brand_data(brand_name):
    response = requests.get(f"https://api.yoursite.com/reports/{brand_name}")
    return response.json()
```

---

## 🎨 Customization

### Update Branding

In `streamlit_app.py`, change colors:

```python
# Your brand colors
DEEP_PLUM = '#YOUR_COLOR'
DUSTY_ROSE = '#YOUR_COLOR'
ACCENT_PINK = '#YOUR_COLOR'
```

### Add Logo

```python
st.sidebar.image("logo.png", width=200)
```

### Custom Domain

In Streamlit Cloud:
- Settings → General → Custom domain
- Add CNAME record: `dashboard.yoursite.com`

---

## 📧 Email Reports from Dashboard

Add email functionality:

```python
import smtplib
from email.mime.text import MIMEText

def send_report_email(client_email, report_data):
    msg = MIMEText(f"Your report is ready: {report_data}")
    msg['Subject'] = 'AI Visibility Report'
    msg['From'] = 'reports@yourcompany.com'
    msg['To'] = client_email

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your_email', 'your_password')
        server.send_message(msg)

# In dashboard
if st.button("📧 Email Report"):
    send_report_email(client_email, report_url)
    st.success("Report sent!")
```

---

## 🔄 Auto-Refresh Reports

### Option 1: Manual Refresh

Add refresh button:

```python
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
```

### Option 2: Scheduled Updates

Use GitHub Actions:

Create `.github/workflows/update_reports.yml`:

```yaml
name: Update Reports

on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly on 1st

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run analysis
        run: |
          python main.py --analyze --brand-config data/brand_config.json
      - name: Commit reports
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/reports/
          git commit -m "Update reports"
          git push
```

---

## 📱 Mobile Responsive

The dashboard is automatically mobile-responsive. Test with:

```bash
streamlit run streamlit_app.py --server.enableCORS false
```

Then open on mobile browser.

---

## 🐛 Troubleshooting

### Issue: "No reports found"

**Solution**: Ensure `data/reports/` directory exists with CSV files

```bash
python main.py --analyze --brand-config data/brand_config.json
```

### Issue: Import errors

**Solution**: Install all dependencies

```bash
pip install -r requirements_streamlit.txt
```

### Issue: Charts not displaying

**Solution**: Update Plotly

```bash
pip install --upgrade plotly
```

### Issue: Slow loading

**Solution**: Use caching

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    return pd.read_csv('data.csv')
```

---

## 🚀 Production Checklist

Before deploying to clients:

- [ ] Test all pages load correctly
- [ ] Verify all charts render
- [ ] Test download buttons
- [ ] Add authentication
- [ ] Set up custom domain
- [ ] Configure secrets (API keys, passwords)
- [ ] Test on mobile
- [ ] Add error handling
- [ ] Set up monitoring
- [ ] Create user documentation

---

## 📈 Advanced Features (Optional)

### Add Historical Tracking

```python
# Track changes over time
historical_data = load_historical_reports(brand_name)

fig = px.line(historical_data, x='date', y='visibility_rate',
             title="Visibility Trend Over Time")
st.plotly_chart(fig)
```

### Add Comparison Tool

```python
# Compare multiple time periods
period1 = st.date_input("Period 1")
period2 = st.date_input("Period 2")

comparison = compare_periods(brand_name, period1, period2)
st.dataframe(comparison)
```

### Add Notifications

```python
# Send alerts for significant changes
if visibility_rate_change > 5:
    st.warning(f"⚠️ Visibility increased by {visibility_rate_change}%!")
    send_slack_notification(brand_name, visibility_rate_change)
```

---

## 💡 Best Practices

1. **Cache Everything**: Use `@st.cache_data` for all data loading
2. **Mobile First**: Test on mobile devices
3. **Error Handling**: Add try/except blocks
4. **Loading States**: Use `st.spinner()` for long operations
5. **User Feedback**: Add success/error messages
6. **Documentation**: Include tooltips and help text
7. **Performance**: Limit data size, paginate tables
8. **Security**: Never expose API keys in code

---

## 📞 Support

- Streamlit Docs: https://docs.streamlit.io
- Streamlit Community: https://discuss.streamlit.io
- Deployment Help: https://docs.streamlit.io/streamlit-community-cloud

---

## 🎉 You're Ready!

Your Streamlit dashboard is production-ready. Deploy it and share with clients!

**Live URL**: `https://your-app.streamlit.app`
**Custom Domain**: `https://dashboard.yoursite.com`

Enjoy! 🚀
