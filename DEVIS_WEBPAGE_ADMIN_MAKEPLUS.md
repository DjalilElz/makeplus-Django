# DEVIS DÉTAILLÉ - PARTIE WEB ADMIN MAKEPLUS
## Plateforme d'Administration Web pour Gestion d'Événements

**Date:** 27 Janvier 2026  
**Projet:** MakePlus - Interface Web d'Administration & API Backend  
**Type:** Développement Backend Django + Dashboard Web Admin  
**Exclusion:** Application mobile (Flutter) - Non inclus dans ce devis

---

## 📋 RÉSUMÉ EXÉCUTIF

Développement complet d'une plateforme web d'administration pour la gestion d'événements professionnels multi-rôles avec système de badges QR, contrôle d'accès, système de caisse, et API REST complète pour intégration mobile future.

### Technologies Utilisées
- **Backend:** Django 5.2.7 + Django REST Framework
- **Base de données:** PostgreSQL (production) / SQLite (développement)
- **Authentification:** JWT (JSON Web Tokens) + Django Sessions
- **Documentation API:** Swagger/OpenAPI (drf-yasg)
- **Frontend Admin:** Django Templates + Bootstrap 5.3
- **Génération QR:** Python qrcode + Pillow
- **Hébergement:** Compatible VPS/Cloud (AWS, Azure, etc.)

---

## 🎯 PARTIE 1: API REST BACKEND

### 1.1 API d'Authentification

#### Endpoints Développés:
- `POST /api/auth/register/` - Inscription utilisateur
- `POST /api/auth/login/` - Connexion utilisateur (retourne JWT)
- `POST /api/auth/logout/` - Déconnexion
- `GET /api/auth/profile/` - Profil utilisateur
- `GET /api/auth/me/` - Informations utilisateur (alias Flutter)
- `PUT /api/auth/change-password/` - Changement mot de passe
- `POST /api/auth/token/` - Obtenir JWT token
- `POST /api/auth/token/refresh/` - Rafraîchir JWT token
- `POST /api/auth/token/verify/` - Vérifier JWT token

#### Fonctionnalités:
✅ **Système JWT complet**
- Génération access token + refresh token
- Expiration configurable (access: 1h, refresh: 7 jours)
- Token inclut: user_id, event_id, role
- Validation automatique sur chaque requête

✅ **Gestion multi-événements**
- `POST /api/auth/select-event/` - Sélection événement au login
- `POST /api/auth/switch-event/` - Changement d'événement
- `GET /api/auth/my-events/` - Liste événements de l'utilisateur
- Un utilisateur peut avoir différents rôles dans différents événements

✅ **Sécurité**
- Hash des mots de passe (PBKDF2)
- CORS configuré pour web/mobile
- Protection CSRF pour sessions web
- Rate limiting (optionnel)

**Temps de développement:** ~20 heures  
**Nombre d'endpoints:** 13

---

### 1.2 API Gestion des Événements

#### Endpoints REST (ViewSet):
- `GET /api/events/` - Liste des événements
- `POST /api/events/` - Créer événement
- `GET /api/events/{id}/` - Détail événement
- `PUT /api/events/{id}/` - Modifier événement
- `PATCH /api/events/{id}/` - Modification partielle
- `DELETE /api/events/{id}/` - Supprimer événement
- `GET /api/events/{id}/stats/` - Statistiques événement

#### Modèle de données Event:
```python
- id (UUID)
- name (string, 200 chars)
- description (texte)
- start_date (datetime)
- end_date (datetime)
- location (string, 200 chars)
- location_details (texte)
- status (upcoming/active/completed/cancelled)
- logo (image upload)
- banner (image upload)
- programme_file (PDF upload)
- guide_file (PDF upload)
- themes (JSON array)
- settings (JSON object)
- total_participants (integer)
- total_exhibitors (integer)
- total_rooms (integer)
- organizer_contact (email)
- metadata (JSON)
- president (FK User)
- created_by (FK User)
- created_at (datetime)
- updated_at (datetime)
```

#### Fonctionnalités API:
✅ **Upload de fichiers**
- Logo événement (images)
- Bannière événement (images)
- Programme PDF (schedule/agenda)
- Guide participant PDF (handbook)
- Stockage optimisé avec organisation par dossiers
- Support multipart/form-data

✅ **Filtres et recherche**
- Filtrer par status (upcoming, active, completed)
- Recherche par nom, lieu
- Tri par date de début
- Pagination (10, 25, 50 résultats par page)

✅ **Permissions**
- Lecture publique (liste et détail)
- Création/Modification: Organisateur ou Admin
- Suppression: Admin uniquement

**Temps de développement:** ~35 heures  
**Nombre d'endpoints:** 7 + 1 custom

---

### 1.3 API Gestion des Salles (Rooms)

#### Endpoints REST (ViewSet):
- `GET /api/rooms/` - Liste des salles
- `POST /api/rooms/` - Créer salle
- `GET /api/rooms/{id}/` - Détail salle
- `PUT /api/rooms/{id}/` - Modifier salle
- `DELETE /api/rooms/{id}/` - Supprimer salle
- `GET /api/rooms/{id}/current-status/` - Statut actuel (occupancy)
- `GET /api/rooms/{id}/sessions/` - Sessions de la salle

#### Modèle de données Room:
```python
- id (UUID)
- event (FK Event)
- name (string, 100 chars)
- description (texte)
- capacity (integer)
- location (string, 200 chars)
- current_participants (integer)
- is_active (boolean)
- created_by (FK User)
- created_at (datetime)
- updated_at (datetime)
```

#### Fonctionnalités:
✅ Calcul automatique du taux d'occupation
✅ Gestion des contraintes (capacité maximale)
✅ Filtrage par événement
✅ Unicité nom par événement

**Temps de développement:** ~15 heures  
**Nombre d'endpoints:** 7

---

### 1.4 API Gestion des Sessions

#### Endpoints REST (ViewSet):
- `GET /api/sessions/` - Liste des sessions
- `POST /api/sessions/` - Créer session
- `GET /api/sessions/{id}/` - Détail session
- `PUT /api/sessions/{id}/` - Modifier session
- `DELETE /api/sessions/{id}/` - Supprimer session
- `POST /api/sessions/{id}/register/` - Inscription participant
- `POST /api/sessions/{id}/unregister/` - Désinscrire participant
- `POST /api/sessions/{id}/mark_live/` - Marquer session en cours
- `POST /api/sessions/{id}/mark_completed/` - Marquer session terminée
- `GET /api/sessions/{id}/participants/` - Liste participants inscrits
- `GET /api/sessions/{id}/questions/` - Questions de la session

#### Modèle de données Session:
```python
- id (UUID)
- event (FK Event)
- room (FK Room)
- title (string, 200 chars)
- description (texte)
- start_time (datetime)
- end_time (datetime)
- speaker_name (string, 100 chars)
- speaker_title (string, 100 chars)
- speaker_bio (texte)
- speaker_photo_url (URL)
- theme (string, 100 chars)
- session_type (conference/atelier/communication/table_ronde/lunch_symposium/symposium/session_photo)
- status (pas_encore/en_cours/termine)
- is_paid (boolean)
- price (decimal 10,2)
- youtube_live_url (URL)
- cover_image_url (URL)
- metadata (JSON)
- created_by (FK User)
- created_at (datetime)
- updated_at (datetime)
```

