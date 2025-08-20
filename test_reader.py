import os

print("--- Dosya Okuma Testi Başladı ---")

try:
    # Bu script'in çalıştığı klasörün tam yolunu al
    # Örnek: C:\Users\Kullanici\Desktop\deprem-instagram-bot
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script'in bulunduğu klasör: {script_dir}")

    # .env dosyasının olması gereken tam yolu oluştur
    env_file_path = os.path.join(script_dir, '.env')
    print(f".env dosyasının olması gereken tam yol: {env_file_path}")

    # Python'a bu yolda bir dosya olup olmadığını sordur
    if os.path.exists(env_file_path):
        print("✅ Harika! Python, .env dosyasını bu yolda buldu.")
        
        # Şimdi dosyayı açıp içeriğini okumayı dene
        print("Dosya içeriği okunuyor...")
        with open(env_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n--- OKUNAN DOSYA İÇERİĞİ ---")
        print(content)
        print("--- İÇERİK SONU ---\n")

        # İçeriğin doğru olup olmadığını kontrol et
        if "SUPABASE_URL" in content and content.strip() != "":
            print("✅ BAŞARILI! Dosyanın içeriği okundu ve 'SUPABASE_URL' metni içinde bulundu.")
        else:
            print("❌ HATA: Dosya okundu ama ya boş ya da içinde 'SUPABASE_URL' bulunamadı.")

    else:
        print("❌ KRİTİK HATA: Python, .env dosyasını belirtilen yolda BULAMADI!")
        print("Lütfen dosya adının ve konumunun doğru olduğundan emin ol.")

except Exception as e:
    print(f"!!! BEKLENMEDİK BİR HATA OLUŞTU: {e}")