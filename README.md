# Forward 2.1

A simple Telegram bot to **index files from a source channel**, store them in a **MongoDB database**, and **forward them to a target channel**.

---

## **What it does**

- ✅ Index files/videos from any public channel (no admin permission needed)  
- ✅ For private channels, the bot requires admin permission  
- ✅ Store files in a MongoDB database  
- ✅ Forward files to a set target channel  
- ✅ View total files stored  
- ✅ Clear database with confirmation  
- ✅ Owner-only access  
- ✅ Prevents duplicate file storage using unique file IDs  

---

## **Commands**

| Command        | Description                                           |
|----------------|-------------------------------------------------------|
| `/index`       | Index files from a channel into the database         |
| `/total`       | Check total files stored                              |
| `/cleardb`     | Clear all files from the database (with confirmation)|
| `/status`      | Check bot’s current status                            |
| `/set_channel` | Set the target channel (required before forwarding)  |
| `/forward`     | Forward files to target chat from the database       |

---

## **Environment Variables**

The bot requires the following environment variables:

```env
# Telegram API credentials
API_ID=123456           # Your Telegram API ID (integer)
API_HASH=your_api_hash  # Your Telegram API Hash
TG_BOT_TOKEN=bot_token_here  # Your Telegram Bot Token

# Owner IDs (space-separated)
OWNER_ID=12345678 98765432

# MongoDB connection URL
MONGO_URL=mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority

# Cache time in seconds (optional, default 300)
CACHE_TIME=300

# MongoDB collection name (optional, default "forward2025")
COLLECTION_NAME=forward2025