#### Fonctionnalités:
✅ **Gestion du cycle de vie**
- Statuts: Pas encore / En cours / Terminé
- Actions custom: start(), end()
- Calcul automatique de la durée

✅ **Système d'ateliers payants**
- Sessions gratuites vs payantes
- Prix en DZD
- Vérification paiement avant accès

✅ **Intégration YouTube Live**
- URL de streaming en direct
- Support événements hybrides

✅ **Système Q&A**
- Participants posent questions
- Gestionnaires répondent
- Endpoint dédié pour questions

**Temps de développement:** ~30 heures  
**Nombre d'endpoints:** 11

---

### 1.5 API Participants & Badges QR

#### Endpoints:
- `GET /api/participants/` - Liste participants
- `POST /api/participants/` - Créer participant
- `GET /api/participants/{id}/` - Détail participant
- `PUT /api/participants/{id}/` - Modifier participant
- `DELETE /api/participants/{id}/` - Supprimer participant
- `GET /api/participants/{id}/badge/` - QR code du participant
- `POST /api/qr/verify/` - Vérifier QR code
- `POST /api/qr/generate/` - Générer QR code

#### Modèle de données Participant:
```python
- user (FK User)
- event (FK Event)
- badge_id (string, 100 chars - unique)
- qr_code_data (texte JSON)
- is_checked_in (boolean)
- checked_in_at (datetime nullable)
- allowed_rooms (M2M Room)
- plan_file (PDF upload - pour exposants)
- metadata (JSON)
- created_at (datetime)
- updated_at (datetime)
```

#### Système QR Code:
✅ **Un QR par utilisateur** (pas par événement)
- Badge ID format: `USER-{user_id}-{hash}`
- QR code fonctionne pour tous les événements de l'utilisateur
- Stocké dans UserProfile (table dédiée)

✅ **Vérification multi-niveaux**
1. **Niveau événement:** Utilisateur assigné à l'événement?
2. **Niveau salle:** Salle dans les salles autorisées?
3. **Niveau session:** Si payante, paiement effectué?

✅ **Génération automatique**
- Création lors de l'assignation à un événement
- Image PNG téléchargeable
- Format: 300x300 pixels, haute qualité

**Temps de développement:** ~25 heures  
**Nombre d'endpoints:** 8

---

### 1.6 API Contrôle d'Accès

#### Endpoints Room Access:
- `GET /api/room-access/` - Historique accès salles
- `POST /api/room-access/` - Enregistrer accès salle
- `GET /api/room-access/{id}/` - Détail accès
- `GET /api/room-access/recent/` - Accès récents

#### Endpoints Session Access:
- `GET /api/session-access/` - Accès sessions
- `POST /api/session-access/` - Enregistrer accès session
- `GET /api/session-access/{id}/` - Détail accès session

#### Modèles:
```python
RoomAccess:
- participant (FK Participant)
- room (FK Room)
- session (FK Session, nullable)
- accessed_at (datetime)
- verified_by (FK User - contrôleur)
- status (granted/denied)
- denial_reason (texte)

SessionAccess:
- participant (FK Participant)
- session (FK Session)
- payment_status (free/paid/pending)
- payment_amount (decimal)
- payment_date (datetime)
- access_granted (boolean)
- created_at (datetime)
```

#### Fonctionnalités:
✅ Enregistrement de tous les check-ins
✅ Historique par participant
✅ Statistiques par salle
✅ Traçabilité des contrôleurs
✅ Raisons de refus

**Temps de développement:** ~18 heures  
**Nombre d'endpoints:** 7

---

### 1.7 API Assignations Utilisateurs

#### Endpoints:
- `GET /api/user-assignments/` - Liste assignations
- `POST /api/user-assignments/` - Créer assignation
- `GET /api/user-assignments/{id}/` - Détail assignation
- `PUT /api/user-assignments/{id}/` - Modifier assignation (changement rôle)
- `DELETE /api/user-assignments/{id}/` - Supprimer assignation
- `GET /api/user-assignments/by-event/{event_id}/` - Assignations par événement
- `GET /api/user-assignments/by-role/{role}/` - Assignations par rôle

#### Modèle UserEventAssignment:
```python
- user (FK User)
- event (FK Event)
- role (organisateur/gestionnaire_des_salles/controlleur_des_badges/participant/exposant)
- is_active (boolean)
- assigned_at (datetime)
- assigned_by (FK User)
- metadata (JSON - ex: assigned_room_id)
```

#### Système de Rôles:
✅ **Organisateur**
- Gestion complète de l'événement
- Création/modification/suppression

✅ **Gestionnaire des Salles**
- Gestion sessions dans les salles assignées
- Statistiques salle
- Q&A sessions

✅ **Contrôleur des Badges**
- Scan QR codes
- Vérification accès
- Enregistrement check-ins

✅ **Participant**
- Inscription sessions
- Consultation programme
- Q&A questions

✅ **Exposant**
- Scan visiteurs
- Statistiques booth
- Plan du salon (PDF)

**Temps de développement:** ~12 heures  
**Nombre d'endpoints:** 7

---

### 1.8 API Annonces

#### Endpoints:
- `GET /api/annonces/` - Liste annonces
- `POST /api/annonces/` - Créer annonce
- `GET /api/annonces/{id}/` - Détail annonce
- `PUT /api/annonces/{id}/` - Modifier annonce
- `DELETE /api/annonces/{id}/` - Supprimer annonce
- `GET /api/annonces/for-me/` - Annonces pour l'utilisateur connecté

#### Modèle Annonce:
```python
- event (FK Event)
- title (string, 200 chars)
- content (texte)
- target_roles (JSON array)
- is_active (boolean)
- priority (low/normal/high/urgent)
- published_at (datetime)
- expires_at (datetime nullable)
- created_by (FK User)
- created_at (datetime)
- updated_at (datetime)
```

#### Fonctionnalités:
✅ Ciblage par rôles (tous, participants, exposants, etc.)
✅ Niveaux de priorité
✅ Expiration automatique
✅ Filtrage par utilisateur connecté

**Temps de développement:** ~10 heures  
**Nombre d'endpoints:** 6

---

### 1.9 API Questions & Réponses Sessions

#### Endpoints:
- `GET /api/session-questions/` - Liste questions
- `POST /api/session-questions/` - Poser question
- `GET /api/session-questions/{id}/` - Détail question
- `DELETE /api/session-questions/{id}/` - Supprimer question
- `POST /api/session-questions/{id}/answer/` - Répondre (gestionnaire)
- `GET /api/session-questions/by-session/{session_id}/` - Questions par session

#### Modèle SessionQuestion:
```python
- session (FK Session)
- asked_by (FK User)
- question_text (texte)
- answer_text (texte nullable)
- answered_by (FK User nullable)
- answered_at (datetime nullable)
- is_answered (boolean)
- is_approved (boolean)
- created_at (datetime)
- updated_at (datetime)
```

#### Fonctionnalités:
✅ Participants posent questions pendant sessions
✅ Gestionnaires approuvent et répondent
✅ Tri par date
✅ Filtres: répondu/non répondu

**Temps de développement:** ~12 heures  
**Nombre d'endpoints:** 6

---

### 1.10 API Assignations Salles (Room Assignments)

