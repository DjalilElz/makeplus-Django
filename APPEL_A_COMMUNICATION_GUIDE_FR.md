# 🎓 Système "Appel à Communication" - Guide Complet

## 📋 Vue d'ensemble

Le système **Appel à Communication** (aussi appelé ePoster) permet de gérer les soumissions scientifiques pour vos événements. Les participants soumettent leurs travaux via un formulaire public, et le **Comité Scientifique** valide ou invalide chaque soumission.

---

## 🚀 Accès au Système

### Pour les Administrateurs

#### Méthode 1: Menu Sidebar (NOUVEAU - RECOMMANDÉ)
```
Sidebar → "Appel à Communication" → Page centrale de gestion
```
Cette page montre TOUS vos événements avec leurs statistiques!

#### Méthode 2: Bouton vert sur la page d'accueil
```
Dashboard Home → Tableau des événements → Bouton vert 📄
```

#### Méthode 3: Depuis la page détail d'un événement
```
Dashboard Home → Voir événement → Onglet "ePoster"
```

### Pour les Membres du Comité Scientifique

```
1. Connectez-vous avec votre compte
2. Cliquez "Appel à Communication" dans le sidebar
3. Trouvez VOS événements (badge jaune "Membre du comité")
4. Cliquez "Voir Soumissions"
5. Validez ou invalidez les soumissions
```

---

## 🎯 Comment ça fonctionne ?

### Workflow Complet

```
┌─────────────────────────────────────────────────────────────┐
│                   FLUX DE TRAVAIL                            │
└─────────────────────────────────────────────────────────────┘

ÉTAPE 1: Configuration (Administrateur)
   │
   ├─ Créer un événement
   │
   ├─ Ajouter des membres au Comité Scientifique
   │  • Minimum 3 membres recommandé
   │  • Rôles: Membre, Président, Secrétaire
   │
   └─ (Optionnel) Configurer les emails automatiques


ÉTAPE 2: Partage (Administrateur)
   │
   └─ Copier l'URL publique
      • Format: /eposter/<event-id>/
      • Partager avec les participants par email, site web, etc.


ÉTAPE 3: Soumissions (Participants)
   │
   ├─ Accéder au formulaire via l'URL publique
   │
   ├─ Remplir le formulaire en 4 étapes:
   │  1. Informations personnelles
   │  2. Informations professionnelles
   │  3. Détails du travail
   │  4. Résumé scientifique
   │
   └─ Soumettre et recevoir email de confirmation


ÉTAPE 4: Validation (Comité Scientifique)
   │
   ├─ Se connecter au dashboard
   │
   ├─ Accéder aux soumissions via "Appel à Communication"
   │
   ├─ Pour chaque soumission:
   │  • Lire le résumé et les détails
   │  • Voter: Accepter ou Rejeter
   │  • Ajouter des commentaires
   │  • Donner une note (1-5 étoiles)
   │
   └─ Décision automatique quand majorité atteinte
      • Majorité = Accepte → Email d'acceptation envoyé
      • Majorité = Rejette → Email de rejet envoyé


ÉTAPE 5: Suivi (Administrateur)
   │
   ├─ Suivre les statistiques en temps réel
   │
   ├─ Voir qui a voté sur chaque soumission
   │
   └─ Exporter les données en CSV
```

---

## 📄 Page "Appel à Communication" (Centrale)

### Que voyez-vous sur cette page ?

**Pour chaque événement, vous voyez:**

#### 1. Statistiques Principales
```
┌─────────────────────────────────┐
│ Total Soumissions: 45           │
│ Comité Scientifique: 5 membres  │
└─────────────────────────────────┘
```

#### 2. Détail des Soumissions
```
┌─────────────────────────────────┐
│ Acceptées:    12                │
│ En attente:   28                │
│ Rejetées:      5                │
└─────────────────────────────────┘
```

#### 3. URL Publique
```
┌─────────────────────────────────────────┐
│ https://votresite.com/eposter/123...    │
│ [Copier] ← Bouton pour copier l'URL    │
└─────────────────────────────────────────┘
```

#### 4. Actions Rapides
```
• Dashboard Complet
• Voir Soumissions
• Comité (gérer membres)
• Emails (templates)
```

---

