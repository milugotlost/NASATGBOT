# -*- coding: utf-8 -*-
# 這個聲明確保 Python 解釋器以 UTF-8 編碼讀取本文件。
# 這對於處理中文字符和特殊符號至關重要，可避免 SyntaxError。

import asyncio
import logging
import os
import datetime
import random
import json
import re  # 導入正則表達式庫

from aiohttp import web, ClientSession  # 用於異步 HTTP 請求
from aiohttp.client_exceptions import ClientResponseError  # 處理 HTTP 響應錯誤
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # 用於排程定時任務
from deep_translator import GoogleTranslator, exceptions  # 用於文本翻譯
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton  # Telegram Bot API 相關類
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode  # 用於指定訊息的解析模式
from telegram.error import TelegramError  # Telegram API 相關錯誤處理

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 從環境變數中獲取敏感信息
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
NASA_API_KEY = os.environ.get("NASA_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# 訂閱者列表 (記憶體存儲)
subscribers = set()
scheduler = AsyncIOScheduler()

# === 天文小知識列表 ===
ASTRONOMY_FACTS = [
    "🌌 太陽系中最大的行星是木星，它的質量是太陽系其他所有行星總和的兩倍半。",
    "⚡️ 光速是每秒約 299,792 公里，這是宇宙中資訊傳播的最高速度。",
    "✨ 銀河系是一個棒旋星系，包含數千億顆恆星，太陽就是其中之一。",
    "⚫️ 黑洞是一種引力極強的天體，連光也無法逃脫其引力束縛。",
    "🌕 月球是地球唯一的天然衛星，它的引力影響著地球的潮汐。",
    "🔥 金星是太陽系中最熱的行星，表面溫度高達攝氏 462 度，比水星還要熱。",
    "🪐 土星以其美麗而複雜的光環而聞名，這些光環主要由冰粒和岩石組成。",
    "🔭 哈伯太空望遠鏡自 1990 年以來一直在軌道上運行，為我們提供了大量關於宇宙的驚人圖像和數據。",
    "💫 獵戶座大星雲是一個活躍的恆星形成區域，距離地球約 1,344 光年，肉眼可見。",
    "🕰️ 宇宙的年齡估計約為 138 億年，這個數字是通過測量宇宙膨脹的速度得出的。",
    "🌠 流星是進入地球大氣層的太空岩石塵埃顆粒，因與空氣摩擦而燃燒發光。",
    "☀️ 太陽是一顆黃矮星，位於銀河系的一個旋臂上，是地球生命能量的最終來源。",
    "🥶 冥王星現在被歸類為矮行星，它位於柯伊伯帶，是一個充滿冰冷天體的區域。",
    "👽 科學家們正在積極尋找太陽系外生命存在的證據，特別是在可能存在液態水的行星上。"
]

# === 選單鍵盤生成器 ===
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🌌 每日天文圖", callback_data='apod_daily'), InlineKeyboardButton("🎲 隨機天文圖", callback_data='apod_random')],
        [InlineKeyboardButton("☄️ 近地小行星", callback_data='neo_info'), InlineKeyboardButton("📸 火星探測器照片", callback_data='mars_rover_photos')],
        [InlineKeyboardButton("🌍 地球每日影像", callback_data='epic_earth_image'), InlineKeyboardButton("🛰️ 國際太空站位置", callback_data='iss_location')],
        [InlineKeyboardButton("💡 隨機天文小知識", callback_data='astronomy_fact'), InlineKeyboardButton("🌙 月相資訊", callback_data='moon_phase_info')],
        # 【新功能】在選單中加入「太陽耀斑報告」
        [InlineKeyboardButton("💥 太陽耀斑報告", callback_data='solar_flare_report'), InlineKeyboardButton("🌋 地磁風暴報告", callback_data='geomagnetic_storm_report')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def send_main_menu(chat_id: int, bot):
    try:
        await bot.send_message(chat_id=chat_id, text="請選擇一個天文相關功能：", reply_markup=get_main_menu_keyboard())
    except TelegramError as e:
        logger.error(f"發送主選單失敗給 {chat_id}: {e}")

# === Telegram Bot 命令處理器 ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ 歡迎來到 NASA 天文機器人！✨")
    await send_main_menu(update.effective_chat.id, context.bot)

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in subscribers:
        subscribers.add(chat_id)
        await update.message.reply_text("✅ 已訂閱每日 NASA APOD！")
    else:
        await update.message.reply_text("您已經是訂閱者了！")
    await send_main_menu(chat_id, context.bot)

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.discard(chat_id)
        await update.message.reply_text("❌ 已取消訂閱。")
    else:
        await update.message.reply_text("您尚未訂閱。")
    await send_main_menu(chat_id, context.bot)

async def apod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_apod_message(update.effective_chat.id, context.bot)
    await send_main_menu(update.effective_chat.id, context.bot)

# === 各項功能的核心函式 ===

async def send_apod_message(chat_id: int, bot, date: str = None):
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    if date:
        url += f"&date={date}"
    try:
        async with ClientSession() as session, session.get(url, timeout=15) as resp:
            resp.raise_for_status()
            data = await resp.json()
        title = data.get("title", "無標題")
        explanation = data.get("explanation", "無說明。")
        image_url = data.get("url", "")
        media_type = data.get("media_type", "image")
        translated = GoogleTranslator(source="auto", target="zh-TW").translate(explanation) or ("翻譯失敗。\n" + explanation)
        text = f"🌌 *{title}*\n\n{translated}"
        if date:
            text = f"🗓️ *{date}*\n" + text
        if media_type == "image":
            await bot.send_photo(chat_id=chat_id, photo=image_url, caption=text, parse_mode=ParseMode.MARKDOWN)
        else:
            await bot.send_message(chat_id=chat_id, text=f"{text}\n\n[觀看內容]({image_url})", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"發送 APOD 失敗: {e}", exc_info=True)
        await bot.send_message(chat_id=chat_id, text="抱歉，獲取天文圖失敗。")

async def send_daily_to_subscribers(bot):
    logger.info("開始向訂閱者發送每日 APOD。")
    for chat_id in subscribers.copy():
        try:
            await send_apod_message(chat_id, bot)
        except Exception as e:
            logger.error(f"發送 APOD 給訂閱者 {chat_id} 失敗：{e}")

def get_random_date():
    start = datetime.date(1995, 6, 16)
    today = datetime.date.today()
    return (start + datetime.timedelta(days=random.randrange((today - start).days))).strftime("%Y-%m-%d")

async def send_random_apod_from_callback(chat_id: int, bot):
    await send_apod_message(chat_id, bot, date=get_random_date())

async def send_neo_info(chat_id: int, bot):
    today = datetime.date.today().strftime("%Y-%m-%d")
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    try:
        async with ClientSession() as session, session.get(url, timeout=15) as resp:
            resp.raise_for_status()
            data = await resp.json()
        objects = data.get("near_earth_objects", {}).get(today, [])
        if not objects:
            await bot.send_message(chat_id=chat_id, text="今日沒有已知的近地小行星經過。")
            return
        msg = [f"☄️ *今日近地小行星 ({len(objects)} 個)*:\n"]
        for obj in objects[:5]:
            name = obj['name']
            hazard = "⚠️ 潛在危險" if obj['is_potentially_hazardous_asteroid'] else "✅ 無危險"
            dist = f"{float(obj['close_approach_data'][0]['miss_distance']['kilometers']):,.0f} 公里"
            diam = f"{float(obj['estimated_diameter']['meters']['estimated_diameter_max']):.2f} 公尺"
            msg.append(f"*{name}* ({hazard})\n- 最近距離: {dist}\n- 估計直徑: {diam}\n")
        await bot.send_message(chat_id=chat_id, text="\n".join(msg), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"發送近地小行星資訊失敗: {e}", exc_info=True)
        await bot.send_message(chat_id=chat_id, text="抱歉，無法獲取近地小行星資訊。")

async def send_mars_rover_photos(chat_id: int, bot):
    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/perseverance/latest_photos?api_key={NASA_API_KEY}"
    try:
        async with ClientSession() as session, session.get(url, timeout=20) as resp:
            resp.raise_for_status()
            data = await resp.json()
        photos = data.get("latest_photos", [])
        if not photos:
            await bot.send_message(chat_id=chat_id, text="抱歉，目前沒有毅力號的最新照片。")
            return
        for photo in sorted(photos, key=lambda x: x['id'], reverse=True)[:3]:
            caption = f"📸 *火星探測器照片*\n- 探測器: {photo['rover']['name']}\n- 相機: {photo['camera']['full_name']}\n- 地球日期: {photo['earth_date']}"
            await bot.send_photo(chat_id=chat_id, photo=photo['img_src'], caption=caption, parse_mode=ParseMode.MARKDOWN)
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"發送火星照片失敗: {e}", exc_info=True)
        await bot.send_message(chat_id=chat_id, text="抱歉，無法獲取火星照片。")

async def send_epic_earth_image(chat_id: int, bot):
    url = f"https://api.nasa.gov/EPIC/api/natural/images?api_key={NASA_API_KEY}"
    try:
        async with ClientSession() as session, session.get(url, timeout=15) as resp:
            resp.raise_for_status()
            images = await resp.json()
        if not images:
            await bot.send_message(chat_id=chat_id, text="抱歉，無法獲取最新的地球影像。")
            return
        img = images[0]
        date = datetime.datetime.fromisoformat(img['date'].replace('Z', '+00:00'))
        img_url = f"https://api.nasa.gov/EPIC/archive/natural/{date.strftime('%Y/%m/%d')}/png/{img['image']}.png?api_key={NASA_API_KEY}"
        caption = f"🌍 *地球每日影像 (EPIC)*\n日期: {date.strftime('%Y年%m月%d日 %H:%M:%S UTC')}"
        await bot.send_photo(chat_id=chat_id, photo=img_url, caption=caption, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"發送地球影像失敗: {e}", exc_info=True)
        await bot.send_message(chat_id=chat_id, text="抱歉，無法獲取地球影像。")

async def send_iss_location(chat_id: int, bot):
    url = "https://api.wheretheiss.at/v1/satellites/25544"
    try:
        async with ClientSession() as session, session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            data = await resp.json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        timestamp = data.get('timestamp')
        if latitude is not None and longitude is not None and timestamp is not None:
            time_obj = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            msg = (f"🛰️ *國際太空站 (ISS) 即時位置*\n"
                   f"- 經度: `{longitude:.4f}`\n- 緯度: `{latitude:.4f}`\n"
                   f"- 更新時間: {time_obj.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                   f"[在地圖上查看](https://www.google.com/maps/search/?api=1&query={latitude},{longitude})")
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)
        else:
            raise ValueError("從 API 收到的資料缺少必要欄位。")
    except Exception as e:
        logger.error(f"發送ISS位置失敗: {e}", exc_info=True)
        await bot.send_message(chat_id=chat_id, text="抱歉，無法獲取國際太空站位置。")

async def send_astronomy_fact(chat_id: int, bot):
    await bot.send_message(chat_id=chat_id, text=random.choice(ASTRONOMY_FACTS), parse_mode=ParseMode.MARKDOWN)

def get_moon_phase(date: datetime.date):
    phases = ["🌑 新月", "🌒 娥眉月", "🌓 上弦月", "🌔 盈凸月", "🌕 滿月", "🌖 虧凸月", "🌗 下弦月", "🌘 殘月"]
    days = (date - datetime.date(2000, 1, 6)).days % 29.530588
    index = int((days / 29.530588) * 8 + 0.5) % 8
    return phases[index]

async def send_moon_phase_info(chat_id: int, bot):
    today = datetime.date.today()
    phase = get_moon_phase(today)
    msg = f"🌙 *今日月相*: {phase}\n日期: {today.strftime('%Y年%m月%d日')}"
    await bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

# === 地磁風暴報告 (DONKI API) ===
def get_kp_level_description(kp_value: int):
    """根據 Kp 指數值返回中文描述和等級"""
    if kp_value < 4: return "✅ 平靜 (Quiet)", "G0"
    if kp_value == 4: return "⚠️ 不穩定 (Unsettled)", "G0"
    if kp_value == 5: return "🔶 輕度磁暴 (Minor Storm)", "G1"
    if kp_value == 6: return "🟠 中度磁暴 (Moderate Storm)", "G2"
    if kp_value == 7: return "🔴 強烈磁暴 (Strong Storm)", "G3"
    if kp_value == 8: return "🟣 特強磁暴 (Severe Storm)", "G4"
    if kp_value == 9: return "🟪 極端磁暴 (Extreme Storm)", "G5"
    return "❔ 未知", ""

async def send_geomagnetic_storm_report(chat_id: int, bot):
    """從 NASA DONKI API 獲取地磁風暴 (GST) 數據。"""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    api_url = f"https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/GST?startDate={today_str}&endDate={today_str}"
    try:
        await bot.send_message(chat_id=chat_id, text="正在從 NASA DONKI 系統獲取地磁風暴數據...")
        async with ClientSession() as session, session.get(api_url, timeout=20) as resp:
            resp.raise_for_status()
            data = await resp.json()
        if not data:
            message = "✅ *今日地磁活動平靜*\n\n根據 NASA DONKI 系統的記錄，今天到目前為止沒有發生地磁風暴事件。"
            await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
            return
        latest_gst_event = data[-1]
        all_kp_index = latest_gst_event.get("allKpIndex")
        if not all_kp_index:
            raise ValueError("地磁風暴事件中未包含 Kp 指數數據。")
        latest_kp_data = all_kp_index[-1]
        kp_value = latest_kp_data.get("kpIndex")
        observed_time_str = latest_kp_data.get("observedTime")
        description, level = get_kp_level_description(kp_value)
        update_time_utc = datetime.datetime.fromisoformat(observed_time_str.replace("Z", "+00:00"))
        update_time_taipei = update_time_utc.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
        message = (
            f"🌋 *地磁風暴即時報告 (DONKI)*\n\n"
            f"📈 *最新觀測 Kp 指數*: `{kp_value}`\n"
            f"- *當前狀況*: {description}\n"
            f"- *磁暴等級*: {level}\n\n"
            f"🕒 *觀測時間*\n"
            f"- UTC: `{update_time_utc.strftime('%Y-%m-%d %H:%M')}`\n"
            f"- 台北: `{update_time_taipei.strftime('%Y-%m-%d %H:%M')}`\n\n"
            f"ℹ️ *資料來源*: NASA DONKI (Database Of Notifications, Knowledge, Information)"
        )
        await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"發送地磁風暴報告失敗: {e}", exc_info=True)
        await bot.send_message(chat_id=chat_id, text="抱歉，目前無法獲取 NASA DONKI 的地磁風暴數據。")

# === 【新功能】太陽耀斑報告 (DONKI API) ===
async def send_solar_flare_report(chat_id: int, bot):
    """從 NASA DONKI API 獲取太陽耀斑 (FLR) 數據。"""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    api_url = f"https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/FLR?startDate={today_str}&endDate={today_str}"
    try:
        await bot.send_message(chat_id=chat_id, text="正在從 NASA DONKI 系統獲取太陽耀斑數據...")
        async with ClientSession() as session, session.get(api_url, timeout=20) as resp:
            resp.raise_for_status()
            data = await resp.json()
        if not data:
            message = "☀️ *今日太陽活動平靜*\n\n根據 NASA DONKI 系統的記錄，今天到目前為止沒有發生太陽耀斑事件。"
            await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
            return
        
        message_parts = [f"💥 *今日太陽耀斑報告 (共 {len(data)} 起)*\n"]
        # 只顯示最新的 5 起事件
        for flare in reversed(data[-5:]):
            class_type = flare.get('classType', 'N/A')
            peak_time_str = flare.get('peakTime', 'N/A').replace("Z", "+00:00")
            peak_time_utc = datetime.datetime.fromisoformat(peak_time_str)
            region = flare.get('sourceLocation', '未知區域')
            
            message_parts.append(f"\n- *等級*: `{class_type}`\n"
                                 f"- *峰值時間 (UTC)*: `{peak_time_utc.strftime('%H:%M')}`\n"
                                 f"- *來源*: {region}")
        
        await bot.send_message(chat_id=chat_id, text="".join(message_parts), parse_mode=ParseMode.MARKDOWN)
        logger.info(f"成功從 DONKI 發送太陽耀斑報告給 {chat_id}")

    except Exception as e:
        logger.error(f"發送太陽耀斑報告失敗: {e}", exc_info=True)
        await bot.send_message(chat_id=chat_id, text="抱歉，目前無法獲取 NASA DONKI 的太陽耀斑數據。")

# === 回調查詢處理器 ===
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    bot = context.bot
    data = query.data

    function_map = {
        'apod_daily': send_apod_message, 'apod_random': send_random_apod_from_callback,
        'neo_info': send_neo_info, 'mars_rover_photos': send_mars_rover_photos,
        'epic_earth_image': send_epic_earth_image, 'iss_location': send_iss_location,
        'astronomy_fact': send_astronomy_fact, 'moon_phase_info': send_moon_phase_info,
        'geomagnetic_storm_report': send_geomagnetic_storm_report,
        'solar_flare_report': send_solar_flare_report, # 【新功能】加入對應
    }
    if data in function_map:
        await function_map[data](chat_id, bot)
    
    await send_main_menu(chat_id, bot)

# === Webhook 設置和應用程式主體 ===
async def setup_webhook(application: Application):
    if WEBHOOK_URL:
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}", allowed_updates=Update.ALL_TYPES)
        logger.info(f"Webhook 已設置為 {WEBHOOK_URL}")