#### Endpoints:
- `GET /api/room-assignments/` - Liste assignations salles
- `POST /api/room-assignments/` - Assigner gestionnaire à salle
- `GET /api/room-assignments/{id}/` - Détail assignation
- `PUT /api/room-assignments/{id}/` - Modifier assignation
- `DELETE /api/room-assignments/{id}/` - Supprimer assignation

#### Modèle RoomAssignment:
```python
- user (FK User - gestionnaire)
- room (FK Room)
- start_time (datetime)
- end_time (datetime)
- is_active (boolean)
- notes (texte)
- assigned_by (FK User)
- created_at (datetime)
```

#### Fonctionnalités:
✅ Gestionnaires assignés à des salles spécifiques
✅ Créneaux horaires
✅ Permissions selon assignation

**Temps de développement:** ~8 heures  
**Nombre d'endpoints:** 5

---

### 1.11 API Scans Exposants

#### Endpoints:
- `GET /api/exposant-scans/` - Historique scans
- `POST /api/exposant-scans/` - Enregistrer scan visiteur
- `GET /api/exposant-scans/{id}/` - Détail scan
- `GET /api/exposant-scans/my-scans/` - Scans de l'exposant connecté
- `GET /api/exposant-scans/stats/` - Statistiques exposant

#### Modèle ExposantScan:
```python
- exposant (FK User)
- participant (FK Participant)
- event (FK Event)
- scanned_at (datetime)
- notes (texte)
- metadata (JSON)
```

#### Fonctionnalités:
✅ Exposants scannent QR des visiteurs
✅ Historique des visites
✅ Statistiques de trafic
✅ Export des contacts

**Temps de développement:** ~10 heures  
**Nombre d'endpoints:** 5

---

### 1.12 API Statistiques

#### Endpoints Dashboard:
- `GET /api/dashboard/stats/` - Statistiques globales
- `GET /api/my-room/statistics/` - Stats salle gestionnaire
- `GET /api/my-ateliers/` - Mes ateliers participant

#### Données retournées:
✅ **Stats globales:**
- Nombre participants total
- Nombre check-ins
- Taux de présence
- Sessions actives
- Salles occupées

✅ **Stats gestionnaire:**
- Sessions de sa salle
- Participants actuels
- Taux d'occupation
- Questions en attente

✅ **Stats participant:**
- Sessions inscrites
- Ateliers payés
- Historique présence

**Temps de développement:** ~15 heures  
**Nombre d'endpoints:** 3

---

### 1.13 Documentation API (Swagger)

#### URLs:
- `GET /swagger/` - Interface Swagger UI
- `GET /redoc/` - Interface ReDoc
- `GET /swagger.json` - Schéma OpenAPI JSON

#### Fonctionnalités:
✅ Documentation auto-générée de tous les endpoints
✅ Interface interactive pour tester l'API
✅ Descriptions des modèles
✅ Exemples de requêtes/réponses
✅ Schémas de validation

**Temps de développement:** ~8 heures  
**Nombre de pages:** 3

---

## 📊 RÉCAPITULATIF API BACKEND

### Nombre total d'endpoints API: **~100 endpoints**

| Module | Endpoints | Temps (h) |
|--------|-----------|-----------|
| Authentication | 13 | 20 |
| Events | 8 | 35 |
| Rooms | 7 | 15 |
| Sessions | 11 | 30 |
| Participants & QR | 8 | 25 |
| Access Control | 7 | 18 |
| User Assignments | 7 | 12 |
| Annonces | 6 | 10 |
| Session Questions | 6 | 12 |
| Room Assignments | 5 | 8 |
| Exposant Scans | 5 | 10 |
| Statistics | 3 | 15 |
| Documentation | 3 | 8 |
| **TOTAL API** | **~100** | **218h** |

---

## 🖥️ PARTIE 2: DASHBOARD WEB ADMIN

### 2.1 Système d'Authentification Web

#### Pages développées:
- `/dashboard/login/` - Page de connexion
- `/dashboard/logout/` - Déconnexion

#### Fonctionnalités:
✅ Interface de connexion sécurisée
✅ Validation formulaire côté client et serveur
✅ Sessions Django
✅ Protection CSRF
✅ Restriction accès (staff uniquement)
✅ Messages flash (succès, erreur)
✅ Redirection après login
✅ Design responsive Bootstrap 5

**Temps de développement:** ~6 heures  
**Nombre de pages:** 2

---

### 2.2 Dashboard Principal (Home)

#### URL:
- `/dashboard/` - Page d'accueil dashboard

#### Sections:
✅ **Cartes statistiques (4 cards):**
- Total événements
- Événements actifs
- Événements à venir
- Événements terminés

✅ **Statistiques secondaires:**
- Total participants
- Total utilisateurs
- Total sessions

✅ **Liste des événements:**
- Tableau avec tous les événements
- Filtrage par statut
- Tri par date
- Recherche par nom
- Actions: Voir détails, Éditer, Supprimer

✅ **Actions rapides:**
- Créer nouvel événement
- Créer utilisateur
- Gérer caisses

#### Design:
- Interface moderne avec Bootstrap 5
- Cards avec icônes Bootstrap Icons
- Couleurs selon statut (vert: actif, bleu: à venir, gris: terminé)
- Responsive design (mobile, tablet, desktop)
- Pagination des résultats

**Temps de développement:** ~12 heures  
**Nombre de templates:** 1 (home.html)

---

### 2.3 Création d'Événement Multi-Étapes

#### URLs:
- `/dashboard/events/create/step1/` - Étape 1: Détails événement
- `/dashboard/events/create/step2/` - Étape 2: Ajout salles
- `/dashboard/events/create/step3/` - Étape 3: Ajout sessions
- `/dashboard/events/create/step4/` - Étape 4: Ajout utilisateurs

#### Wizard de création (4 étapes):

**ÉTAPE 1 - Détails de l'événement:**
✅ Formulaire Django avec validation
- Nom événement (requis)
- Description
- Dates début/fin (requis)
- Lieu (requis)
- Détails lieu
- Statut (upcoming/active/completed/cancelled)
- Upload logo (image)
- Upload bannière (image)
- Email organisateur
- Nombre de salles (requis pour étape 2)
- Métadonnées JSON

✅ Upload de fichiers PDF:
- Programme de l'événement (PDF)
- Guide participant (PDF)

**ÉTAPE 2 - Ajout des salles:**
✅ Formulaire dynamique pour chaque salle
- Barre de progression (Salle X sur Y)
- Nom salle (requis)
- Capacité (requis)
- Description
- Localisation
- Étage
- Type de salle
- Équipements
- Bouton "Ajouter salle & Continuer"

**ÉTAPE 3 - Ajout des sessions:**
✅ Formulaire session par salle
- Sélection salle (dropdown)
- Liste sessions déjà ajoutées (panneau gauche)
- Formulaire session:
  - Titre (requis)
  - Type (Conférence/Atelier/Communication/etc.)
  - Thème
  - Description
  - Horaires début/fin (requis)
  - Intervenant (nom, titre, bio, photo)
  - Capacité max
  - URL YouTube Live
  - Session payante (checkbox)
  - Prix en DZD
- Boutons: "Ajouter session", "Passer salle", "Terminer"

**ÉTAPE 4 - Ajout utilisateurs:**
✅ Formulaire création utilisateur
- Panneau gauche: Utilisateurs déjà créés
- Formulaire:
  - Username (requis)
  - Email (requis)
  - Prénom/Nom (requis)
  - Mot de passe + confirmation (requis)
  - Rôle (dropdown)
