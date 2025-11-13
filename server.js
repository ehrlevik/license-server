const express = require('express');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const app = express();
const port = 3000;

app.use(express.json());
app.use(express.static('public'));

// Plik do przechowywania licencji
const LICENSES_FILE = path.join(__dirname, 'licenses.json');

// Funkcja do generowania losowego klucza licencji
function generateLicenseKey() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 16; i++) {
        if (i > 0 && i % 4 === 0) result += '-';
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// Funkcja do wczytania licencji
function loadLicenses() {
    try {
        if (fs.existsSync(LICENSES_FILE)) {
            return JSON.parse(fs.readFileSync(LICENSES_FILE, 'utf8'));
        }
    } catch (error) {
        console.error('Błąd wczytywania licencji:', error);
    }
    return [];
}

// Funkcja do zapisania licencji
function saveLicenses(licenses) {
    try {
        fs.writeFileSync(LICENSES_FILE, JSON.stringify(licenses, null, 2));
        return true;
    } catch (error) {
        console.error('Błąd zapisywania licencji:', error);
        return false;
    }
}

// API - Pobierz wszystkie licencje
app.get('/api/licenses', (req, res) => {
    const licenses = loadLicenses();
    res.json(licenses);
});

// API - Utwórz nową licencję
app.post('/api/licenses', (req, res) => {
    const { type, days, customer_name, customer_email } = req.body;
    
    if (!type || !days || !customer_name || !customer_email) {
        return res.json({ success: false, error: 'Wszystkie pola są wymagane' });
    }
    
    const licenses = loadLicenses();
    const license_key = generateLicenseKey();
    
    const newLicense = {
        license_key,
        type,
        days: parseInt(days),
        customer_name,
        customer_email,
        active: true,
        created_at: new Date().toISOString(),
        activated_at: null,
        last_check: null,
        deactivation_reason: null
    };
    
    licenses.push(newLicense);
    
    if (saveLicenses(licenses)) {
        res.json({ success: true, license_key });
    } else {
        res.json({ success: false, error: 'Błąd zapisywania licencji' });
    }
});

// API - Sprawdź licencję (dla bota)
app.get('/api/check-license/:licenseKey', (req, res) => {
    const { licenseKey } = req.params;
    const licenses = loadLicenses();
    
    const license = licenses.find(l => l.license_key === licenseKey);
    
    if (!license) {
        return res.json({ 
            valid: false, 
            error: 'Nieprawidłowy klucz licencji' 
        });
    }
    
    if (!license.active) {
        return res.json({ 
            valid: false, 
            error: 'Licencja jest dezaktywowana',
            reason: license.deactivation_reason
        });
    }
    
    // Sprawdź czy licencja lifetime
    if (license.days === 9999) {
        // Lifetime - zawsze ważna
        license.last_check = new Date().toISOString();
        saveLicenses(licenses);
        
        return res.json({ 
            valid: true,
            type: license.type,
            days: license.days,
            customer_name: license.customer_name
        });
    }
    
    // Sprawdź datę wygaśnięcia dla licencji czasowych
    const createdDate = new Date(license.created_at);
    const expirationDate = new Date(createdDate);
    expirationDate.setDate(expirationDate.getDate() + license.days);
    const now = new Date();
    
    if (now > expirationDate) {
        return res.json({ 
            valid: false, 
            error: 'Licencja wygasła' 
        });
    }
    
    // Aktualizuj ostatnie sprawdzenie
    license.last_check = new Date().toISOString();
    if (!license.activated_at) {
        license.activated_at = new Date().toISOString();
    }
    saveLicenses(licenses);
    
    const remainingDays = Math.ceil((expirationDate - now) / (1000 * 60 * 60 * 24));
    
    res.json({ 
        valid: true,
        type: license.type,
        days: license.days,
        remaining_days: remainingDays,
        customer_name: license.customer_name,
        expires_at: expirationDate.toISOString()
    });
});

// API - Dezaktywuj licencję
app.post('/api/licenses/:licenseKey/deactivate', (req, res) => {
    const { licenseKey } = req.params;
    const { reason } = req.body;
    
    const licenses = loadLicenses();
    const license = licenses.find(l => l.license_key === licenseKey);
    
    if (!license) {
        return res.json({ success: false, error: 'Licencja nie znaleziona' });
    }
    
    license.active = false;
    license.deactivation_reason = reason || 'Dezaktywowana przez administratora';
    
    if (saveLicenses(licenses)) {
        res.json({ success: true });
    } else {
        res.json({ success: false, error: 'Błąd zapisywania' });
    }
});

// API - Aktywuj licencję
app.post('/api/licenses/:licenseKey/activate', (req, res) => {
    const { licenseKey } = req.params;
    
    const licenses = loadLicenses();
    const license = licenses.find(l => l.license_key === licenseKey);
    
    if (!license) {
        return res.json({ success: false, error: 'Licencja nie znaleziona' });
    }
    
    license.active = true;
    license.deactivation_reason = null;
    
    if (saveLicenses(licenses)) {
        res.json({ success: true });
    } else {
        res.json({ success: false, error: 'Błąd zapisywania' });
    }
});

// API - Usuń licencję
app.delete('/api/licenses/:licenseKey', (req, res) => {
    const { licenseKey } = req.params;
    
    let licenses = loadLicenses();
    const initialLength = licenses.length;
    licenses = licenses.filter(l => l.license_key !== licenseKey);
    
    if (licenses.length === initialLength) {
        return res.json({ success: false, error: 'Licencja nie znaleziona' });
    }
    
    if (saveLicenses(licenses)) {
        res.json({ success: true });
    } else {
        res.json({ success: false, error: 'Błąd zapisywania' });
    }
});

// Strona główna
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, () => {
    console.log(`🚀 Serwer licencji uruchomiony na http://localhost:${port}`);
    console.log(`📁 Plik licencji: ${LICENSES_FILE}`);
});
