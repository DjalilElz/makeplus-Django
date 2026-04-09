# MakePlus Backend - Architecture Diagram

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                          │
├─────────────────────────────────────────────────────────────────────┤
│  Flutter Mobile App  │  Web Dashboard  │  Admin Panel  │  Public Web │
└──────────┬───────────┴────────┬────────┴──────┬───────┴─────────┬───┘
           │                    │               │                 │
           │ JWT Token          │ Session Auth  │ Session Auth    │ No Auth
           │                    │               │                 │
           ▼                    ▼               ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DJANGO APPLICATION                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    URL ROUTING (urls.py)                     │   │
│  └────┬──────────────┬──────────────┬──────────────┬───────────┘   │
│       │              │              │              │                │
│       ▼              ▼              ▼              ▼                │
│  ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐          │
│  │  /api/  │   │/dashboard│   │ /admin/ │   │ /forms/  │          │
│  │         │   │    /     │   │         │   │ /eposter/│          │
│  └────┬────┘   └────┬─────┘   └────┬────┘   └────┬─────┘          │
│       │             │              │              │                │
│       ▼             ▼              ▼              ▼                │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    MIDDLEWARE LAYER                          │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ CORS │ JWT Auth │ Event Context │ Session │ CSRF │ Cache    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│       │             │              │              │                │
│       ▼             ▼              ▼              ▼                │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    APPLICATION LAYER                         │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │  │ events app   │  │dashboard app │  │ caisse app   │      │  │
│  │  ├──────────────┤  ├──────────────┤  ├──────────────┤      │  │
│  │  │ • ViewSets   │  │ • Views      │  │ • Views      │      │  │
│  │  │ • Serializers│  │ • Forms      │  │ • Models     │      │  │
│  │  │ • Permissions│  │ • Templates  │  │ • Templates  │      │  │
│  │  │ • Models     │  │ • Models     │  │              │      │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │  │
│  │         │                 │                 │               │  │
│  └─────────┼─────────────────┼─────────────────┼───────────────┘  │
│            │                 │                 │                   │
│            ▼                 ▼                 ▼                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    DATABASE LAYER (ORM)                      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│            │                                                        │
└────────────┼────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA STORAGE                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │   PostgreSQL     │  │   File Storage   │  │   Cache (Redis)  │ │
│  │   (Production)   │  │   (media/)       │  │   (Optional)     │ │
│  │   SQLite (Dev)   │  │   • Images       │  │                  │ │
│  │                  │  │   • PDFs         │  │                  │ │
│  │   • Events       │  │   • Documents    │  │                  │ │
│  │   • Users        │  │                  │  │                  │ │
│  │   • Sessions     │  │                  │  │                  │ │
│  │   • Participants │  │                  │  │                  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  MailerLite  │  │   SendGrid   │  │   YouTube    │             │
│  │  (Email)     │  │   (Backup)   │  │   (Live)     │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow Diagrams

### 1. Authentication Flow

```
┌──────────┐                                    ┌──────────────┐
│  Client  │                                    │   Backend    │
└────┬─────┘                                    └──────┬───────┘
     │                                                 │
     │  POST /api/auth/login/                         │
     │  { email, password }                           │
     ├───────────────────────────────────────────────>│
     │                                                 │
     │                                                 │ Validate credentials
     │                                                 │ Check event assignments
     │                                                 │
     │  200 OK                                         │
     │  { access, refresh, user, current_event }      │
     │<───────────────────────────────────────────────┤
     │                                                 │
     │  Store JWT tokens                               │
     │                                                 │
     │  GET /api/events/                               │
     │  Authorization: Bearer <access_token>           │
     ├───────────────────────────────────────────────>│
     │                                                 │
     │                                                 │ Verify JWT
     │                                                 │ Extract event context
     │                                                 │ Check permissions
     │                                                 │
     │  200 OK                                         │
     │  { events: [...] }                              │
     │<───────────────────────────────────────────────┤
     │                                                 │
```

### 2. QR Code Verification Flow