- Génération automatique QR code
- Boutons: "Créer utilisateur", "Terminer"

#### Fonctionnalités techniques:
✅ Session storage des données entre étapes
✅ Validation à chaque étape
✅ Possibilité de revenir en arrière
✅ Annulation à tout moment
✅ Messages de confirmation
✅ Redirection vers détails événement après création

**Temps de développement:** ~45 heures  
**Nombre de templates:** 4 (step1.html, step2.html, step3.html, step4.html)

---

### 2.4 Détail d'Événement

#### URL:
- `/dashboard/events/{event_id}/` - Page détail événement

#### Sections avec onglets:

**ONGLET OVERVIEW:**
✅ Informations événement
- Nom, description, lieu
- Dates début/fin
- Statut avec badge coloré
- Contact organisateur
- Logo et bannière
- Liens vers fichiers PDF (programme, guide)

✅ Cartes statistiques (4 cards):
- Participants (total + checked-in)
- Salles (nombre total)
- Sessions (total + par type)
- Exposants (nombre + scans)

**ONGLET SALLES:**
✅ Liste toutes les salles
- Tableau responsive
- Colonnes: Nom, Capacité, Localisation, Étage, Type, Sessions
- Taux d'occupation (barre de progression)
- Actions: Éditer, Supprimer
- Bouton "Ajouter salle"

**ONGLET SESSIONS:**
✅ Liste toutes les sessions
- Tableau responsive
- Colonnes: Titre, Type, Salle, Horaire, Intervenant, Statut
- Badge statut: Pas encore / En cours / Terminé
- Indicateur session payante
- Icône YouTube Live
- Capacité/Inscrits
- Actions: Éditer, Supprimer
- Filtres: Par type, par salle, par statut
- Bouton "Ajouter session"

**ONGLET UTILISATEURS:**
✅ Onglets secondaires par rôle:
- Tous
- Organisateurs
- Gestionnaires
- Contrôleurs
- Exposants

✅ Tableau utilisateurs:
- Photo profil
- Nom complet
- Email
- Badge ID
- Date assignation
- Actions: Voir détails, Changer rôle, Retirer

✅ Compteurs par rôle

**ACTIONS GLOBALES:**
- Bouton "Éditer événement"
- Bouton "Supprimer événement" (confirmation)
- Bouton "Retour à la liste"

#### Design:
✅ Interface tabs Bootstrap
✅ Cards avec statistiques visuelles
✅ Tableaux triables
✅ Badges colorés pour statuts
✅ Icons Bootstrap
✅ Responsive design
✅ Modals de confirmation

**Temps de développement:** ~25 heures  
**Nombre de templates:** 1 (event_detail.html)

---

### 2.5 Édition d'Événement

#### URL:
- `/dashboard/events/{event_id}/edit/` - Page édition événement

#### Fonctionnalités:
✅ Formulaire pré-rempli avec données actuelles
✅ Tous les champs modifiables:
- Informations de base
- Dates
- Lieu
- Statut
- Upload nouveaux fichiers (logo, bannière, PDFs)
- Métadonnées

✅ Gestion fichiers:
- Affichage fichiers actuels
- Option de remplacement
- Suppression fichiers

✅ Validation:
- Côté client (HTML5)
- Côté serveur (Django forms)
- Messages d'erreur contextuels

✅ Actions:
- Bouton "Enregistrer"
- Bouton "Annuler"
- Confirmation avant changements majeurs

**Temps de développement:** ~10 heures  
**Nombre de templates:** 1 (event_edit.html)

---

### 2.6 Suppression d'Événement

#### URL:
- `/dashboard/events/{event_id}/delete/` - Suppression événement

#### Fonctionnalités:
✅ Page de confirmation
✅ Affichage détails événement à supprimer
✅ Avertissement sur suppressions en cascade:
- Toutes les salles
- Toutes les sessions
- Tous les participants (liens)
- Tous les accès
- Toutes les assignations

✅ Options:
- Confirmation requise
- Bouton "Confirmer suppression" (rouge)
- Bouton "Annuler" (retour)

✅ Protection:
- Confirmation par mot "DELETE"
- Message flash de succès
- Redirection vers dashboard

**Temps de développement:** ~4 heures  
**Nombre de templates:** 0 (modal dans event_detail.html)

---

### 2.7 Gestion des Utilisateurs

#### URLs:
- `/dashboard/users/` - Liste utilisateurs
- `/dashboard/users/create/` - Créer utilisateur
- `/dashboard/users/{user_id}/` - Détail utilisateur
- `/dashboard/users/{user_id}/delete/` - Supprimer utilisateur
- `/dashboard/users/{user_id}/qr-code/download/` - Télécharger QR

**PAGE LISTE UTILISATEURS:**
✅ Tableau tous les utilisateurs
- Colonnes: Username, Email, Nom complet, Date création
- Recherche par nom/email
- Tri par colonne
- Pagination (25, 50, 100 par page)
- Actions: Voir détails, Supprimer

✅ Filtres:
- Par rôle
- Par événement
- Staff / Non-staff

✅ Bouton "Créer utilisateur"

**PAGE CRÉATION UTILISATEUR:**
✅ Formulaire Django
- Username (unique, requis)
- Email (unique, requis)
- Prénom (requis)
- Nom (requis)
- Mot de passe + confirmation (requis)
- Sélection événement (dropdown)
- Sélection rôle (dropdown)
- Options: Staff, Superuser

✅ Validation:
- Format email
- Force mot de passe
- Unicité username/email

✅ Actions automatiques:
- Création compte User
- Création UserProfile avec QR code
- Assignation à événement (UserEventAssignment)
- Création Participant (si rôle participant/exposant)

**PAGE DÉTAIL UTILISATEUR:**
✅ Sections:
1. **Informations personnelles:**
   - Photo profil (si disponible)
   - Nom complet
   - Username
   - Email
   - Date création
   - Statut: Actif/Inactif

2. **Badge QR Code:**
   - Affichage QR code (300x300px)
   - Badge ID affiché
   - Bouton "Télécharger QR Code" (PNG)

3. **Assignations événements:**
   - Tableau des événements
   - Colonnes: Événement, Rôle, Date assignation, Statut
   - Badge coloré par rôle
   - Bouton "Changer rôle"

4. **Statistiques:**
   - Nombre d'événements
   - Check-ins effectués
   - Sessions inscrites
   - Scans effectués (si exposant)

✅ Actions:
- Bouton "Éditer utilisateur"
- Bouton "Supprimer utilisateur"
- Bouton "Retour à la liste"

**TÉLÉCHARGEMENT QR CODE:**
✅ Génération image PNG
- Format: 300x300 pixels
- Haute qualité
- Nom fichier: `qr_code_{username}.png`
- Téléchargement direct

**Temps de développement:** ~20 heures  
**Nombre de templates:** 3 (user_list.html, user_create.html, user_detail.html)

---

### 2.8 Gestion Utilisateurs par Événement

#### URLs:
- `/dashboard/events/{event_id}/users/` - Utilisateurs de l'événement
- `/dashboard/events/{event_id}/users/{user_id}/delete/` - Retirer utilisateur
- `/dashboard/assignments/{assignment_id}/change-role/` - Changer rôle

**PAGE UTILISATEURS ÉVÉNEMENT:**
✅ Onglets par rôle:
- Tous
- Organisateurs
- Gestionnaires des Salles
- Contrôleurs des Badges
- Participants
- Exposants

