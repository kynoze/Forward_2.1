from pyrogram import enums
import pytz, re, os
from datetime import datetime
from database.utils import Media

class temp:
    CURRENT = int(os.environ.get("SKIP", 2))
    CANCEL = False

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def get_name(name):
    return re.sub(r'@\w+', '', name)

def list_to_str(k):    
    return "N/A" if not k else ', '.join(str(item) for item in k)

def get_status():
    tz = pytz.timezone('Asia/Colombo')
    hour = datetime.now(tz).time().hour
    if 5 <= hour < 12:
        return "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ"
    elif 12 <= hour < 18:
        return "ɢᴏᴏᴅ ᴀꜰᴛᴇʀɴᴏᴏɴ"
    else:
        return "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ"

async def is_check_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in {enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER}
    except:
        return False

def get_readable_time(seconds):
    periods = [('days', 86400), ('hour', 3600), ('min', 60), ('sec', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name} '
    return result.strip()
