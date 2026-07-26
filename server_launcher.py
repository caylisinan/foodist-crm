"""
Foodist Hosted Buyer CRM — SUNUCU Başlatıcı.

Bu program backend'i (veritabanı + API + web arayüzü) çalıştırır.
Ekibin ortak veriye erişebilmesi için bu programın TEK BİR bilgisayarda
sürekli açık kalması yeterlidir. Diğer herkes kendi bilgisayarındaki
tarayıcıdan (Chrome/Edge) bu bilgisayarın adresine girer — hiçbir kurulum,
hiçbir ek program gerekmez.

Bu pencere kapatılırsa, ona bağlı hiç kimse veriye erişemez.
"""
import os
import sys
import socket

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(THIS_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

PORT = 8000


def get_local_ip() -> str:
    """Bu bilgisayarın yerel ağdaki IP adresini bulur (internet bağlantısı
    gerekmez, sadece işletim sisteminin yönlendirme tablosunu kullanır)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def main():
    import uvicorn
    from app.main import app as backend_app

    local_ip = get_local_ip()
    print("=" * 64)
    print("  FOODIST HOSTED BUYER CRM — SUNUCU ÇALIŞIYOR")
    print("=" * 64)
    print()
    print("  Bu bilgisayardan kullanmak için tarayıcıda:")
    print(f"      http://127.0.0.1:{PORT}")
    print()
    print("  Aynı ağdaki DİĞER bilgisayarlardan (kurulum gerekmez,")
    print("  sadece tarayıcı yeterli) kullanmak için:")
    print(f"      http://{local_ip}:{PORT}")
    print()
    print("  Bu pencereyi KAPATMAYIN — kapatırsanız kimse veriye")
    print("  erişemez. Bilgisayarı uyku moduna almayın.")
    print("=" * 64)
    print()

    uvicorn.run(backend_app, host="0.0.0.0", port=PORT, log_level="info")


if __name__ == "__main__":
    main()