✅ Tableau utilisateurs:
- Photo
- Nom complet
- Email
- Badge ID avec QR icon
- Date assignation
- Actions: Détails, Changer rôle, Retirer

✅ Statistiques par rôle (badges)

✅ Actions:
- Bouton "Ajouter utilisateur existant"
- Bouton "Créer nouvel utilisateur"

**CHANGEMENT DE RÔLE:**
✅ Modal popup
- Utilisateur sélectionné
- Rôle actuel affiché
- Dropdown nouveau rôle
- Bouton "Confirmer"
- Historique changements

**Temps de développement:** ~12 heures  
**Nombre de templates:** 1 (event_users.html)

---

### 2.9 Gestion des Salles (Dashboard)

#### URLs:
- `/dashboard/events/{event_id}/rooms/create/` - Créer salle
- `/dashboard/rooms/{room_id}/edit/` - Éditer salle
- `/dashboard/rooms/{room_id}/delete/` - Supprimer salle

**FORMULAIRE SALLE:**
✅ Champs:
- Nom (requis)
- Description
- Capacité (requis, minimum 1)
- Localisation (requis)
- Étage
- Type (Auditorium, Workshop, Conference, Meeting)
- Équipements (textarea)

✅ Validation Django Forms

✅ Actions:
- Bouton "Enregistrer"
- Bouton "Annuler"

**PAGE ÉDITION:**
✅ Formulaire pré-rempli
✅ Affichage sessions dans cette salle
✅ Statistiques:
- Nombre de sessions
- Taux d'occupation moyen
- Prochaine session

**SUPPRESSION:**
✅ Confirmation requise
✅ Vérification sessions liées
✅ Option: Réassigner sessions ou supprimer

**Temps de développement:** ~8 heures  
**Nombre de templates:** 1 (room_edit.html)

---

### 2.10 Gestion des Sessions (Dashboard)

#### URLs:
- `/dashboard/events/{event_id}/sessions/create/` - Créer session
- `/dashboard/sessions/{session_id}/edit/` - Éditer session
- `/dashboard/sessions/{session_id}/delete/` - Supprimer session

**FORMULAIRE SESSION:**
✅ Champs organisés en sections:

**1. Informations de base:**
- Titre (requis)
- Description (textarea)
- Type (dropdown)
- Thème

**2. Horaires:**
- Date et heure début (datetime picker)
- Date et heure fin (datetime picker)
- Validation: fin > début

**3. Salle:**
- Sélection salle (dropdown filtré par événement)
- Affichage capacité salle

**4. Intervenant:**
- Nom
- Titre
- Biographie (textarea)
- URL photo

**5. Configuration:**
- Capacité max participants
- Session payante (checkbox)
- Prix en DZD (si payante)
- URL YouTube Live (optionnel)
- URL image couverture

**6. Statut:**
- Statut actuel (Pas encore/En cours/Terminé)

✅ Validation:
- Horaires cohérents
- Prix si session payante
- Capacité <= capacité salle

**PAGE ÉDITION:**
✅ Formulaire pré-rempli
✅ Section statistiques:
- Nombre inscrits
- Nombre présents
- Taux de remplissage
- Questions posées

✅ Section participants:
- Liste inscrits
- Statut paiement (si payante)

**SUPPRESSION:**
✅ Confirmation
✅ Vérification inscriptions
✅ Option: Notifier participants

**Temps de développement:** ~15 heures  
**Nombre de templates:** 1 (session_edit.html)

---

### 2.11 Gestion des Caisses

#### URLs:
- `/dashboard/caisses/` - Liste caisses
- `/dashboard/caisses/create/` - Créer caisse
- `/dashboard/caisses/{caisse_id}/` - Détail caisse
- `/dashboard/caisses/{caisse_id}/edit/` - Éditer caisse
- `/dashboard/caisses/{caisse_id}/delete/` - Supprimer caisse

**PAGE LISTE CAISSES:**
✅ Tableau caisses:
- Nom
- Événement
- Gestionnaire
- Statut (Active/Inactive)
- Total transactions
- Montant total
- Actions: Détails, Éditer, Supprimer

✅ Filtres:
- Par événement
- Par statut

✅ Bouton "Créer caisse"

**FORMULAIRE CAISSE:**
✅ Champs:
- Nom caisse (requis)
- Événement (dropdown, requis)
- Gestionnaire (user dropdown, requis)
- Localisation
- Statut actif/inactif
- Notes

**PAGE DÉTAIL CAISSE:**
✅ Statistiques:
- Transactions aujourd'hui
- Montant total encaissé
- Articles vendus
- Transactions annulées

✅ Historique transactions récentes:
- Tableau 50 dernières transactions
- Colonnes: ID, Participant, Articles, Montant, Date, Statut
- Filtres: Par date, par statut
- Export CSV

**Temps de développement:** ~15 heures  
**Nombre de templates:** 3 (caisse_list.html, caisse_form.html, caisse_detail.html)

---

### 2.12 Gestion des Articles Payables (Payable Items)

#### URLs:
- `/dashboard/events/{event_id}/payable-items/` - Liste articles
- `/dashboard/events/{event_id}/payable-items/create/` - Créer article
- `/dashboard/payable-items/{item_id}/edit/` - Éditer article
- `/dashboard/payable-items/{item_id}/delete/` - Supprimer article

**PAGE LISTE ARTICLES:**
✅ Tableau articles payables:
- Nom article
- Type (Session/Item/Service)
- Prix (DZD)
- Quantité disponible
- Vendus
- Statut
- Actions: Éditer, Supprimer

✅ Types d'articles:
- Ateliers payants
- Merchandise
- Services additionnels
- Documents

✅ Bouton "Ajouter article"

**FORMULAIRE ARTICLE:**
✅ Champs:
- Nom (requis)
- Description
- Type (dropdown)
- Prix (DZD, requis)
- Quantité disponible (optionnel)
- Session liée (si type=Session)
- Image
- Statut disponible/épuisé

**Temps de développement:** ~10 heures  
**Nombre de templates:** 2 (payable_items_list.html, payable_item_form.html)

---

### 2.13 Système d'Emails (Templates & Envois)

#### URLs Globales:
- `/dashboard/email-templates/` - Templates globaux
- `/dashboard/email-templates/create/` - Créer template
- `/dashboard/email-templates/{id}/edit/` - Éditer template
- `/dashboard/email-templates/{id}/delete/` - Supprimer template

#### URLs Par Événement:
- `/dashboard/events/{event_id}/email-templates/` - Templates événement
- `/dashboard/events/{event_id}/email-templates/create/` - Créer template événement
- `/dashboard/events/{event_id}/email-templates/{id}/edit/` - Éditer
- `/dashboard/events/{event_id}/email-templates/{id}/send/` - Envoyer email
- `/dashboard/events/{event_id}/email-logs/` - Historique envois

**PAGE LISTE TEMPLATES:**
✅ Tableau templates:
- Nom template
- Sujet email
- Type (Bienvenue/Confirmation/Rappel/Annonce)
- Dernière modification
- Utilisations
- Actions: Éditer, Dupliquer, Supprimer, Envoyer

✅ Templates par défaut:
- Email bienvenue participant
- Confirmation inscription session
- Rappel session (24h avant)
- Annonce générale