## 👨‍💼 Guide Administrateur Détaillé

### Configuration Initiale (10 minutes)

#### Étape 1: Créer/Sélectionner un événement
```
1. Si pas encore d'événement:
   Dashboard → "Create Event" → Remplir les informations

2. Si événement existe déjà:
   Sidebar → "Appel à Communication"
```

#### Étape 2: Ajouter le Comité Scientifique
```
1. Sur la page "Appel à Communication"
2. Trouvez votre événement
3. Cliquez "Comité (X membres)"
4. Cliquez "Ajouter un Membre"
5. Sélectionnez:
   • Utilisateur (doit exister dans le système)
   • Rôle: Membre / Président / Secrétaire
6. Répétez pour 3-7 membres (recommandé)
```

**Important:** Les utilisateurs doivent d'abord être créés dans "Users" avant d'être ajoutés au comité.

#### Étape 3: Configurer les Emails (Optionnel)
```
1. Cliquez "Emails" sur votre événement
2. 4 types de templates disponibles:
   • Soumission reçue
   • Accepté
   • Rejeté
   • Révision demandée
3. Pour chaque type, créez un template avec:
   • Sujet
   • Corps (avec variables: {nom}, {prenom}, etc.)
```

#### Étape 4: Partager l'URL
```
1. Sur la page "Appel à Communication"
2. Copiez l'URL publique avec le bouton "Copier"
3. Partagez via:
   • Email aux participants potentiels
   • Annonce sur votre site web
   • Réseaux sociaux
   • Newsletters
```

### Gestion Quotidienne

#### Suivre les Soumissions
```
Option 1: Page centrale
→ Sidebar → "Appel à Communication"
→ Voir les statistiques mises à jour

Option 2: Dashboard détaillé
→ Cliquez "Dashboard Complet" sur un événement
→ Voir graphiques et soumissions récentes
```

#### Voir Toutes les Soumissions
```
1. Cliquez "Voir Soumissions (X)"
2. Filtrez par statut:
   • Toutes
   • En attente
   • Acceptées
   • Rejetées
3. Cliquez "Voir Détails" pour lire une soumission
```

#### Exporter les Données
```
1. Sur la liste des soumissions
2. Cliquez "Exporter CSV"
3. Ouvrez dans Excel/Google Sheets
4. Contient: toutes les infos + votes + commentaires
```

#### Changer Manuellement un Statut
```
1. Ouvrez une soumission
2. Utilisez le dropdown "Changer le statut"
3. Sélectionnez nouveau statut
4. Email automatique envoyé au participant
```

---

## 🗳️ Guide Comité Scientifique

### Première Connexion

```
1. Recevez vos identifiants de l'administrateur
2. Connectez-vous: /dashboard/login/
3. Cliquez "Appel à Communication" dans le sidebar
4. Vous voyez VOS événements avec badge jaune
```

### Processus de Validation

#### Étape 1: Accéder aux Soumissions
```
1. Sur la page "Appel à Communication"
2. Trouvez votre événement (badge jaune)
3. Cliquez "Voir Soumissions (X)"
```

#### Étape 2: Ouvrir une Soumission
```
1. Dans la liste, cliquez "Voir Détails"
2. Vous voyez:
   • Informations du participant
   • Résumé scientifique (4 sections)
   • Fichiers joints
   • Panel des votes (temps réel)
```

#### Étape 3: Voter
```
1. Scrollez jusqu'au formulaire "Votre Vote"

2. Sélectionnez votre décision:
   [ ] Accepter    [ ] Rejeter

3. Ajoutez vos commentaires:
   ┌─────────────────────────────────┐
   │ Vos commentaires (optionnel)    │
   │                                 │
   │ Exemple:                        │
   │ "Excellente méthodologie,       │
   │ résultats bien présentés..."    │
   └─────────────────────────────────┘

4. Donnez une note:
   ⭐⭐⭐⭐⭐ (1-5 étoiles)

5. Cliquez "Soumettre Validation"
```

