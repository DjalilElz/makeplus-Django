# DEVIS - Plateforme de Gestion d'Événements MakePlus

**Date :** 28 Janvier 2026  
**Montant Total :** 100 000,00 DA

---

## 📊 Résumé du Projet

Développement d'une plateforme web complète de gestion d'événements avec tableau de bord administratif, système de gestion des utilisateurs, et application mobile.

---

## 🎯 Composants de la Plateforme

### **1. TABLEAU DE BORD ADMINISTRATIF**
**35 Pages Développées**

#### Pages de Gestion des Événements (8 pages)
- Tableau de bord principal avec statistiques
- Liste et détails des événements
- Création d'événements (4 étapes)
- Modification et suppression d'événements

#### Pages de Gestion des Utilisateurs (6 pages)
- Liste complète des utilisateurs
- Création et détails des utilisateurs
- Gestion des rôles et permissions
- Téléchargement des codes QR
- Affectation des utilisateurs aux événements

#### Pages de Gestion des Inscriptions (3 pages)
- Liste des inscriptions par événement
- Approbation et validation des inscriptions
- Suppression des inscriptions

#### Pages de Gestion Financière (5 pages)
- Gestion des caisses
- Création et détails des caisses
- Articles payables par événement
- Création et modification des articles
- Suivi des paiements

#### Pages de Gestion des Salles et Sessions (6 pages)
- Création et modification des salles
- Suppression des salles
- Gestion des sessions/ateliers
- Programmation des sessions
- Attribution des salles aux sessions

#### Pages de Communication (8 pages)
- Constructeur de templates d'emails (avec éditeur visuel)
- Gestion des templates d'emails globaux
- Templates d'emails spécifiques aux événements
- Envoi d'emails aux participants
- Statistiques d'envoi d'emails
- Constructeur de formulaires d'inscription personnalisés
- Gestion des soumissions de formulaires
- Historique des emails envoyés

---

### **2. API REST (Interface de Programmation)**
**68 Endpoints API Développés**

#### APIs d'Authentification (7 endpoints)
- Inscription et connexion des utilisateurs
- Gestion des profils
- Changement de mot de passe
- Sélection et changement d'événement
- Déconnexion

#### APIs de Gestion d'Événements (12 endpoints)
- CRUD complet des événements (Create, Read, Update, Delete)
- Liste et filtrage des événements
- Événements par utilisateur
- Statistiques des événements
- Recherche et pagination

#### APIs de Gestion des Salles (10 endpoints)
- CRUD complet des salles
- Salles par événement
- Disponibilité des salles
- Attribution des salles
- Statistiques d'utilisation

#### APIs de Gestion des Sessions (12 endpoints)
- CRUD complet des sessions
- Sessions par événement et par salle
- Démarrage et fin de sessions
- Accès aux sessions
- Mes ateliers (pour les participants)

#### APIs de Gestion des Participants (10 endpoints)
- CRUD complet des participants
- Liste par événement
- Scan des codes QR
- Enregistrement des présences
- Historique de participation

#### APIs de Notifications (5 endpoints)
- Liste des notifications
- Détails d'une notification
- Marquer comme lu
- Notifications non lues
- Suppression

#### APIs d'Affectations (6 endpoints)
- Attribution des utilisateurs aux événements
- Attribution des salles aux contrôleurs
- Accès aux salles et sessions
- Gestion des scans exposants
- Historique des attributions

#### APIs de Questions et Annonces (6 endpoints)
- Questions des participants
- Annonces de l'événement
- CRUD complet des annonces
- Liste des questions par session
- Modération des questions

---

### **3. FONCTIONNALITÉS PRINCIPALES**

#### 🎫 Gestion Complète des Événements
- Création d'événements en plusieurs étapes
- Configuration détaillée (dates, lieu, capacité)
- Gestion des salles et sessions
- Planning et programmation
- Suivi en temps réel

#### 👥 Système de Gestion des Utilisateurs
- Rôles multiples (Admin, Contrôleur, Exposant, Participant)
- Affectation automatique aux événements
- Génération automatique de codes QR
- Système de permissions avancé
- Profils utilisateurs complets

#### 📝 Système d'Inscriptions Personnalisables
- Formulaires d'inscription sur mesure
- Constructeur de formulaires drag-and-drop
- Champs personnalisables illimités
- URL publique unique par formulaire
- Validation et approbation des inscriptions

#### 💰 Gestion Financière
- Système de caisse intégré
- Articles payables personnalisables
- Suivi des paiements
- Rapports financiers
- Gestion multi-caisses

#### 📱 Codes QR et Contrôle d'Accès
- Génération automatique de codes QR uniques
- Vérification instantanée par scan
- Contrôle d'accès aux salles et sessions
- Enregistrement automatique des présences
- Historique complet des scans

#### 📧 Système de Communication Avancé
- Éditeur d'emails visuel (drag-and-drop)
- Templates d'emails réutilisables
- Envoi en masse aux participants
- Personnalisation des emails
- Statistiques d'envoi et de lecture
- Emails de confirmation automatiques

#### 📊 Statistiques et Rapports
- Tableau de bord avec indicateurs clés
- Statistiques par événement
- Rapports de présence
- Statistiques des contrôleurs
- Analyse des inscriptions

#### 🔔 Système de Notifications
- Notifications en temps réel
- Alertes pour les administrateurs
- Notifications pour les participants
- Gestion des préférences
- Historique des notifications

#### 🔒 Sécurité et Authentification
- Authentification sécurisée
- Gestion des sessions
- Tokens d'authentification
- Protection des données
- Contrôle d'accès par rôles

#### 🖼️ Système E-Posters *(À développer)*
- Galerie de posters scientifiques numériques
- Téléchargement et gestion des e-posters par les participants
- Catégorisation des posters par thématique
- Système de vote et évaluation des posters
- Affichage des posters les mieux notés
- Téléchargement des posters en PDF
- Commentaires et discussions sur les posters
- Interface de navigation interactive

---

## 💻 Technologies Utilisées

- **Backend :** Django REST Framework (Python)
- **Base de données :** SQLite (évolutif vers PostgreSQL)
- **Frontend Admin :** HTML5, CSS3, Bootstrap, JavaScript
- **API :** REST avec documentation complète
- **Éditeur d'emails :** Unlayer (éditeur drag-and-drop professionnel)
- **Codes QR :** Génération et lecture automatique
- **Sécurité :** Authentification par tokens

---

## 📦 Livrables

✅ **35 Pages de tableau de bord** entièrement fonctionnelles  
✅ **68 APIs REST** documentées et testées  
✅ **Base de données** structurée et optimisée  
✅ **Système de codes QR** complet  
✅ **Constructeur de formulaires** personnalisables  
✅ **Éditeur d'emails** visuel intégré  
✅ **Système de notifications** en temps réel  
✅ **Documentation technique** complète  
✅ **Tests et déploiement** sur serveur de développement

### 🔜 Fonctionnalités Prévues
⏳ **Système E-Posters** *(en cours de développement)*

---

## 💰 MONTANT TOTAL

### **100 000,00 DA**
*(Cent Mille Dinars Algériens)*

---