**FORMULAIRE TEMPLATE:**
✅ Champs:
- Nom template (requis)
- Sujet email (requis)
- Corps email (WYSIWYG editor)
- Variables disponibles:
  - {{first_name}}
  - {{last_name}}
  - {{event_name}}
  - {{session_title}}
  - {{qr_code}}
  - {{badge_id}}
  - etc.
- Type template
- Actif/inactif

✅ Prévisualisation:
- Rendu HTML
- Version texte
- Test variables

**PAGE ENVOI EMAIL:**
✅ Sélection destinataires:
- Tous les participants
- Par rôle (Participants, Exposants, etc.)
- Par session inscrite
- Liste personnalisée (checkbox)

✅ Configuration:
- Template à utiliser
- Personnalisation sujet/corps (optionnel)
- Pièces jointes
- Planification (envoi immédiat ou différé)

✅ Confirmation:
- Nombre de destinataires
- Aperçu email
- Bouton "Envoyer"

**PAGE HISTORIQUE EMAILS:**
✅ Tableau envois:
- Date envoi
- Template utilisé
- Destinataires (nombre)
- Statut (Envoyé/Échec/En cours)
- Taux ouverture
- Taux clic
- Actions: Voir détails, Renvoyer

✅ Détail envoi:
- Liste destinataires individuels
- Statut par destinataire
- Erreurs éventuelles

**Temps de développement:** ~25 heures  
**Nombre de templates:** 4 (email_template_list.html, email_template_form.html, send_event_email.html, event_email_logs.html)

---

### 2.14 Template de Base & Navigation

#### Template base.html:

✅ **Header:**
- Logo MakePlus
- Titre dashboard
- Menu utilisateur (dropdown):
  - Profil
  - Paramètres
  - Déconnexion

✅ **Sidebar (navigation):**
- Dashboard (home)
- **Événements:**
  - Liste événements
  - Créer événement
- **Utilisateurs:**
  - Liste utilisateurs
  - Créer utilisateur
- **Caisses:**
  - Liste caisses
  - Créer caisse
- **Email Templates:**
  - Templates globaux
  - Créer template
- **Paramètres** (si admin)
- **Documentation**

✅ **Content area:**
- Breadcrumb navigation
- Messages flash (succès/erreur/info/warning)
- Zone contenu dynamique

✅ **Footer:**
- Copyright
- Version
- Liens utiles

✅ **Design:**
- Bootstrap 5.3
- Icons Bootstrap Icons
- Thème moderne
- Mode clair (extensible mode sombre)
- Responsive sidebar (collapse sur mobile)

**Temps de développement:** ~10 heures  
**Nombre de templates:** 1 (base.html)

---

## 📊 RÉCAPITULATIF DASHBOARD WEB

### Nombre total de pages web: **~30 pages**

| Module | Pages | Temps (h) |
|--------|-------|-----------|
| Authentication | 2 | 6 |
| Dashboard Home | 1 | 12 |
| Wizard Création Event | 4 | 45 |
| Détail Événement | 1 | 25 |
| Édition Événement | 1 | 10 |
| Gestion Utilisateurs | 3 | 20 |
| Utilisateurs par Event | 1 | 12 |
| Gestion Salles | 1 | 8 |
| Gestion Sessions | 1 | 15 |
| Gestion Caisses | 3 | 15 |
| Articles Payables | 2 | 10 |
| Système Emails | 4 | 25 |
| Template Base | 1 | 10 |
| **TOTAL DASHBOARD** | **25** | **213h** |

---

## 🎨 SYSTÈME DE CAISSE (WEB)

### 3.1 Interface Caisse Web

#### URLs:
- `/caisse/login/` - Connexion caisse
- `/caisse/` - Dashboard caisse
- `/caisse/search/` - Recherche participant
- `/caisse/process-transaction/` - Traiter transaction
- `/caisse/transactions/` - Historique
- `/caisse/transactions/{id}/cancel/` - Annuler transaction
- `/caisse/print-badge/{participant_id}/` - Imprimer badge

#### Fonctionnalités:

**PAGE LOGIN CAISSE:**
✅ Interface simplifiée
✅ Authentification par username/password
✅ Vérification rôle caissier
✅ Sélection caisse si plusieurs

**DASHBOARD CAISSE:**
✅ Interface optimisée vente rapide
✅ **Zone recherche participant:**
- Par nom
- Par email
- Par badge ID
- Scan QR code (via webcam)

✅ **Résultats recherche:**
- Photo participant
- Nom complet
- Badge ID
- Événement
- Statut check-in
- Bouton "Sélectionner"

**PAGE TRANSACTION:**
✅ **Participant sélectionné:**
- Affichage infos participant
- Articles déjà achetés (grisés)

✅ **Sélection articles:**
- Liste articles disponibles
- Cards visuelles avec images
- Prix affiché
- Checkbox sélection multiple
- Sessions payantes visibles

✅ **Panier:**
- Articles sélectionnés
- Quantités
- Prix unitaires
- Total calculé automatiquement

✅ **Méthode de paiement:**
- Espèces
- Carte bancaire
- Virement
- Autre

✅ **Finalisation:**
- Bouton "Valider transaction"
- Impression reçu (optionnel)
- Impression/Mise à jour badge

**HISTORIQUE TRANSACTIONS:**
✅ Tableau transactions de la caisse
✅ Filtres par date, participant, montant
✅ Statut: Validée/Annulée
✅ Actions: Voir détail, Annuler (si < 24h)

**IMPRESSION BADGE:**
✅ Template badge imprimable
✅ Inclut:
- Photo participant
- Nom
- Événement
- QR code
- Sessions payées (liste)
✅ Format A6 (standard badge)
✅ CSS print-friendly

#### Design:
✅ Interface tactile-friendly
✅ Boutons larges
✅ Couleurs vives
✅ Responsive (tablette recommandée)
✅ Mode plein écran
✅ Raccourcis clavier

**Temps de développement:** ~30 heures  
**Nombre de templates:** 5

---

## 📦 RÉCAPITULATIF GLOBAL PARTIE WEB

### Modules développés:

| Composant | Sous-modules | Pages/Endpoints | Temps (h) |
|-----------|--------------|-----------------|-----------|
| **API Backend** | 13 modules | ~100 endpoints | 218 |
| **Dashboard Admin** | 13 modules | ~25 pages | 213 |
| **Système Caisse** | 7 fonctionnalités | 5 pages | 30 |
| **Templates Base** | Navigation, Base | 1 template | (inclus) |
| **TOTAL** | **33 modules** | **~130 items** | **461h** |

---

## 🗄️ STRUCTURE BASE DE DONNÉES

### Tables développées:

1. **auth_user** (Django standard)
   - Comptes utilisateurs

2. **events_userprofile**
   - Profils utilisateurs
   - QR codes utilisateurs

3. **events_event**
   - Événements
   - Fichiers PDFs

4. **events_usereventassignment**
   - Assignations utilisateur-événement-rôle

5. **events_room**
   - Salles des événements

6. **events_session**
   - Sessions/Conférences/Ateliers

7. **events_participant**
   - Participants aux événements

8. **events_roomaccess**
   - Historique accès salles

9. **events_sessionaccess**
   - Accès sessions (paiements)

10. **events_roomassignment**
    - Assignations gestionnaires-salles

11. **events_exposantscan**
    - Scans exposants

12. **events_annonce**
    - Annonces

13. **events_sessionquestion**
    - Questions-réponses sessions

