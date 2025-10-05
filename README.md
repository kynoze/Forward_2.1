# 🤖 Telegram File Forwarding Bot

A simple Telegram bot to **index messages/files from a source channel**, store them in a **database**, and **forward them to a target channel**.

---

## **Features**

- ✅ Index files/messages from any channel  
- ✅ Store files in a MongoDB database  
- ✅ Forward files to a set target channel  
- ✅ View total files stored  
- ✅ Clear database with confirmation  
- ✅ Owner-only access for sensitive commands  

---

## **Commands**

| Command | Description |
|---------|-------------|
| `/index` | Index files from a channel into the database |
| `/total` | Check total files stored |
| `/cleardb` | Clear all files from the database (with confirmation) |
| `/status` | Check bot’s current status |
| `/set_channel` | Set the target channel (required before forwarding) |
| `/forward` | Forward files from the database |

---

