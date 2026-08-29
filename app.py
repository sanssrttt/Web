from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
import threading
import yt_dlp
import os
import time

app = Flask(__name__)
CORS(app) # Web sitenden gelen isteklere izin verir

active_bots = {} # Çalışan botları hafızada tutar

def run_bot(token):
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        bot.reply_to(message, "Merhaba! Ben bir Medya İndirici botum. Bana YouTube, Instagram veya TikTok linki gönder, videoyu indireyim.")

    @bot.message_handler(func=lambda message: True)
    def download_media(message):
        url = message.text
        if "http" not in url:
            bot.reply_to(message, "Lütfen geçerli bir video linki gönder.")
            return

        msg = bot.reply_to(message, "⏳ Link inceleniyor ve indiriliyor, lütfen bekle...")
        
        try:
            # yt-dlp ile medyayı indirme ayarları
            file_name = f"video_{message.chat.id}_{int(time.time())}.mp4"
            ydl_opts = {
                'outtmpl': file_name,
                'format': 'best',
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # İndirilen videoyu Telegramdan kullanıcıya at
            with open(file_name, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="✅ İşte videon!")
            
            # Sunucuda yer kaplamaması için videoyu sil
            os.remove(file_name)
            bot.delete_message(message.chat.id, msg.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ Hata Detayı: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

    # Botun sürekli mesaj beklemesini sağla
    bot.polling(non_stop=True)

@app.route('/')
def home():
    return "Bot Sunucusu Aktif ve Çalışıyor!"

@app.route('/api/baslat', methods=['POST'])
def baslat_api():
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({"error": "Token gönderilmedi!"}), 400
        
    if token in active_bots:
        return jsonify({"message": "Bu bot zaten bir medya indirici olarak çalışıyor!"}), 200

    # Sistemi dondurmamak için her botu ayrı bir işlem (thread) olarak başlatıyoruz
    thread = threading.Thread(target=run_bot, args=(token,))
    thread.daemon = True
    thread.start()
    active_bots[token] = thread

    return jsonify({"message": "Tebrikler! Bot başarıyla medya indiriciye dönüştürüldü."}), 200

if __name__ == '__main__':
    # Sunucuyu başlat
    app.run(host='0.0.0.0', port=10000)