#### Étape 4: Voir les Votes en Temps Réel
```
Le panel se met à jour automatiquement (toutes les 10 secondes):

┌────────────────────────────────────────┐
│ VOTES DU COMITÉ                        │
├────────────────────────────────────────┤
│ Dr. Dupont    ✅ ACCEPTÉ    ⭐⭐⭐⭐  │
│ Dr. Martin    ❌ REJETÉ     ⭐⭐⭐   │
│ Dr. Bernard   ⏳ EN ATTENTE          │
│ Dr. Petit     ⏳ EN ATTENTE          │
└────────────────────────────────────────┘

Légende:
✅ = A voté Accepter
❌ = A voté Rejeter
⏳ = N'a pas encore voté
```

### Conseils pour Voter

**Critères de Décision:**
- Pertinence scientifique
- Qualité de la méthodologie
- Clarté de la présentation
- Originalité des résultats
- Respect des consignes

**Commentaires Utiles:**
- Soyez constructif et professionnel
- Mentionnez les points forts ET les faiblesses
- Proposez des améliorations si possible
- Restez respectueux et encourageant

**Notation:**
- ⭐⭐⭐⭐⭐ (5) = Excellent, publier sans modifications
- ⭐⭐⭐⭐ (4) = Très bien, modifications mineures
- ⭐⭐⭐ (3) = Correct, révisions nécessaires
- ⭐⭐ (2) = Faible, révisions majeures
- ⭐ (1) = Insuffisant, refuser

---

## 📝 Guide Participant

### Comment Soumettre

#### Étape 1: Obtenir le Lien
```
L'organisateur vous envoie l'URL:
https://votresite.com/eposter/abc-123-def-456/
```

#### Étape 2: Remplir le Formulaire

**Le formulaire a 4 étapes:**

```
ÉTAPE 1/4: Informations Personnelles
├─ Nom *
├─ Prénom *
├─ Email *
├─ Téléphone *
└─ Spécialité *

ÉTAPE 2/4: Informations Professionnelles
├─ Institution *
├─ Département / Service
├─ Ville *
└─ Pays *

ÉTAPE 3/4: Détails du Travail
├─ Titre du travail *
├─ Mots clés * (séparés par virgules)
├─ Type de travail *
│  • Communication orale
│  • Communication affichée
│  • E-poster
└─ Fichiers supplémentaires (max 10MB)

ÉTAPE 4/4: Résumé
├─ Introduction *
│  (Contexte et objectifs)
│
├─ Matériels et Méthodes *
│  (Méthodologie utilisée)
│
├─ Résultats *
│  (Principaux résultats obtenus)
│
└─ Conclusion *
   (Synthèse et implications)

* = Champs obligatoires
```

#### Étape 3: Navigation dans le Formulaire
```
• Bouton "Suivant" → Passe à l'étape suivante
• Bouton "Précédent" → Retour à l'étape précédente
• Étape 4 → Bouton "Soumettre" (final)
```

#### Étape 4: Confirmation
```
Après soumission:
1. Message de succès apparaît
2. Email de confirmation reçu immédiatement
3. Votre soumission est enregistrée
```

### Que se passe-t-il ensuite ?

```
1. CONFIRMATION (Immédiat)
   └─ Email automatique de confirmation

2. ÉVALUATION (Quelques jours)
   └─ Le comité scientifique examine votre travail

3. DÉCISION (Après vote majoritaire)
   ├─ Accepté → Email d'acceptation
   │  "Félicitations! Votre travail a été accepté..."
   │
   └─ Rejeté → Email de rejet
      "Merci pour votre soumission. Malheureusement..."
```

### Conseils pour une Bonne Soumission

**AVANT de commencer:**
- ✅ Préparez votre texte dans Word/Google Docs
- ✅ Relisez attentivement (orthographe, grammaire)
- ✅ Vérifiez que vous avez tous les fichiers
- ✅ Assurez-vous d'avoir 30-45 minutes devant vous

