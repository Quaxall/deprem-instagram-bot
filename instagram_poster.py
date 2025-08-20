import os
from PIL import Image, ImageDraw, ImageFont
import logging
from datetime import datetime

# Gerekli kütüphaneleri ve ayar dosyasını import et
try:
    from instagrapi import Client
    from config import Config
except ImportError as e:
    print(f"HATA: Gerekli bir kütüphane eksik: {e}. Lütfen 'pip install instagrapi python-dotenv Pillow' komutunu çalıştırın.")
    exit()

# Temel loglama ayarlarını yap
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class InstagramPoster:
    def __init__(self, username, password):
        """
        Instagram istemcisini başlatır ve giriş yapar.
        """
        self.username = username
        self.password = password
        self.client = None

        if not username or not password:
            logging.warning("Instagram kullanıcı adı veya şifresi eksik. Giriş yapılamadı.")
            return

        self.client = Client()
        try:
            logging.info(f"'{self.username}' olarak Instagram'a giriş yapılıyor...")
            self.client.login(self.username, self.password)
            logging.info("✅ Instagram'a başarıyla giriş yapıldı.")
        except Exception as e:
            logging.error(f"❌ Instagram'a giriş yapılamadı: {e}")
            self.client = None

    def create_earthquake_image(self, earthquake_data: dict, output_path="earthquake_post.jpg"):
        """
        Verilen deprem verilerinden bir görsel oluşturur.
        """
        logging.info(f"'{earthquake_data['location']}' için görsel oluşturuluyor...")

        # Görsel Ayarları
        width, height = 1080, 1080
        background_color = (255, 255, 255)
        text_color = (0, 0, 0)
        red_color = (200, 0, 0)
        gray_color = (100, 100, 100)

        image = Image.new("RGB", (width, height), background_color)
        draw = ImageDraw.Draw(image)

        try:
            # Türkçe karakterleri destekleyen Open Sans fontunu kullanıyoruz
            # Dosya adını senin belirttiğin şekilde güncelledim.
            font_path = "fonts/OpenSans-VariableFont_wdth,wght.ttf"
            font_large = ImageFont.truetype(font_path, size=90)
            font_medium = ImageFont.truetype(font_path, size=60)
            font_footer = ImageFont.truetype(font_path, size=30)
        except IOError:
            logging.error(f"Font dosyası bulunamadı: {font_path}.")
            return None

        # Uyarı İşareti Ekleme
        try:
            warning_icon = Image.open("uyari_isareti.png").convert("RGBA").resize((100, 100))
            icon_x = (width - warning_icon.width) / 2
            icon_y = 200
            image.paste(warning_icon, (int(icon_x), int(icon_y)), warning_icon)
        except FileNotFoundError:
            logging.warning("Uyarı işareti görseli 'uyari_isareti.png' bulunamadı.")

        # Büyüklük
        magnitude_text = f"M {earthquake_data['magnitude']}"
        mag_bbox = draw.textbbox((0, 0), magnitude_text, font=font_large)
        mag_width = mag_bbox[2] - mag_bbox[0]
        mag_x = (width - mag_width) / 2
        mag_y = 450
        draw.text((mag_x, mag_y), magnitude_text, font=font_large, fill=red_color)

        # Lokasyon
        location_text = earthquake_data['location'].upper()
        loc_bbox = draw.textbbox((0, 0), location_text, font=font_medium)
        loc_width = loc_bbox[2] - loc_bbox[0]
        loc_x = (width - loc_width) / 2
        loc_y = 350
        draw.text((loc_x, loc_y), location_text, font=font_medium, fill=text_color)
        
        # Diğer Bilgiler
        depth_text = f"Derinlik: {earthquake_data['depth']} km"
        date_str = earthquake_data['earthquake_time'].strftime('%d.%m.%Y %H:%M:%S')
        draw.text((150, 650), depth_text, font=font_medium, fill=text_color)
        draw.text((150, 750), f"Tarih: {date_str}", font=font_medium, fill=text_color)
        
        # Alt Bilgi
        footer_text = "Kaynak: Kandilli Rasathanesi"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_x = (width - footer_width) / 2
        draw.text((footer_x, 980), footer_text, font=font_footer, fill=gray_color)

        image.save(output_path)
        logging.info(f"Görsel başarıyla '{output_path}' olarak kaydedildi.")
        return output_path

    def post_image_to_instagram(self, image_path: str, caption: str):
        """
        Oluşturulan görseli verilen başlıkla Instagram'a gönderir.
        """
        if not self.client:
            logging.warning("Instagram'a giriş yapılmadığı için post atılamadı.")
            return False
        try:
            logging.info(f"'{image_path}' adresindeki görsel Instagram'a gönderiliyor...")
            self.client.photo_upload(image_path, caption=caption)
            logging.info("✅ Görsel başarıyla Instagram'da paylaşıldı.")
            return True
        except Exception as e:
            logging.error(f"❌ Görsel Instagram'a gönderilemedi: {e}")
            return False


# --- CANLI TEST ALANI ---
if __name__ == "__main__":
    print(f"--- Instagram Poster CANLI TEST (Yeni Font ile) ---")

    if not Config.INSTAGRAM_USERNAME or not Config.INSTAGRAM_PASSWORD:
        print("\n❌ HATA: Lütfen .env dosyasına INSTAGRAM_USERNAME ve INSTAGRAM_PASSWORD bilgilerini ekleyin.")
    else:
        print(f"✅ .env dosyasından '{Config.INSTAGRAM_USERNAME}' kullanıcısı okundu.")
        
        poster = InstagramPoster(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)

        if poster.client:
            test_earthquake = {
                'magnitude': 4.2,
                'location': 'İZMİR AÇIKLARI (EGE DENİZİ)', 
                'depth': 8.5,
                'earthquake_time': datetime.now()
            }
            
            generated_image_path = poster.create_earthquake_image(test_earthquake)
            
            if generated_image_path:
                print(f"✅ Görsel başarıyla oluşturuldu: '{generated_image_path}'")
                
                magnitude = test_earthquake['magnitude']
                
                caption_text = f"🚨 DEPREM BİLDİRİMİ (TEST)\n\n"
                caption_text += f"📍 Lokasyon: {test_earthquake['location']}\n"
                caption_text += f"📊 Büyüklük: M {magnitude}\n"
                caption_text += f"📏 Derinlik: {test_earthquake['depth']} km\n"
                caption_text += f"📅 Tarih: {test_earthquake['earthquake_time'].strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                caption_text += f"ℹ️ Bu, @{Config.INSTAGRAM_USERNAME} botunun test gönderisidir.\n\n"

                if 4 <= magnitude < 5:
                    caption_text += "⚠️ Sevdiklerinize ulaşmakta zorlanıyorsanız, internet tabanlı mesajlaşma uygulamalarını kullanmayı deneyin.\n\n"
                
                caption_text += "#deprem #kandilli #türkiye #earthquake #test #izmir"

                print("\n--- Oluşturulan Instagram Başlığı ---")
                print(caption_text)

                success = poster.post_image_to_instagram(generated_image_path, caption_text)

                if success:
                    print("\n✅ CANLI TEST BAŞARILI! Gönderi Instagram hesabında paylaşıldı.")
                else:
                    print("\n❌ CANLI TEST BAŞARISIZ! Gönderi paylaşılamadı.")
            else:
                print("❌ Görsel oluşturulurken bir hata oluştu.")
        else:
            print("\n❌ Instagram'a giriş yapılamadığı için test devam edemedi.")

    print("\n--- Test Tamamlandı ---")