14. **dashboard_emailtemplate**
    - Templates emails

15. **dashboard_emaillog**
    - Historique envois emails

16. **caisse_caisse**
    - Caisses enregistreuses

17. **caisse_payableitem**
    - Articles payables

18. **caisse_transaction**
    - Transactions

19. **caisse_transactionitem**
    - Détails transactions

**Total tables:** ~19 tables personnalisées (+ tables Django standard)

---

## 🔧 FONCTIONNALITÉS TECHNIQUES

### Sécurité:
✅ Authentification JWT pour API
✅ Sessions Django pour dashboard
✅ Hash passwords (PBKDF2)
✅ Protection CSRF
✅ CORS configuré
✅ Permissions par rôle
✅ Validation données entrée/sortie
✅ Rate limiting (configurable)
✅ HTTPS recommandé production

### Performance:
✅ Pagination tous les listings
✅ Select_related & prefetch_related (optimisation requêtes)
✅ Indexation base de données
✅ Caching pages dashboard (optionnel)
✅ Compression fichiers statiques
✅ CDN-ready pour médias

### Uploads de fichiers:
✅ Images (logo, bannière, photos): JPG, PNG, WebP
✅ PDFs (programme, guide, plan): max 10MB
✅ Organisation dossiers:
- `media/events/logos/`
- `media/events/banners/`
- `media/events/programmes/`
- `media/events/guides/`
- `media/exposants/plans/`

✅ Validation types MIME
✅ Redimensionnement images automatique (optionnel)
✅ Compatible cloud storage (AWS S3, Azure Blob)

### Exportations:
✅ Listes participants: CSV, Excel
✅ Transactions caisse: CSV, PDF
✅ Statistiques: CSV
✅ QR codes: PNG (individuel ou batch ZIP)
✅ Badges: PDF imprimable

### Intégrations:
✅ YouTube Live API (streaming)
✅ QR code generation library
✅ Email SMTP (Gmail, SendGrid, etc.)
✅ Swagger documentation
✅ REST API complet pour mobile

---

## 📱 COMPATIBILITÉ MOBILE API

### API prêt pour intégration Flutter:

✅ **Endpoints compatibles:**
- Tous les endpoints API fonctionnels
- Format JSON standardisé
- CORS activé
- Documentation Swagger complète

✅ **Flux mobile typiques supportés:**
1. Login → Liste événements → Sélection événement
2. Scan QR → Vérification → Enregistrement accès
3. Consultation programme → Inscription session
4. Q&A → Poser question → Voir réponses
5. Stats gestionnaire → Démarrer/Terminer session

✅ **Non inclus dans ce devis:**
- Application mobile Flutter
- Interfaces utilisateur mobiles
- Développement iOS/Android
- Tests mobiles
- Publication stores

**Note:** Ce devis couvre uniquement le backend API et l'interface web admin. L'application mobile nécessite un devis séparé.

---

## 🚀 DÉPLOIEMENT

### Configuration serveur requise:

