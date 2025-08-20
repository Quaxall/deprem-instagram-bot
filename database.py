# Gerekli kütüphaneleri import et
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict

# Supabase kütüphanesini import et
try:
    from supabase import create_client, Client
except ImportError:
    print("HATA: 'supabase' kütüphanesi bulunamadı. Lütfen 'pip install supabase' ile yükleyin.")
    exit()

# python-dotenv kütüphanesini import et
try:
    from dotenv import load_dotenv
except ImportError:
    print("HATA: 'python-dotenv' kütüphanesi bulunamadı. Lütfen 'pip install python-dotenv' ile yükleyin.")
    exit()


# Temel loglama ayarlarını yap
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# .env dosyasını yükle ve Supabase değişkenlerini al
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")


class EarthquakeDatabase:
    def __init__(self, url: str, key: str):
        """Veritabanı bağlantısını kurar."""
        if not url or not key:
            logging.error("Supabase URL ve Key .env dosyasında bulunamadı!")
            raise ValueError("SUPABASE_URL ve SUPABASE_ANON_KEY ayarlanmalı.")
        
        try:
            self.supabase: Client = create_client(url, key)
            logging.info("✅ Supabase bağlantısı başarıyla kuruldu.")
        except Exception as e:
            logging.error(f"❌ Supabase client oluşturulurken hata: {e}")
            raise

    def is_earthquake_posted(self, kandilli_id: str) -> bool:
        """Verilen ID'ye sahip depremin veritabanında olup olmadığını kontrol eder."""
        try:
            response = self.supabase.table('earthquakes').select('id').eq('kandilli_id', kandilli_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logging.error(f"Deprem kontrolü sırasında hata: {e}")
            return False # Hata durumunda paylaşılmış varsaymak daha güvenli olabilir.

    def save_earthquake(self, eq_data: Dict) -> bool:
        """Yeni deprem verisini veritabanına kaydeder."""
        try:
            # Proje planımızdaki tablo yapısıyla eşleşen veriyi hazırla
            db_record = {
                'kandilli_id': eq_data.get('kandilli_id'),
                'magnitude': eq_data.get('magnitude'),
                'depth': eq_data.get('depth'),
                'location': eq_data.get('location'),
                'earthquake_time': eq_data['earthquake_time'].isoformat(),
                'latitude': eq_data.get('latitude'),
                'longitude': eq_data.get('longitude'),
                'posted_to_instagram': True, # Bu fonksiyon çağrıldığında paylaşılmış demektir.
                'posted_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('earthquakes').insert(db_record).execute()
            
            if len(response.data) > 0:
                logging.info(f"✅ Deprem veritabanına kaydedildi: {db_record['location']}")
                return True
            else:
                logging.error(f"Deprem kaydedilemedi. Supabase yanıtı: {response}")
                return False

        except Exception as e:
            logging.error(f"❌ Deprem kaydı sırasında kritik hata: {e}")
            return False


# --- BU DOSYAYI DOĞRUDAN ÇALIŞTIRMAK İÇİN TEST ALANI ---
if __name__ == "__main__":
    print("\n--- Veritabanı Modülü Testi Başlatılıyor ---")

    # 1. Adım: .env dosyasından değişkenlerin okunup okunmadığını kontrol et
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ TEST BAŞARISIZ: .env dosyasını kontrol edin. SUPABASE_URL ve SUPABASE_ANON_KEY bulunamadı.")
    else:
        print("✅ .env değişkenleri başarıyla okundu.")
        
        try:
            # 2. Adım: Veritabanı bağlantısını test et
            print("\n-> Supabase'e bağlanılıyor...")
            db = EarthquakeDatabase(url=SUPABASE_URL, key=SUPABASE_KEY)
            print("✅ Veritabanı bağlantı nesnesi oluşturuldu.")

            # 3. Adım: Gerçek bir sorgu ile bağlantıyı test et
            print("\n-> 'earthquakes' tablosuna erişim deneniyor...")
            test_response = db.supabase.table('earthquakes').select('id', head=True).execute()
            print("✅ Tablo erişim testi başarılı.")

            # 4. Adım: Örnek bir deprem verisiyle kaydetme ve kontrol etme fonksiyonlarını test et
            print("\n-> Kaydetme ve Kontrol etme fonksiyonları test ediliyor...")
            
            # Test için sahte bir deprem verisi oluşturalım
            # Bu ID'yi her testte farklı yapmak için saniye ekleyelim
            current_second = datetime.now().second
            fake_kandilli_id = f"test_{datetime.now().date()}_{current_second}"

            fake_earthquake = {
                'kandilli_id': fake_kandilli_id,
                'magnitude': 3.5,
                'depth': 10.1,
                'location': 'GEMINI-TEST (MARMARA)',
                'earthquake_time': datetime.now() - timedelta(minutes=10),
                'latitude': 40.7128,
                'longitude': 29.0060
            }
            
            # Önce bu depremin sistemde olmadığından emin olalım
            is_posted = db.is_earthquake_posted(fake_kandilli_id)
            print(f"'{fake_earthquake['location']}' depremi sistemde var mı? -> {is_posted}")
            
            if not is_posted:
                print("-> Deprem sistemde yok, şimdi kaydediliyor...")
                save_success = db.save_earthquake(fake_earthquake)
                if save_success:
                    print("✅ Deprem başarıyla kaydedildi.")
                    # Tekrar kontrol edelim, bu sefer 'True' dönmeli
                    is_posted_after_save = db.is_earthquake_posted(fake_kandilli_id)
                    print(f"-> Kayıttan sonra tekrar kontrol ediliyor: Sistemde var mı? -> {is_posted_after_save}")
                    if not is_posted_after_save:
                        print("❌ TEST BAŞARISIZ: Deprem kaydedildi ama kontrol fonksiyonu bulamadı!")
                else:
                    print("❌ TEST BAŞARISIZ: Deprem kaydetme fonksiyonu 'False' döndü.")
            else:
                print("-> Deprem zaten sistemde mevcut. Testin bu kısmı atlanıyor. (Eski bir testi silmeniz gerekebilir)")

            print("\n--- Veritabanı Modülü Testi Tamamlandı ---")

        except Exception as e:
            print(f"\n❌ TEST SIRASINDA KRİTİK BİR HATA OLUŞTU: {e}")