```
┌────────────┐         ┌────────────┐         ┌──────────────┐
│ Controller │         │  Backend   │         │   Database   │
└─────┬──────┘         └─────┬──────┘         └──────┬───────┘
      │                      │                       │
      │ Scan QR Code         │                       │
      │ {"user_id": 15,      │                       │
      │  "badge_id": "..."}  │                       │
      │                      │                       │
      │ POST /api/rooms/{id}/verify_access/          │
      │ { qr_data, session } │                       │
      ├─────────────────────>│                       │
      │                      │                       │
      │                      │ 1. Get User           │
      │                      ├──────────────────────>│
      │                      │<──────────────────────┤
      │                      │                       │
      │                      │ 2. Check Event Access │
      │                      │    (UserEventAssignment)
      │                      ├──────────────────────>│
      │                      │<──────────────────────┤
      │                      │                       │
      │                      │ 3. Check Room Access  │
      │                      │    (Participant.allowed_rooms)
      │                      ├──────────────────────>│
      │                      │<──────────────────────┤
      │                      │                       │
      │                      │ 4. Check Session Payment
      │                      │    (SessionAccess)    │
      │                      ├──────────────────────>│
      │                      │<──────────────────────┤
      │                      │                       │
      │                      │ 5. Create RoomAccess  │
      │                      ├──────────────────────>│
      │                      │<──────────────────────┤
      │                      │                       │
      │ 200 OK               │                       │
      │ { status: "granted", │                       │
      │   participant: {...},│                       │
      │   access: {...} }    │                       │
      │<─────────────────────┤                       │
      │                      │                       │
      │ Display Success      │                       │
      │                      │                       │
```

### 3. Session Q&A Flow

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│ Participant │       │   Backend    │       │Gestionnaire │
└──────┬──────┘       └──────┬───────┘       └──────┬──────┘
       │                     │                      │
       │ POST /api/session-questions/               │
       │ { session, question_text }                 │
       ├────────────────────>│                      │
       │                     │                      │
       │                     │ Create Question      │
       │                     │ is_answered = false  │
       │                     │                      │
       │ 201 Created         │                      │
       │ { question: {...} } │                      │
       │<────────────────────┤                      │
       │                     │                      │
       │                     │                      │
       │                     │ GET /api/session-questions/
       │                     │ ?is_answered=false   │
       │                     │<─────────────────────┤
       │                     │                      │
       │                     │ 200 OK               │
       │                     │ { questions: [...] } │
       │                     │─────────────────────>│
       │                     │                      │
       │                     │                      │ Review question
       │                     │                      │
       │                     │ POST /api/session-questions/{id}/answer/
       │                     │ { answer_text }      │
       │                     │<─────────────────────┤
       │                     │                      │
       │                     │ Update Question      │
       │                     │ is_answered = true   │
       │                     │                      │
       │                     │ 200 OK               │
       │                     │ { question: {...} }  │
       │                     │─────────────────────>│
       │                     │                      │
       │ GET /api/session-questions/{id}/           │
       ├────────────────────>│                      │
       │                     │                      │
       │ 200 OK              │                      │
       │ { question with answer }                   │
       │<────────────────────┤                      │
       │                     │                      │
       │ Display answer      │                      │
       │                     │                      │