**PENDANT la saisie:**
- ✅ Copiez votre travail régulièrement (pas d'auto-save)
- ✅ Respectez la structure demandée
- ✅ Soyez clair et concis
- ✅ Utilisez un langage scientifique approprié

**Fichiers joints:**
- ✅ Max 10MB par fichier
- ✅ Formats recommandés: PDF, DOCX, PPTX
- ✅ Nommez clairement vos fichiers
- ✅ Vérifiez que les fichiers s'ouvrent correctement

---

## 🔒 Accès et Permissions

### Qui peut faire quoi ?

```
┌──────────────────┬──────────┬───────────┬─────────────┐
│ Action           │ Particip.│ Comité    │ Admin       │
├──────────────────┼──────────┼───────────┼─────────────┤
│ Soumettre travail│    ✅    │     ❌    │     ❌      │
│ Voir soumissions │    ❌    │     ✅    │     ✅      │
│ Voter/Valider    │    ❌    │     ✅    │     ❌*     │
│ Gérer comité     │    ❌    │     ❌    │     ✅      │
│ Voir dashboard   │    ❌    │     ✅    │     ✅      │
│ Exporter CSV     │    ❌    │     ❌    │     ✅      │
│ Config emails    │    ❌    │     ❌    │     ✅      │
│ Changer statut   │    ❌    │     ❌    │     ✅      │
└──────────────────┴──────────┴───────────┴─────────────┘

* Admin peut voir mais ne devrait pas voter
  (sauf s'il est aussi membre du comité)
```

### Comptes Utilisateurs

#### Pour le Comité Scientifique:
```
1. Admin crée le compte:
   Dashboard → Users → Create User
   
2. Renseignements nécessaires:
   • Nom d'utilisateur
   • Email
   • Mot de passe
   • Prénom / Nom
   • (Pas besoin de rôle "staff")

3. Admin ajoute au comité:
   Appel à Communication → Comité → Ajouter

4. Membre reçoit ses identifiants
   (par email ou communication directe)

5. Membre se connecte:
   /dashboard/login/
```

---

## 📊 Statistiques et Rapports

### Statistiques Disponibles

#### Sur la Page Centrale
```
Pour CHAQUE événement:
• Total soumissions
• Nombre de membres du comité
• Acceptées / En attente / Rejetées
```

#### Sur le Dashboard Détaillé
```
• Graphiques de soumissions par statut
• Soumissions récentes (5 dernières)
• Liste des membres du comité
• Actions rapides
```

#### Sur la Liste des Soumissions
```
• Filtrage par statut
• Recherche par titre/auteur
• Tri par date
• Nombre total affiché
```

### Export CSV

**Contenu du fichier:**
```
Colonnes exportées:
• ID soumission
• Date de soumission
• Nom et prénom
• Email et téléphone
• Institution et spécialité
• Titre du travail
• Mots clés
• Type de travail
• Résumé complet (4 sections)
• Statut de validation
• Nombre de votes accepter/rejeter
• Date dernière modification
```

**Utilisation:**
- Ouvrir dans Excel ou Google Sheets
- Créer des rapports personnalisés
- Analyser les tendances
- Partager avec les co-organisateurs
- Archiver pour historique

---

## 🔔 Notifications Email

### Emails Automatiques

#### 1. Confirmation de Soumission
```
Quand: Immédiatement après soumission
À: Participant
Contenu par défaut:
"Merci pour votre soumission. Nous avons bien reçu 
votre travail intitulé '{titre_travail}'..."
```

#### 2. Acceptation
```
Quand: Dès que majorité du comité accepte
À: Participant
Contenu par défaut:
"Félicitations! Votre travail a été accepté par le 
comité scientifique..."
```

#### 3. Rejet
```
Quand: Dès que majorité du comité rejette
À: Participant
Contenu par défaut:
"Merci pour votre soumission. Après examen, le comité 
scientifique n'a pas pu retenir votre travail..."
```

#### 4. Révision Demandée (Manuel)
```
Quand: Admin change statut manuellement
À: Participant
Contenu par défaut:
"Le comité scientifique a examiné votre travail et 
demande quelques modifications..."
```

### Personnalisation des Emails

**Variables disponibles:**
```
{nom}               → Nom du participant
{prenom}            → Prénom
{email}             → Email
{telephone}         → Téléphone
{specialite}        → Spécialité
{institution}       → Institution
{titre_travail}     → Titre du travail
{type_travail}      → Type (oral/affiché/e-poster)
{event_name}        → Nom de l'événement
{submission_date}   → Date de soumission
```

**Exemple de template personnalisé:**
```
Sujet: Soumission reçue - {event_name}

Corps:
Bonjour Dr. {nom},

Nous avons bien reçu votre soumission intitulée 
"{titre_travail}" pour l'événement {event_name}.

Le comité scientifique examinera votre travail dans 
les prochains jours. Vous recevrez une réponse par 
email.

Cordialement,
L'équipe organisatrice
```

---

## ❓ Dépannage

### Problèmes Courants

#### "Je ne vois pas mes événements sur la page Appel à Communication"
```
Solutions:
1. Vérifiez que vous êtes connecté
2. Assurez-vous qu'au moins un événement existe
3. Rafraîchissez la page (F5)
4. Vérifiez vos permissions avec l'admin
```

#### "Le bouton 'Voir Soumissions' ne s'affiche pas"
```
Causes possibles:
• Vous n'êtes pas membre du comité pour cet événement
• Vous n'êtes pas administrateur
Solution: Demandez à l'admin de vous ajouter au comité
```

#### "Les emails ne sont pas envoyés"
```
Vérifications:
1. Configuration SMTP dans Django settings.py
2. Templates d'email créés pour l'événement
3. Email du participant valide
4. Vérifier les spams/courrier indésirable
```

#### "Le formulaire public affiche 'Soumissions Fermées'"
```
Causes:
• Les dates de soumission sont passées
• Les dates n'ont pas été configurées
Solution: Admin doit modifier les dates dans l'événement
```

#### "Les mises à jour temps réel ne fonctionnent pas"
```
Solutions:
1. Attendez 10 secondes pour l'auto-refresh
2. Rafraîchissez manuellement (F5)
3. Vérifiez que JavaScript est activé
4. Ouvrez la console (F12) pour voir les erreurs
```

---

## 💡 Astuces et Bonnes Pratiques

### Pour Administrateurs

**Organisation:**
- 📅 Définissez des dates claires de soumission
- 👥 Choisissez un comité diversifié (3-7 membres)
- 📧 Testez les emails avant d'ouvrir les soumissions
- 💾 Exportez le CSV régulièrement (backup)

**Communication:**
- 📣 Annoncez largement l'appel à communication
- 🔗 Partagez l'URL sur plusieurs canaux
- ⏰ Rappelez la date limite quelques jours avant
- 📊 Tenez les participants informés du processus

### Pour Comité Scientifique

**Évaluation:**
- ⚡ Votez rapidement (24-48h max)
- 💬 Soyez constructif dans vos commentaires
- 🤝 Discutez avec les autres membres si doute
- ⚖️ Utilisez les mêmes critères pour tous

**Éthique:**
- 🚫 Signalez les conflits d'intérêts
- 🤐 Gardez les soumissions confidentielles
- ⚖️ Soyez impartial et objectif
- 📝 Documentez vos décisions (commentaires)

### Pour Participants

**Préparation:**
- 📝 Écrivez d'abord dans un traitement de texte
- 👀 Faites relire par un collègue
- 🎯 Respectez la structure demandée
- 📎 Préparez vos fichiers à l'avance

**Soumission:**
- ⏰ Ne attendez pas la dernière minute
- 💾 Sauvegardez votre texte régulièrement
- ✅ Relisez avant de soumettre
- 📧 Vérifiez votre email après soumission

---

## 📚 Résumé Rapide

### En 3 Points

1. **Administrateur** configure le comité et partage l'URL
2. **Participants** soumettent via le formulaire public
3. **Comité Scientifique** vote et valide les soumissions

### URLs Importantes

```
Central Hub:    /dashboard/eposter/
Public Form:    /eposter/<event-id>/
Login:          /dashboard/login/
Admin Panel:    /admin/
```

### Accès Rapides

```
Sidebar → "Appel à Communication" → Page centrale
         ↓
   Voir TOUS les événements
         ↓
   Cliquer sur boutons d'action
         ↓
   Gérer soumissions et comité
```

---

**Besoin d'aide ?** Consultez les autres guides:
- [EPOSTER_USER_GUIDE.md](EPOSTER_USER_GUIDE.md) - Guide technique détaillé
- [EPOSTER_VISUAL_GUIDE.md](EPOSTER_VISUAL_GUIDE.md) - Schémas et visuels
- [EPOSTER_ARCHITECTURE.md](EPOSTER_ARCHITECTURE.md) - Architecture système

**Système opérationnel et prêt à l'emploi!** 🎉
