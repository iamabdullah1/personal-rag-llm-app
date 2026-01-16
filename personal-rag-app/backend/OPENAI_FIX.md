# ⚠️ OpenAI Quota Error Fix

## The Problem

You're getting this error:
```
openai.RateLimitError: Error code: 429 - insufficient_quota
```

## Why This Happens

OpenAI requires you to **add a payment method** even to use free $5 credits. New accounts without a payment method can't make API calls.

## ✅ Solution

### Step 1: Add Payment Method to OpenAI

1. Go to: https://platform.openai.com/account/billing/overview
2. Click **"Add payment method"**
3. Add a credit/debit card
4. **Don't worry**: You won't be charged until you use the $5 free credits

### Step 2: Verify Free Credits

1. Check: https://platform.openai.com/account/usage
2. You should see **$5.00 in free credits**
3. Valid for 3 months

### Step 3: Update Your API Key (if needed)

Your `.env` file should look like:
```env
OPENAI_API_KEY=sk-proj-YOUR-ACTUAL-KEY-HERE
```

Get your key from: https://platform.openai.com/api-keys

### Step 4: Run Ingestion Again

```bash
cd /Users/apple/Desktop/My\ LLM && source .venv/bin/activate
cd personal-rag-app/backend
python scripts/ingest_documents.py --data-dir ./data/personal --target chroma
```

## 💰 Costs

With $5 free credits, you can:
- Embed your documents: ~$0.01
- Test 2,500+ questions: ~$4.99
- Build your entire portfolio project: ~$1-2

**You'll have plenty left over!**

## 🆓 Alternative: Completely Free Option

If you don't want to add a payment method, you need Python 3.11 or 3.12 (not 3.13) to use free local embeddings.

To downgrade Python:
1. Install Python 3.12: https://www.python.org/downloads/
2. Recreate virtual environment with Python 3.12
3. Use HuggingFace embeddings (100% free)

**But honestly**: Just add the payment method. It takes 2 minutes and the $5 free credits are more than enough!

## 📧 Still Having Issues?

Check:
1. API key is correct in `.env`
2. Payment method added to OpenAI account
3. No typos in the API key
4. Using the correct OpenAI account

---

**Bottom line**: Add a payment method to OpenAI → Get $5 free credits → Build your project! 🚀
