# 🔑 MakePlus API - Fresh Test Credentials

**Database Last Reset:** November 19, 2025  
**Default Password for ALL users:** `makeplus2025`

---

## 🎯 Quick Login for Testing

| Purpose | Username | Full Name | Email | Password |
|---------|----------|-----------|-------|----------|
| **Organizer** | `tech_organisateur` | Ahmed Benali | ahmed.benali@techsummit.dz | makeplus2025 |
| **Controller** | `tech_controleur` | Amina Bouzid | amina.bouzid@techsummit.dz | makeplus2025 |
| **Participant** | `tech_participant1` | Karim Meziane | karim.meziane@gmail.com | makeplus2025 |
| **Exhibitor** | `tech_exposant1` | Yacine Belkacem | yacine.belkacem@innovtech.dz | makeplus2025 |

---

## 📅 Event 1: TechSummit Algeria 2025

### Users & Credentials

| Role | Username | Full Name | Email | Badge ID |
|------|----------|-----------|-------|----------|
| 👔 Organisateur | tech_organisateur | Ahmed Benali | ahmed.benali@techsummit.dz | - |
| 🎫 Contrôleur | tech_controleur | Amina Bouzid | amina.bouzid@techsummit.dz | - |
| 👤 Participant | tech_participant1 | Karim Meziane | karim.meziane@gmail.com | TECH-29A781A2 |
| 👤 Participant | tech_participant2 | Sarah Hassani | sarah.hassani@outlook.com | TECH-877D2F01 |
| 🏢 Exposant | tech_exposant1 | Yacine Belkacem | yacine.belkacem@innovtech.dz | TECH-FA0592E0 |
| 🏢 Exposant | tech_exposant2 | Fatima Zerhouni | fatima.zerhouni@algsoft.dz | TECH-ABF91206 |

---

## 📅 Event 2: StartupWeek Oran 2025

### Users & Credentials

| Role | Username | Full Name | Email | Badge ID |
|------|----------|-----------|-------|----------|
| 👔 Organisateur | startup_organisateur | Mohamed Brahimi | mohamed.brahimi@startupweek.dz | - |
| 🎫 Contrôleur | startup_controleur | Leila Madani | leila.madani@startupweek.dz | - |
| 👤 Participant | startup_participant1 | Rania Khelifa | rania.khelifa@yahoo.fr | STARTUP-C199DB8A |
| 👤 Participant | startup_participant2 | Nassim Sahraoui | nassim.sahraoui@gmail.com | STARTUP-2C1B4E35 |
| 🏢 Exposant | startup_exposant1 | Sophia Boumediene | sophia.boumediene@startuplab.dz | STARTUP-82ABCAE1 |
| 🏢 Exposant | startup_exposant2 | Malik Cherif | malik.cherif@techventures.dz | STARTUP-3C695CB9 |

---

## 📅 Event 3: InnoFest Constantine 2025

### Users & Credentials

| Role | Username | Full Name | Email | Badge ID |
|------|----------|-----------|-------|----------|
| 👔 Organisateur | inno_organisateur | Salah Hamidi | salah.hamidi@innofest.dz | - |
| 🎫 Contrôleur | inno_controleur | Nadia Amrani | nadia.amrani@innofest.dz | - |
| 👤 Participant | inno_participant1 | Mehdi Boudjemaa | mehdi.boudjemaa@gmail.com | INNO-BA47AEC3 |
| 👤 Participant | inno_participant2 | Lynda Benabdallah | lynda.benabdallah@hotmail.com | INNO-BD91AE8B |
| 🏢 Exposant | inno_exposant1 | Redha Kaddour | redha.kaddour@innovcorp.dz | INNO-D833B384 |
| 🏢 Exposant | inno_exposant2 | Samira Bouazza | samira.bouazza@creativetech.dz | INNO-9ADFAE2A |

---

## 🧪 Quick Testing

### Swagger UI Login
1. Go to: `http://127.0.0.1:8000/swagger/`
2. POST `/api/auth/login/`
3. Body:
```json
{
  "username": "tech_organisateur",
  "password": "makeplus2025"
}
```
**User:** Ahmed Benali (Organisateur, TechSummit Algeria 2025)

### cURL Test
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "tech_organisateur", "password": "makeplus2025"}'
```

### Test Different Roles
```json
// Organisateur (Full Control)
{"username": "tech_organisateur", "password": "makeplus2025"}
// Ahmed Benali - Can manage entire event

// Contrôleur des Badges (QR Scanner)  
{"username": "tech_controleur", "password": "makeplus2025"}
// Amina Bouzid - Can verify badges and grant access

// Participant (Attendee)
{"username": "tech_participant1", "password": "makeplus2025"}
// Karim Meziane - Has badge TECH-29A781A2

// Exposant (Exhibitor)
{"username": "tech_exposant1", "password": "makeplus2025"}
// Yacine Belkacem - Has badge TECH-FA0592E0
```

---

## 🔄 Management Commands

### Reset Database
```bash
python manage.py reset_everything --confirm
```

### Create Test Data
```bash
python manage.py create_multi_event_data
```

---

**Password for ALL users:** `makeplus2025`
