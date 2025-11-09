from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Plik do przechowywania licencji
LICENSE_FILE = 'licenses.json'

def load_licenses():
    """Ładuje licencje z pliku JSON"""
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_licenses(licenses):
    """Zapisuje licencje do pliku JSON"""
    try:
        with open(LICENSE_FILE, 'w', encoding='utf-8') as f:
            json.dump(licenses, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

class LicenseHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Obsługa żądań GET"""
        parsed_path = urlparse(self.path)
        
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if parsed_path.path == '/api/licenses':
            # Zwróć wszystkie licencje
            licenses = load_licenses()
            self.wfile.write(json.dumps(licenses).encode('utf-8'))
            
        elif parsed_path.path.startswith('/api/verify/'):
            # Weryfikuj licencję
            license_key = parsed_path.path.split('/')[-1]
            response = self.verify_license(license_key)
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Obsługa żądań OPTIONS dla CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Obsługa żądań POST"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/licenses':
            # Dodaj nową licencję
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                new_license = json.loads(post_data.decode('utf-8'))
                
                licenses = load_licenses()
                
                # Sprawdź czy klucz już istnieje
                if any(l.get('key') == new_license.get('key') for l in licenses):
                    response = {'error': 'Klucz licencji już istnieje'}
                    self.send_response(400)
                else:
                    licenses.append(new_license)
                    if save_licenses(licenses):
                        response = {'message': 'Licencja dodana pomyślnie'}
                        self.send_response(201)
                    else:
                        response = {'error': 'Błąd zapisu licencji'}
                        self.send_response(500)
            except Exception as e:
                response = {'error': f'Błąd przetwarzania: {str(e)}'}
                self.send_response(400)
            
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def verify_license(self, license_key):
        """Weryfikuje licencję"""
        licenses = load_licenses()
        
        # Znajdź licencję
        license_data = None
        for l in licenses:
            if l.get('key') == license_key:
                license_data = l
                break
        
        if not license_data:
            return {
                'valid': False,
                'message': 'Licencja nie znaleziona w systemie'
            }
        
        # Sprawdź status
        if license_data.get('status') == 'deactivated':
            return {
                'valid': False,
                'message': 'LICENCJA DEZAKTYWOWANA. Skontaktuj się ze sprzedawcą.',
                'license_key': license_key,
                'product': license_data.get('product', 'Nieznany'),
                'customer': license_data.get('customer', 'Nieznany'),
                'status': 'deactivated'
            }
        
        # Sprawdź datę wygaśnięcia
        expiration_date_str = license_data.get('expirationDate', '')
        license_type = license_data.get('type', '')
        
        if license_type != 'lifetime' and expiration_date_str:
            try:
                expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d')
                if expiration_date < datetime.now():
                    return {
                        'valid': False,
                        'message': 'Licencja wygasła',
                        'expiration_date': expiration_date_str,
                        'product': license_data.get('product', 'Nieznany')
                    }
            except ValueError:
                # Błąd w formacie daty
                pass
        
        # Licencja poprawna
        return {
            'valid': True,
            'message': 'Licencja poprawna',
            'product': license_data.get('product', 'Nieznany'),
            'customer': license_data.get('customer', 'Nieznany'),
            'email': license_data.get('email', ''),
            'type': license_type,
            'expiration_date': expiration_date_str,
            'issue_date': license_data.get('issueDate', ''),
            'seats': license_data.get('count', 1),
            'status': license_data.get('status', 'active')
        }
    
    def log_message(self, format, *args):
        """Wycisza logi"""
        pass

def run_server():
    """Uruchamia serwer"""
    try:
        server = HTTPServer(('localhost', 5000), LicenseHandler)
        print("=" * 60)
        print("🚀 SERWER LICENCJI URUCHOMIONY")
        print("=" * 60)
        print("📡 Adres: http://localhost:5000")
        print("🔗 Dostępne endpointy:")
        print("   GET  /api/verify/<klucz>  - Weryfikuj licencję")
        print("   GET  /api/licenses        - Pobierz wszystkie licencje")
        print("   POST /api/licenses        - Dodaj nową licencję")
        print("")
        print("⏹️  Naciśnij Ctrl+C aby zatrzymać serwer")
        print("=" * 60)
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Zatrzymywanie serwera...")
        server.server_close()
    except Exception as e:
        print(f"❌ Błąd uruchamiania serwera: {e}")
        print("💡 Sprawdź czy port 5000 nie jest zajęty")

if __name__ == '__main__':
    # Utwórz plik licencji jeśli nie istnieje
    if not os.path.exists(LICENSE_FILE):
        sample_licenses = []
        with open(LICENSE_FILE, 'w', encoding='utf-8') as f:
            json.dump(sample_licenses, f, ensure_ascii=False, indent=2)
        print("📁 Utworzono nowy plik licencji")
    
    run_server()
