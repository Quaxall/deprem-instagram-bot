import schedule
import time
import logging
from datetime import datetime

# Kendi yazdığımız modülleri import edelim
from kandilli_scraper import KandilliScraper
from database import EarthquakeDatabase
from instagram_poster import InstagramPoster
from config import Config

# Temel loglama ayarlarını yap
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_and_post_earthquakes():
    """
    Ana bot fonksiyonu: Depremleri kontrol eder ve yenilerini Instagram'a gönderir.
    """
    logging.info("--- Yeni deprem kontrol döngüsü başlatıldı ---")
    
    try:
        # 1. Gerekli tüm sınıflardan nesneler oluştur
        scraper = KandilliScraper()
        db = EarthquakeDatabase(url=Config.SUPABASE_URL, key=Config.SUPABASE_ANON_KEY)
        poster = InstagramPoster(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)

        # Instagram'a giriş yapılamadıysa, işlemi durdur
        if not poster.client:
            logging.error("Instagram'a giriş yapılamadığı için bu döngü atlanıyor.")
            return

        # 2. Kandilli'den son depremleri çek
        latest_earthquakes = scraper.get_latest_earthquakes()

        if not latest_earthquakes:
            logging.info("Kandilli'den yeni veri çekilemedi veya deprem yok.")
            return

        # 3. Sadece belirli büyüklük ve üzerindeki depremleri filtrele
        significant_earthquakes = [eq for eq in latest_earthquakes if eq['magnitude'] >= Config.MIN_MAGNITUDE]

        if not significant_earthquakes:
            logging.info(f"{Config.MIN_MAGNITUDE} büyüklüğünde veya daha büyük yeni deprem bulunamadı.")
            return
        
        logging.info(f"{len(significant_earthquakes)} adet {Config.MIN_MAGNITUDE}+ büyüklüğünde deprem bulundu.")

        # 4. Bu depremlerden hangilerinin daha önce paylaşılmadığını veritabanından kontrol et
        new_earthquakes_to_post = []
        for eq in significant_earthquakes:
            if not db.is_earthquake_posted(eq['kandilli_id']):
                new_earthquakes_to_post.append(eq)
        
        if not new_earthquakes_to_post:
            logging.info("Bulunan tüm önemli depremler daha önce paylaşılmış.")
            return

        logging.info(f"Paylaşılacak {len(new_earthquakes_to_post)} yeni deprem var!")

        # 5. Paylaşılacak her yeni deprem için işlemleri yap (en eskiden başlayarak)
        for earthquake in reversed(new_earthquakes_to_post):
            logging.info(f"Yeni deprem paylaşılıyor: {earthquake['location']} - M{earthquake['magnitude']}")
            
            # A. Görseli oluştur
            image_path = poster.create_earthquake_image(earthquake)
            
            if not image_path:
                logging.error("Görsel oluşturulamadı, bu deprem atlanıyor.")
                continue

            # B. Deprem büyüklüğüne göre başlık (caption) oluştur
            magnitude = earthquake['magnitude']
            
            caption_text = f"🚨 DEPREM BİLDİRİMİ\n\n"
            caption_text += f"📍 Lokasyon: {earthquake['location']}\n"
            caption_text += f"📊 Büyüklük: M {magnitude}\n"
            caption_text += f"📏 Derinlik: {earthquake['depth']} km\n"
            caption_text += f"📅 Tarih: {earthquake['earthquake_time'].strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            caption_text += "ℹ️ Kandilli Rasathanesi verisidir.\n\n"

            if 4 <= magnitude < 5:
                caption_text += "⚠️ Sevdiklerinize ulaşmakta zorlanıyorsanız, internet tabanlı mesajlaşma uygulamalarını kullanmayı deneyin.\n\n"
            elif 5 <= magnitude < 6:
                caption_text += "⚠️ Lütfen sığınaklara veya güvenli toplanma alanlarına gidin.\n"
                caption_text += "⚠️ Sevdiklerinize ulaşmakta zorlanıyorsanız, internet tabanlı mesajlaşma uygulamalarını kullanmayı deneyin.\n\n"
            elif magnitude >= 6:
                caption_text += "⚠️ ACİL DURUM UYARISI! Lütfen güvenli bir yerde kalın ve konumunuzu güvendiğiniz kişilerle paylaşın.\n"
                caption_text += "⚠️ Sığınaklara veya güvenli toplanma alanlarına gidin.\n"
                caption_text += "⚠️ Sevdiklerinize ulaşmakta zorlanıyorsanız, internet tabanlı mesajlaşma uygulamalarını kullanın.\n\n"

            caption_text += "#deprem #kandilli #türkiye #earthquake"

            # C. Instagram'a gönder
            post_success = poster.post_image_to_instagram(image_path, caption_text)

            # D. Başarılı olduysa veritabanına kaydet
            if post_success:
                db.save_earthquake(earthquake)
                logging.info(f"Deprem başarıyla paylaşıldı ve veritabanına kaydedildi: {earthquake['location']}")
            else:
                logging.error(f"Deprem paylaşılamadı, veritabanına kaydedilmeyecek: {earthquake['location']}")
            
            time.sleep(30) # Instagram'dan ban yememek için postlar arasına biraz zaman koyalım

    except Exception as e:
        logging.critical(f"!!! ANA DÖNGÜDE KRİTİK HATA: {e}", exc_info=True)

    logging.info("--- Kontrol döngüsü tamamlandı ---")


# Ana program başlangıcı
if __name__ == "__main__":
    logging.info(">>> Deprem Instagram Bot'u başlatıldı. <<<")
    logging.info(f"Kontrol sıklığı: {Config.CHECK_INTERVAL_MINUTES} dakika.")
    
    # Botu hemen ilk çalıştırmada bir kez çalıştır
    check_and_post_earthquakes()

    # Ardından her X dakikada bir çalışacak şekilde zamanla
    schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(check_and_post_earthquakes)

    while True:
        schedule.run_pending()
        time.sleep(1)