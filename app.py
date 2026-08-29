from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
import threading
import yt_dlp
import os
import time

app = Flask(__name__)
CORS(app)

ACTIVE_BOTS_FILE = "tokens.txt"
active_bots = {}

def run_bot(token):
    try:
        bot = telebot.TeleBot(token)

        @bot.message_handler(commands=['start'])
        def send_welcome(message):
            bot.reply_to(message, "Merhaba! Ben 7/24 aktif Medya İndirici botum. Bana YouTube, Instagram veya TikTok linki gönder, videoyu indireyim.")

        @bot.message_handler(func=lambda message: True)
        def download_media(message):
            url = message.text
            if "http" not in url:
                bot.reply_to(message, "Lütfen geçerli bir video linki gönder.")
                return

            msg = bot.reply_to(message, "⏳ Link inceleniyor ve indiriliyor, lütfen bekle...")
            
            try:
                file_name = f"video_{message.chat.id}_{int(time.time())}.mp4"
                ydl_opts = {
                    'outtmpl': file_name,
                    'format': 'best',
                    'quiet': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                with open(file_name, 'rb') as video:
                    bot.send_video(message.chat.id, video, caption="✅ İşte videon!")
                
                os.remove(file_name)
                bot.delete_message(message.chat.id, msg.message_id)

            except Exception as e:
                bot.edit_message_text(f"❌ Hata Detayı: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Bot başlatılamadı: {e}")

def load_saved_bots():
    if os.path.exists(ACTIVE_BOTS_FILE):
        with open(ACTIVE_BOTS_FILE, "r") as f:
            tokens = f.read().splitlines()
            for token in tokens:
                token = token.strip()
                if token and token not in active_bots:
                    thread = threading.Thread(target=run_bot, args=(token,))
                    thread.daemon = True
                    thread.start()
                    active_bots[token] = thread

# Sunucu başlarken kayıtlı botları otomatik uyandır
load_saved_bots()

@app.route('/')
def home():
    return "Bot Sunucusu Aktif, 7/24 Çalışıyor!"

@app.route('/api/baslat', methods=['POST'])
def baslat_api():
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({"error": "Token gönderilmedi!"}), 400
        
    if token in active_bots:
        return jsonify({"message": "Bu bot zaten aktif ve çalışıyor!"}), 200

    # Token'ı dosyaya kaydet (kalıcı olması için)
    with open(ACTIVE_BOTS_FILE, "a") as f:
        f.write(token + "\n")

    # Botu başlat
    thread = threading.Thread(target=run_bot, args=(token,))
    thread.daemon = True
    thread.start()
    active_bots[token] = thread

    return jsonify({"message": "Tebrikler! Bot başarıyla 7/24 medya indiriciye dönüştürüldü."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