async def health_check(request):
    return web.Response(text="Bot is running")

async def on_startup(app: web.Application):
    application: Application = app['bot_app']
    await application.initialize()
    await setup_webhook(application)
    scheduler.start()
    logger.info("Scheduler and Application have been initialized and started.")

async def on_shutdown(app: web.Application):
    application: Application = app['bot_app']
    scheduler.shutdown()
    await application.shutdown()
    logger.info("Scheduler and Application have been shut down.")

def main():
    if not TELEGRAM_BOT_TOKEN or not NASA_API_KEY:
        logger.critical("必要的環境變數 BOT_TOKEN 或 NASA_API_KEY 未設置。")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 註冊處理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("apod", apod))
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    # 每日 APOD 推送 (UTC 12:00, 台北時間 20:00)
    scheduler.add_job(send_daily_to_subscribers, 'cron', hour=12, minute=0, args=[application.bot])

    port = int(os.environ.get('PORT', 8443))
    
    if WEBHOOK_URL:
        # Webhook 模式 (用於部署)
        logger.info("以 Webhook 模式啟動...")
        webapp = web.Application()
        webapp['bot_app'] = application
        webapp.on_startup.append(on_startup)
        webapp.on_shutdown.append(on_shutdown)

        async def telegram_webhook(request):
            try:
                update = Update.de_json(await request.json(), application.bot)
                await application.process_update(update)
                return web.Response()
            except Exception as e:
                logger.error(f"處理 webhook 時發生錯誤: {e}", exc_info=True)
                return web.Response(status=500)

        webapp.add_routes([
            web.post(f'/{TELEGRAM_BOT_TOKEN}', telegram_webhook),
            web.get('/health', health_check)
        ])
        
        web.run_app(webapp, host="0.0.0.0", port=port)
    else:
        # 本地 Polling 模式 (用於開發)
        logger.info("以 Polling 模式啟動...")
        scheduler.start()
        application.run_polling()
        scheduler.shutdown()

if __name__ == "__main__":
    main()
