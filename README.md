#  Forward 2.1

A simple Telegram bot to **index messages/files from a source channel**, store them in a **database**, and **forward them to a target channel**.

---
## ⚠️ **Important Warning**

> ⚠️ **This bot indexes slowly!**  
> It saves approximately **5 files per second** into the database.  
> This is **intentional** — the bot checks **every file for duplicates** before saving to MongoDB to prevent storing the same file multiple times.  

> 💬 Note: This is an open-source project made for learning and automation.
> ***⚡ Your Choice — this repo may feel slow for you (due to duplicate checks), so use it only if accuracy matters to you!***
---
## **What it does**

- ✅ Index files/videos from any public channel ***without admin permission***, in private channel bot need admin permission. 
- ✅ Store files in a MongoDB database  
- ✅ Forward files to a set target channel  
- ✅ View total files stored  
- ✅ Clear database with confirmation  
- ✅ Owner-only access
- ✅ Bot Index message from channel and saves to database, further forwards and deletes each messages from database.Use of database was to Remove duplicacy of files.

---

## **Commands**

| Command | Description |
|---------|-------------|
| `/index` | Index files from a channel into the database |
| `/total` | Check total files stored |
| `/cleardb` | Clear all files from the database (with confirmation) |
| `/status` | Check bot’s current status |
| `/set_channel` | Set the target channel (required before forwarding) |
| `/forward` | Forward files to target chat from the database |

---

## **Environment Variables**

The bot requires the following environment variables.

```env
# Telegram API credentials
API_ID=123456             # Your Telegram API ID (integer)
API_HASH=your_api_hash     # Your Telegram API Hash
TG_BOT_TOKEN=bot_token_here # Your Telegram Bot Token

# Owner IDs (space-separated)
OWNER_ID=12345678 98765432

# MongoDB connection URL
MONGO_URL=mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority

# Cache time in seconds (optional, default 300)
CACHE_TIME=300

# MongoDB collection name (optional, default "forward2025")
COLLECTION_NAME=forward2025
```
