import os
from dotenv import load_dotenv

# .env dosyasını bul ve içindeki değişkenleri yükle
load_dotenv()

class Config:
    """
    Proje için gerekli tüm ayarları .env dosyasından okuyan ve saklayan sınıf.
    """
    # Instagram ayarları
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
    
    # Supabase ayarları
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    
    # Bot ayarları
    MIN_MAGNITUDE = 4.0  # Paylaşım yapılacak minimum deprem büyüklüğü
    CHECK_INTERVAL_MINUTES = 5  # Depremleri kontrol etme sıklığı (dakika)
    
    # Kandilli ayarları
    KANDILLI_URL = "http://www.koeri.boun.edu.tr/scripts/lst0.asp"