import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
import logging

# Logger kurulumu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KandilliScraper:
    def __init__(self):
        self.url = "http://www.koeri.boun.edu.tr/scripts/lst0.asp"
        self.session = requests.Session()
        
        # Headers ekle (bot olmadığımızı göstermek için)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_latest_earthquakes(self):
        """Kandilli'den son depremleri çek"""
        try:
            logger.info("Kandilli'den veri çekiliyor...")
            
            # Kandilli sitesine istek gönder
            response = self.session.get(self.url, timeout=15)
            response.raise_for_status()
            
            # Türkçe karakter sorunları için encoding ayarla
            response.encoding = 'utf-8'
            
            # HTML'i parse et
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Pre tagını bul (Kandilli verileri burada)
            pre_tag = soup.find('pre')
            if not pre_tag:
                logger.error("Pre tag bulunamadı - site yapısı değişmiş olabilir")
                return []
            
            # Satırları ayır
            lines = pre_tag.text.strip().split('\n')
            
            earthquakes = []
            
            for line in lines[7:]:  # İlk 7 satır başlık
                earthquake = self.parse_earthquake_line(line)
                if earthquake:
                    earthquakes.append(earthquake)
            
            logger.info(f"{len(earthquakes)} deprem verisi çekildi")
            return earthquakes
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kandilli sitesine bağlanırken hata: {e}")
            return []
        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")
            return []
    
    def parse_earthquake_line(self, line):
        """Tek bir deprem satırını parse et"""
        try:
            # Boş satırları atla
            if not line.strip():
                return None
            
            # Kandilli formatı:
            # 2024.08.20 14:30:15 39.1234  27.5678  8.7 -.- 4.2 -.- IZMIR-SEFERIHISAR (AEGEAN SEA)
            
            parts = line.split()
            if len(parts) < 8:
                return None
            
            # Tarih ve saat
            date_str = parts[0]  # 2024.08.20
            time_str = parts[1]  # 14:30:15
            
            # Koordinatlar
            latitude = float(parts[2])
            longitude = float(parts[3])
            
            # Derinlik
            depth = float(parts[4])
            
            # Büyüklük (genellikle 6. sütun)
            magnitude = None
            for i in range(5, len(parts)):
                try:
                    mag_candidate = float(parts[i])
                    if 0.1 <= mag_candidate <= 10.0:  # Mantıklı büyüklük aralığı
                        magnitude = mag_candidate
                        location_start_index = i + 2  # Büyüklükten 2 sütun sonra konum
                        break
                except:
                    continue
            
            if magnitude is None:
                return None
            
            # Konum (geri kalan kısım)
            if location_start_index < len(parts):
                location_parts = parts[location_start_index:]
                location = ' '.join(location_parts)
                # Parantez içindeki kısmı temizle
                location = re.sub(r'\([^)]*\)', '', location).strip()
                # Çoklu boşlukları tek boşluğa çevir
                location = re.sub(r'\s+', ' ', location)
            else:
                location = "Bilinmeyen Konum"
            
            # Tarih/saat formatını düzenle
            datetime_str = f"{date_str} {time_str}"
            earthquake_time = datetime.strptime(datetime_str, "%Y.%m.%d %H:%M:%S")
            
            # Unique ID oluştur (tarih+konum+büyüklük kombinasyonu)
            kandilli_id = f"{earthquake_time.strftime('%Y%m%d_%H%M%S')}_{latitude:.3f}_{longitude:.3f}_{magnitude}"
            
            return {
                'magnitude': magnitude,
                'location': location,
                'depth': depth,
                'earthquake_time': earthquake_time,
                'latitude': latitude,
                'longitude': longitude,
                'kandilli_id': kandilli_id
            }
            
        except Exception as e:
            logger.debug(f"Satır parse edilemedi: {line[:50]}... - Hata: {e}")
            return None
    
    def filter_significant_earthquakes(self, earthquakes, min_magnitude=4.0):
        """Belirli büyüklük ve üstündeki depremleri filtrele"""
        significant = [eq for eq in earthquakes if eq['magnitude'] >= min_magnitude]
        logger.info(f"{min_magnitude}+ büyüklüğünde {len(significant)} deprem bulundu")
        return significant

# Test fonksiyonu
if __name__ == "__main__":
    scraper = KandilliScraper()
    earthquakes = scraper.get_latest_earthquakes()
    
    print(f"Toplam deprem sayısı: {len(earthquakes)}")
    
    # 4.0+ büyüklükteki depremleri göster
    significant = scraper.filter_significant_earthquakes(earthquakes, 4.0)
    
    print(f"\n4.0+ büyüklükteki depremler:")
    for eq in significant[:5]:  # İlk 5'ini göster
        print(f"Büyüklük: {eq['magnitude']}, Konum: {eq['location']}, Zaman: {eq['earthquake_time']}")