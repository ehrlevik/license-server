import json
import sys
from datetime import datetime

def load_licenses():
    """Ładuje licencje z pliku"""
    try:
        with open('licenses.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def verify_license(license_key):
    """Weryfikuje licencję"""
    licenses = load_licenses()
    license_data = next((l for l in licenses if l['key'] == license_key), None)
    
    if not license_data:
        print("❌ LICENCJA NIE ZNALEZIONA")
        return False
    
    if license_data.get('status') == 'deactivated':
        print("🚫 LICENCJA DEZAKTYWOWANA")
        print("📞 Skontaktuj się ze sprzedawcą")
        print(f"🔑 Numer licencji: {license_key}")
        return False
    
    expiration_date = datetime.strptime(license_data['expirationDate'], '%Y-%m-%d')
    if expiration_date < datetime.now() and license_data.get('type') != 'lifetime':
        print("⚠️ LICENCJA WYGASŁA")
        print(f"📅 Data wygaśnięcia: {license_data['expirationDate']}")
        return False
    
    print("✅ LICENCJA POPRAWNA")
    print(f"📦 Produkt: {license_data['product']}")
    print(f"👤 Klient: {license_data['customer']}")
    print(f"📅 Ważna do: {license_data['expirationDate']}")
    return True

def main():
    print("=" * 50)
    print("🛡️ SYSTEM WERYFIKACJI LICENCJI")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        license_key = sys.argv[1]
    else:
        license_key = input("🔑 Wprowadź klucz licencji: ")
    
    verify_license(license_key)

if __name__ == "__main__":
    main()
