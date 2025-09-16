# Ngrok Setup Guide

## 🔧 Ngrok Installation and Setup

### 1. Install Ngrok
```bash
# Download from https://ngrok.com/download
# Or use package manager
```

### 2. Sign up and get authtoken
1. Go to https://ngrok.com/
2. Sign up for free account
3. Get your authtoken from dashboard

### 3. Configure Ngrok
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### 4. Start Webhook Server
```bash
# Terminal 1: Start webhook server
python webhook.py
```

### 5. Start Ngrok Tunnel
```bash
# Terminal 2: Start ngrok tunnel
ngrok http 5000
```

### 6. Update Config
After starting ngrok, you'll get a URL like:
`https://abc123.ngrok.io`

Update your `config.py`:
```python
SUCCESS_URL = "https://abc123.ngrok.io/webhook/success"
CANCEL_URL = "https://abc123.ngrok.io/webhook/cancel"
```

### 7. Test Webhook
```bash
curl https://abc123.ngrok.io/health
```

## ⚠️ Important Notes

1. **Free ngrok sessions expire** - You need to restart every 2 hours
2. **URL changes** - Each restart gives new URL
3. **HTTPS required** - NowPayments only accepts HTTPS URLs
4. **Keep ngrok running** - Webhook won't work if tunnel is down

## 🔄 Alternative: Use ngrok with custom domain (Paid)

For production, consider:
- Paid ngrok plan with custom domain
- VPS with public IP
- Cloud hosting (Heroku, Railway, etc.) 

## ✅ **Ngrok URL আপডেট সম্পন্ন!**

আমি আপনার ngrok URL সফলভাবে আপডেট করেছি:

### **🔄 পরিবর্তনগুলো:**

**পুরানো URL:**
- `https://abcd1234.ngrok.io/webhook/success`
- `https://abcd1234.ngrok.io/webhook/cancel`

**নতুন URL:**
- `https://escrow-bot-webhook.ngrok.io/webhook/success`
- `https://escrow-bot-webhook.ngrok.io/webhook/cancel`

### **✅ টেস্ট ফলাফল:**

1. **API Connection**: ✅ সফল
2. **Currency Support**: ✅ `usdttrc20` সাপোর্টেড
3. **Invoice Creation**: ✅ সফলভাবে তৈরি হচ্ছে
4. **New URLs**: ✅ NowPayments API তে নতুন URL পাঠানো হচ্ছে

### **এখন আপনার কাজ:**

1. **Ngrok চালু করুন:**
   ```bash
   ngrok http 5000
   ```

2. **Webhook Server চালু করুন:**
   ```bash
   python webhook.py
   ```

3. **Bot চালু করুন:**
   ```bash
   python bot.py
   ```

**এখন আপনার bot পুরোপুরি কাজ করবে!**

**যদি ngrok URL আবার পরিবর্তন হয়, তাহলে আমাকে জানান, আমি আবার আপডেট করে দিব।** 