```

## 🔐 Permission Matrix

```
┌──────────────────────┬──────────────┬────────────┬─────────────┬──────────┐
│      Endpoint        │ Gestionnaire │ Contrôleur │ Participant │ Exposant │
├──────────────────────┼──────────────┼────────────┼─────────────┼──────────┤
│ Events (CRUD)        │      ✅      │     ❌     │      ❌     │    ❌    │
│ Events (Read)        │      ✅      │     ✅     │      ✅     │    ✅    │
│ Rooms (CRUD)         │      ✅      │     ❌     │      ❌     │    ❌    │
│ Rooms (Read)         │      ✅      │     ✅     │      ✅     │    ✅    │
│ Sessions (CRUD)      │      ✅      │     ❌     │      ❌     │    ❌    │
│ Sessions (Read)      │      ✅      │     ✅     │      ✅     │    ✅    │
│ QR Verification      │      ✅      │     ✅     │      ❌     │    ❌    │
│ Session Questions    │      ✅      │     ❌     │      ✅     │    ❌    │
│ Answer Questions     │      ✅      │     ❌     │      ❌     │    ❌    │
│ Exposant Scans       │      ❌      │     ❌     │      ❌     │    ✅    │
│ Room Statistics      │      ✅      │     ✅     │      ❌     │    ❌    │
│ Announcements (CRUD) │      ✅      │     ✅     │      ✅     │    ✅    │
│ Announcements (Read) │   ✅ (All)   │ ✅ (Target)│  ✅ (Target)│✅ (Target)│
└──────────────────────┴──────────────┴────────────┴─────────────┴──────────┘
```

## 📦 Database Schema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CORE MODELS                                  │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
│    Event     │         │  UserEventAssign │         │     User     │
├──────────────┤         ├──────────────────┤         ├──────────────┤
│ id (UUID)    │◄───────┤│ event_id (FK)    │◄───────┤│ id           │
│ name         │         │ user_id (FK)     │         │ username     │
│ description  │         │ role             │         │ email        │
│ start_date   │         │ is_active        │         │ first_name   │
│ end_date     │         └──────────────────┘         │ last_name    │
│ location     │                                       └──────┬───────┘
│ logo         │                                              │
│ banner       │                                              │
│ programme_pdf│                                              │
│ guide_pdf    │                                              │
└──────┬───────┘                                              │
       │                                                      │
       │                                                      │
       │         ┌──────────────┐                            │
       │         │ UserProfile  │                            │
       │         ├──────────────┤                            │
       │         │ user_id (FK) │◄───────────────────────────┘
       │         │ qr_code_data │
       │         └──────────────┘
       │
       │
       ├────────>┌──────────────┐
       │         │     Room     │
       │         ├──────────────┤
       │         │ id (UUID)    │
       │         │ event_id (FK)│
       │         │ name         │
       │         │ capacity     │
       │         │ description  │
       │         └──────┬───────┘
       │                │
       │                │
       ├────────>┌──────┴───────┐
       │         │   Session    │
       │         ├──────────────┤
       │         │ id (UUID)    │
       │         │ event_id (FK)│
       │         │ room_id (FK) │
       │         │ title        │
       │         │ speaker_name │
       │         │ start_time   │
       │         │ end_time     │
       │         │ status       │
       │         │ is_paid      │
       │         │ price        │
       │         │ youtube_url  │
       │         └──────┬───────┘
       │                │
       │                │
       └────────>┌──────┴───────┐
                 │ Participant  │
                 ├──────────────┤
                 │ id (UUID)    │
                 │ user_id (FK) │
                 │ event_id (FK)│
                 │ badge_id     │
                 │ qr_code_data │
                 │ is_checked_in│
                 └──────┬───────┘
                        │
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
┌────────────────┐ ┌──────────────┐ ┌──────────────┐
│  RoomAccess    │ │SessionAccess │ │ExposantScan  │
├────────────────┤ ├──────────────┤ ├──────────────┤
│ participant_id │ │participant_id│ │ exposant_id  │
│ room_id        │ │ session_id   │ │ scanned_id   │
│ accessed_at    │ │ has_access   │ │ scanned_at   │
│ status         │ │ payment_stat │ │ notes        │
└────────────────┘ └──────────────┘ └──────────────┘
```

## 🔄 Request/Response Cycle

```
1. Client Request
   ↓
2. CORS Middleware (check origin)
   ↓
3. JWT Authentication (verify token)
   ↓
4. Event Context Middleware (extract event from JWT)
   ↓
5. URL Router (match endpoint)
   ↓
6. ViewSet/View (handle request)
   ↓
7. Permission Check (verify role)
   ↓
8. Serializer (validate data)
   ↓
9. Model/Database (query/update)
   ↓
10. Serializer (format response)
    ↓
11. JSON Response
    ↓
12. Client receives data
```

## 🎯 Key Design Patterns

### 1. ViewSet Pattern (DRF)
- Combines list, create, retrieve, update, delete in one class
- Automatic URL routing
- Built-in pagination, filtering, search

### 2. Serializer Pattern
- Data validation
- Object serialization/deserialization
- Nested relationships

### 3. Permission Classes
- Reusable permission logic
- Role-based access control
- Object-level permissions

### 4. Middleware Pattern
- Request/response processing
- Authentication
- Event context injection

### 5. Signal Pattern
- Auto-update statistics
- Trigger actions on model changes
- Decouple logic

---

**Note**: This architecture supports horizontal scaling, caching, and can be deployed on cloud platforms (Render, AWS, Azure, etc.)