**Minimum:**
- VPS/Cloud: 2 CPU, 4GB RAM, 50GB SSD
- OS: Ubuntu 20.04/22.04 LTS
- Python: 3.10+
- PostgreSQL: 13+
- Nginx/Apache
- SSL/TLS (Let's Encrypt)

**Recommandé Production:**
- VPS/Cloud: 4 CPU, 8GB RAM, 100GB SSD
- Load balancer (si haute charge)
- CDN pour médias (Cloudflare, AWS CloudFront)
- Monitoring (Sentry pour erreurs)
- Backup automatique DB quotidien

### Services cloud compatibles:
✅ AWS (EC2, RDS, S3)
✅ Azure (VM, Database, Blob Storage)
✅ DigitalOcean (Droplet, Managed Database)
✅ Heroku
✅ Google Cloud Platform

### Livrables déploiement:
✅ Scripts déploiement automatisé
✅ Configuration Nginx/Gunicorn
✅ Fichiers systemd service
✅ Configuration SSL
✅ Script backup base de données
✅ Documentation déploiement complète
✅ Variables d'environnement (.env template)

**Temps de développement (déploiement):** ~15 heures

---

## 📚 DOCUMENTATION LIVRÉE

### Documents fournis:

1. **BACKEND_DOCUMENTATION.md** (3600+ lignes)
   - Architecture complète
   - Tous les endpoints API
   - Modèles de données
   - Exemples requêtes/réponses
   - Guide permissions

2. **ADMIN_DASHBOARD_DOCUMENTATION.md** (870+ lignes)
   - Guide utilisateur dashboard
   - Workflows création événement
   - Gestion utilisateurs
   - Tutoriels pas-à-pas

3. **API_SWAGGER_DOCUMENTATION** (auto-générée)
   - Documentation interactive
   - Test endpoints en ligne
   - Schémas JSON

4. **DEVIS_CLIENT_MAKEPLUS.md** (existant)
   - Vue d'ensemble projet
   - Fonctionnalités complètes

5. **README.md**
   - Installation développement
   - Configuration
   - Commandes utiles

6. **Guides spécialisés:**
   - EVENT_PDF_FILES_IMPLEMENTATION.md
   - YOUTUBE_AND_QA_INTEGRATION.md
   - CAISSE_SYSTEM_IMPLEMENTATION.md
   - USER_ACCESS_CONTROL_SYSTEM.md
   - DATABASE_STRUCTURE_AND_WORKFLOW.md

**Total documentation:** ~6000+ lignes

**Temps de développement (documentation):** ~20 heures

---

## ⏱️ ESTIMATION TEMPS TOTAL

### Récapitulatif par composante:

| Composante | Détail | Heures |
|------------|--------|--------|
| **API Backend** | 13 modules, ~100 endpoints | 218h |
| **Dashboard Web** | 25 pages admin | 213h |
| **Système Caisse** | Interface caisse web | 30h |
| **Déploiement** | Scripts, config serveur | 15h |
| **Documentation** | Guides complets | 20h |
| **Tests & Debug** | QA, corrections bugs | 40h |
| **Réunions & Support** | Communication client | 20h |
| **TOTAL** | | **556h** |

### Répartition par phase:

**Phase 1 - Backend API (218h):**
- Modèles de données
- Endpoints REST
- Authentification JWT
- Permissions
- Tests API

**Phase 2 - Dashboard Admin (213h):**
- Templates HTML/CSS
- Formulaires Django
- Wizard création événement
- Pages gestion
- Interface responsive

**Phase 3 - Caisse (30h):**
- Interface caisse
- Traitement transactions
- Impression badges
- Historique

**Phase 4 - Finalisation (95h):**
- Déploiement
- Documentation
- Tests complets
- Formation
- Support

---

## 💰 ESTIMATION BUDGÉTAIRE

### Tarification proposée:

**Tarif horaire:** [À définir selon profil développeur]

**Options tarifaires:**

1. **Junior Developer (€25-35/h):**
   - Total: 556h × €30/h = **€16,680**

2. **Mid-Level Developer (€40-60/h):**
   - Total: 556h × €50/h = **€27,800**

3. **Senior Developer (€70-100/h):**
   - Total: 556h × €85/h = **€47,260**

4. **Forfait projet (recommandé):**
   - Estimation: **€25,000 - €35,000**
   - Inclut tout le développement
   - Support 3 mois inclus
   - Maintenance corrective
   - Formation utilisateurs (4h)

### Options additionnelles (non incluses):

| Service | Estimation |
|---------|-----------|
| Application mobile Flutter | €15,000 - €25,000 |
| Hébergement (1 an) | €500 - €2,000 |
| Nom de domaine (1 an) | €10 - €50 |
| SSL certificat | Gratuit (Let's Encrypt) |
| Maintenance mensuelle | €500 - €1,500/mois |
| Support technique (après 3 mois) | €800/mois |
| Formation avancée | €800/jour |
| Personnalisation design | €2,000 - €5,000 |

---

## 📋 LIVRABLES FINAUX

### Code source:
✅ Projet Django complet
✅ Structure dossiers organisée
✅ Code commenté
✅ Requirements.txt
✅ .env.example
✅ .gitignore
✅ Scripts utilitaires

### Base de données:
✅ Schéma PostgreSQL
✅ Migrations Django
✅ Données de test (fixtures)
✅ Script d'initialisation

### Documentation:
✅ Documentation technique (6000+ lignes)
✅ Guide utilisateur dashboard
✅ Guide API (Swagger)
✅ Guide déploiement
✅ FAQ

### Assets:
✅ Templates HTML/CSS
✅ Fichiers statiques (JS, CSS, images)
✅ Icons Bootstrap
✅ Templates emails

### Déploiement:
✅ Scripts déploiement
✅ Configuration serveur
✅ Backup scripts
✅ Monitoring setup

### Support:
✅ 3 mois support inclus
✅ Corrections bugs
✅ Mises à jour sécurité
✅ Formation utilisateurs (4h)

---

## 📅 PLANNING PRÉVISIONNEL

### Durée estimée: **3-4 mois** (pour 1 développeur à temps plein)

**Mois 1 (Semaines 1-4):**
- Semaine 1-2: Backend API (Modèles, Auth, Events)
- Semaine 3-4: Backend API (Rooms, Sessions, Participants)

**Mois 2 (Semaines 5-8):**
- Semaine 5-6: Backend API (Access Control, Assignations)
- Semaine 7-8: Dashboard Admin (Base, Auth, Home, Wizard)

**Mois 3 (Semaines 9-12):**
- Semaine 9-10: Dashboard Admin (Détails, Gestion)
- Semaine 11: Système Caisse
- Semaine 12: Emails, Tests

**Mois 4 (Semaines 13-14):**
- Semaine 13: Déploiement, Documentation
- Semaine 14: Tests finaux, Formation, Livraison

### Jalons (Milestones):

✅ **Jalon 1 (Fin Mois 1):** API Backend complète et testée  
✅ **Jalon 2 (Fin Mois 2):** Dashboard Admin de base fonctionnel  
✅ **Jalon 3 (Fin Mois 3):** Système complet + Caisse  
✅ **Jalon 4 (Fin Mois 4):** Déploiement production et formation  

---

## 🔒 GARANTIES

### Inclus dans le projet:

✅ **Garantie qualité:**
- Code propre et commenté
- Respect standards Django/Python
- Tests des fonctionnalités critiques
- Performance optimisée

✅ **Garantie fonctionnelle:**
- Toutes les fonctionnalités spécifiées
- API complète et documentée
- Dashboard intuitif et responsive
- Système caisse opérationnel

✅ **Garantie sécurité:**
- Authentification sécurisée
- Permissions par rôle
- Protection injections SQL
- Hash passwords
- HTTPS ready

✅ **Support inclus (3 mois):**
- Corrections bugs
- Mises à jour sécurité
- Support email (48h response)
- 1 intervention urgente/mois

### Exclusions:

❌ Application mobile (devis séparé)
❌ Hébergement et infrastructure
❌ Modifications majeures post-livraison
❌ Formation supplémentaire (> 4h)
❌ Maintenance après 3 mois (sauf contrat)

---

## 📧 CONTACT & VALIDATION

### Pour valider ce devis:

**Contact:**
[Votre nom/entreprise]  
Email: [votre@email.com]  
Téléphone: [votre téléphone]

**Validité du devis:** 30 jours

**Conditions de paiement suggérées:**
- 30% à la signature
- 30% à Jalon 2 (Dashboard de base)
- 30% à Jalon 4 (Livraison finale)
- 10% après 1 mois de production

**Acceptation:**
Signature client: ________________  
Date: ________________

---

## 📎 ANNEXES

### Technologies détaillées:

**Backend:**
- Django 5.2.7
- Django REST Framework 3.14+
- djangorestframework-simplejwt 5.3+
- drf-yasg 1.21+ (Swagger)
- django-cors-headers 4.3+
- Pillow 11.0+ (images)
- qrcode 8.0+ (QR codes)
- psycopg2-binary 2.9+ (PostgreSQL)

**Frontend Dashboard:**
- Bootstrap 5.3.0
- Bootstrap Icons 1.11+
- JavaScript ES6
- HTML5 / CSS3

**Serveur:**
- Nginx 1.18+
- Gunicorn 21.2+
- PostgreSQL 13+
- Redis (optionnel pour cache)

**Outils développement:**
- Git (version control)
- VSCode / PyCharm
- Postman (tests API)
- PostgreSQL Admin
- Python 3.10+

---

## ✅ CHECKLIST PROJET

### Fonctionnalités Backend API:
- [x] Authentification JWT
- [x] Gestion événements (CRUD)
- [x] Gestion salles (CRUD)
- [x] Gestion sessions (CRUD)
- [x] Système participants
- [x] QR codes utilisateurs
- [x] Vérification QR multi-niveaux
- [x] Contrôle d'accès salles
- [x] Ateliers payants
- [x] Assignations utilisateurs
- [x] Système rôles (5 rôles)
- [x] Annonces
- [x] Q&A sessions
- [x] YouTube Live integration
- [x] Assignations salles gestionnaires
- [x] Scans exposants
- [x] Statistiques
- [x] Upload fichiers (images, PDFs)
- [x] Documentation Swagger

### Fonctionnalités Dashboard Web:
- [x] Authentification web
- [x] Dashboard principal
- [x] Wizard création événement (4 étapes)
- [x] Détail événement (onglets)
- [x] Édition événement
- [x] Gestion utilisateurs (liste, création, détail)
- [x] QR codes (affichage, téléchargement)
- [x] Gestion utilisateurs par événement
- [x] Changement rôles
- [x] Gestion salles
- [x] Gestion sessions
- [x] Gestion caisses
- [x] Articles payables
- [x] Templates emails
- [x] Envoi emails masse
- [x] Historique emails
- [x] Navigation responsive
- [x] Messages flash

### Fonctionnalités Caisse:
- [x] Authentification caisse
- [x] Recherche participants
- [x] Scan QR code
- [x] Sélection articles
- [x] Traitement transactions
- [x] Méthodes paiement
- [x] Historique transactions
- [x] Annulation transactions
- [x] Impression badges

### Infrastructure:
- [x] Base de données PostgreSQL
- [x] Migrations Django
- [x] Scripts déploiement
- [x] Configuration Nginx
- [x] SSL/HTTPS setup
- [x] Backup scripts
- [x] Documentation technique
- [x] Guide utilisateur

---

**FIN DU DEVIS**

**Date de création:** 27 Janvier 2026  
**Version:** 1.0  
**Statut:** Proposition détaillée complète

---

*Ce devis détaillé couvre uniquement la partie web (backend API + dashboard admin + caisse). L'application mobile Flutter nécessite un devis séparé.*
