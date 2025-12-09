# YouTube Live Streaming & Q&A System - Frontend Integration Guide

**Version:** 1.0  
**Last Updated:** November 29, 2025  
**Status:** ✅ Production Ready

---

## Overview

This guide explains how to integrate two key features into your Flutter/web frontend:

1. **YouTube Live Streaming** - Display live YouTube streams for sessions
2. **Q&A System** - Allow participants to ask questions and see answers

Both features are **already implemented** in the backend and ready for frontend integration.

---

## 1. YouTube Live Streaming

### How It Works

- Each session (conference/atelier) can have a YouTube live stream URL
- Field: `youtube_live_url` (URLField, optional)
- Returned in all session endpoints (`/api/sessions/`, `/api/my-ateliers/`)
- Use case: Hybrid events (in-person + online participation)

### Session Response Example

```json
{
  "id": "session-uuid",
  "title": "Conférence: Startup Fundraising",
  "speaker_name": "Karim Benyoucef",
  "start_time": "2025-11-30T09:00:00Z",
  "end_time": "2025-11-30T10:30:00Z",
  "status": "en_cours",
  "is_live": true,
  "youtube_live_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `youtube_live_url` | String (URL) | YouTube live stream URL (null if no stream) |
| `is_live` | Boolean | True if session is currently running |
| `status` | String | `pas_encore`, `en_cours`, `termine` |

---

### Frontend Implementation (Flutter)

#### 1. Check if Session Has Live Stream

```dart
bool hasLiveStream(Session session) {
  return session.youtubeUrl != null && 
         session.youtubeUrl!.isNotEmpty;
}

bool canWatchLive(Session session) {
  return hasLiveStream(session) && session.isLive;
}
```

#### 2. Display "Watch Live" Button

```dart
Widget buildLiveStreamButton(Session session) {
  if (!canWatchLive(session)) return SizedBox.shrink();
  
  return ElevatedButton.icon(
    onPressed: () => _openYouTubeLive(session.youtubeUrl),
    icon: Icon(Icons.play_circle_filled, color: Colors.red),
    label: Text('Regarder en direct'),
    style: ElevatedButton.styleFrom(
      backgroundColor: Colors.red[50],
      foregroundColor: Colors.red[900],
    ),
  );
}
```

#### 3. Open YouTube Live Stream

**Option A: Open YouTube App (Recommended for Mobile)**

```dart
import 'package:url_launcher/url_launcher.dart';

Future<void> _openYouTubeLive(String youtubeUrl) async {
  final Uri url = Uri.parse(youtubeUrl);
  
  if (await canLaunchUrl(url)) {
    await launchUrl(
      url,
      mode: LaunchMode.externalApplication, // Opens YouTube app
    );
  } else {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Impossible d\'ouvrir YouTube')),
    );
  }
}
```

**Option B: Embedded YouTube Player (In-App)**

First, add dependency to `pubspec.yaml`:
```yaml
dependencies:
  youtube_player_flutter: ^8.1.2
```

Then implement:
```dart
import 'package:youtube_player_flutter/youtube_player_flutter.dart';

Widget buildYouTubePlayer(String youtubeUrl) {
  String? videoId = YoutubePlayer.convertUrlToId(youtubeUrl);
  
  if (videoId == null) {
    return Text('URL YouTube invalide');
  }
  
  final controller = YoutubePlayerController(
    initialVideoId: videoId,
    flags: YoutubePlayerFlags(
      autoPlay: false,
      mute: false,
      isLive: true, // Enable live stream mode
      enableCaption: false,
    ),
  );
  
  return YoutubePlayer(
    controller: controller,
    showVideoProgressIndicator: true,
    progressIndicatorColor: Colors.red,
    progressColors: ProgressBarColors(
      playedColor: Colors.red,
      handleColor: Colors.redAccent,
    ),
  );
}
```

#### 4. Show Live Indicator

```dart
Widget buildLiveIndicator(Session session) {
  if (!session.isLive) return SizedBox.shrink();
  
  return Container(
    decoration: BoxDecoration(
      color: Colors.red,
      borderRadius: BorderRadius.circular(4),
    ),
    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: Colors.white,
            shape: BoxShape.circle,
          ),
        ),
        SizedBox(width: 4),
        Text(
          'EN DIRECT',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 12,
          ),
        ),
      ],
    ),
  );
}
```

#### 5. Complete Session Card with Live Stream

```dart
class SessionCard extends StatelessWidget {
  final Session session;
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          // Session header
          ListTile(
            title: Text(session.title),
            subtitle: Text(session.speakerName),
            trailing: buildLiveIndicator(session),
          ),
          
          // Session details
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              children: [
                Text(session.description),
                SizedBox(height: 16),
                
                // Show YouTube button if live
                if (canWatchLive(session))
                  buildLiveStreamButton(session),
                  
                // Or show embedded player
                if (canWatchLive(session))
                  buildYouTubePlayer(session.youtubeUrl!),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

#### 6. YouTube URL Helper

```dart
class YouTubeHelper {
  /// Extract video ID from YouTube URL
  static String? extractVideoId(String? url) {
    if (url == null || url.isEmpty) return null;
    
    final regExp = RegExp(
      r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})',
    );
    
    final match = regExp.firstMatch(url);
    return match?.group(1);
  }
  
  /// Check if URL is a valid YouTube URL
  static bool isValidYouTubeUrl(String? url) {
    return extractVideoId(url) != null;
  }
  
  /// Convert to YouTube embed URL
  static String? getEmbedUrl(String? url) {
    final videoId = extractVideoId(url);
    if (videoId == null) return null;
    return 'https://www.youtube.com/embed/$videoId';
  }
}
```

---

## 2. Q&A System (Session Questions)

### How It Works

- Participants can ask questions on any session
- Gestionnaires can answer questions
- Questions are visible to all participants
- Filter by session, answered status, participant

### API Endpoints

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/session-questions/` | List questions | Authenticated |
| POST | `/api/session-questions/` | Ask question | Participant |
| GET | `/api/session-questions/{id}/` | Get question details | Authenticated |
| POST | `/api/session-questions/{id}/answer/` | Answer question | Gestionnaire |

### Question Model

```json
{
  "id": "question-uuid",
  "session": "session-uuid",
  "session_title": "Atelier: Product Development",
  "participant": "participant-uuid",
  "participant_name": "Ahmed Benali",
  "question_text": "What are the key differences between MVP and Prototype?",
  "is_answered": true,
  "answer_text": "An MVP is a basic version with core features...",
  "answered_by": "gestionnaire-uuid",
  "answered_by_name": "Fatima Cherif",
  "asked_at": "2025-11-29T14:30:00Z",
  "answered_at": "2025-11-29T14:45:00Z"
}
```

---

### Frontend Implementation (Flutter)

#### 1. Data Model

```dart
class SessionQuestion {
  final String id;
  final String sessionId;
  final String sessionTitle;
  final String participantId;
  final String participantName;
  final String questionText;
  final bool isAnswered;
  final String? answerText;
  final String? answeredBy;
  final String? answeredByName;
  final DateTime askedAt;
  final DateTime? answeredAt;
  
  SessionQuestion.fromJson(Map<String, dynamic> json)
      : id = json['id'],
        sessionId = json['session'],
        sessionTitle = json['session_title'],
        participantId = json['participant'],
        participantName = json['participant_name'],
        questionText = json['question_text'],
        isAnswered = json['is_answered'],
        answerText = json['answer_text'],
        answeredBy = json['answered_by'],
        answeredByName = json['answered_by_name'],
        askedAt = DateTime.parse(json['asked_at']),
        answeredAt = json['answered_at'] != null 
            ? DateTime.parse(json['answered_at']) 
            : null;
}
```

#### 2. API Service

```dart
class QAService {
  final ApiClient _apiClient;
  
  /// Get questions for a session
  Future<List<SessionQuestion>> getSessionQuestions(
    String sessionId, {
    bool? isAnswered,
  }) async {
    final params = {
      'session': sessionId,
      if (isAnswered != null) 'is_answered': isAnswered.toString(),
    };
    
    final response = await _apiClient.get(
      '/api/session-questions/',
      queryParameters: params,
    );
    
    return (response.data['results'] as List)
        .map((json) => SessionQuestion.fromJson(json))
        .toList();
  }
  
  /// Ask a question
  Future<SessionQuestion> askQuestion(
    String sessionId,
    String questionText,
  ) async {
    final response = await _apiClient.post(
      '/api/session-questions/',
      data: {
        'session': sessionId,
        'question_text': questionText,
      },
    );
    
    return SessionQuestion.fromJson(response.data);
  }
  
  /// Get participant's questions
  Future<List<SessionQuestion>> getMyQuestions(String participantId) async {
    final response = await _apiClient.get(
      '/api/session-questions/',
      queryParameters: {'participant': participantId},
    );
    
    return (response.data['results'] as List)
        .map((json) => SessionQuestion.fromJson(json))
        .toList();
  }
  
  /// Answer a question (Gestionnaire only)
  Future<SessionQuestion> answerQuestion(
    String questionId,
    String answerText,
  ) async {
    final response = await _apiClient.post(
      '/api/session-questions/$questionId/answer/',
      data: {'answer_text': answerText},
    );
    
    return SessionQuestion.fromJson(response.data);
  }
}
```

#### 3. Ask Question UI

```dart
class AskQuestionDialog extends StatefulWidget {
  final String sessionId;
  final String sessionTitle;
  
  @override
  _AskQuestionDialogState createState() => _AskQuestionDialogState();
}

class _AskQuestionDialogState extends State<AskQuestionDialog> {
  final _controller = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;
  
  Future<void> _submitQuestion() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      await context.read<QAService>().askQuestion(
        widget.sessionId,
        _controller.text,
      );
      
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Question envoyée avec succès')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Poser une question'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              widget.sessionTitle,
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            TextFormField(
              controller: _controller,
              maxLines: 4,
              decoration: InputDecoration(
                hintText: 'Votre question...',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Veuillez entrer votre question';
                }
                return null;
              },
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('Annuler'),
        ),
        ElevatedButton(
          onPressed: _isLoading ? null : _submitQuestion,
          child: _isLoading
              ? SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text('Envoyer'),
        ),
      ],
    );
  }
}
```

#### 4. Display Q&A List

```dart
class SessionQAList extends StatefulWidget {
  final String sessionId;
  
  @override
  _SessionQAListState createState() => _SessionQAListState();
}

class _SessionQAListState extends State<SessionQAList> {
  List<SessionQuestion> _questions = [];
  bool _isLoading = true;
  bool _showOnlyUnanswered = false;
  
  @override
  void initState() {
    super.initState();
    _loadQuestions();
  }
  
  Future<void> _loadQuestions() async {
    setState(() => _isLoading = true);
    
    try {
      final questions = await context.read<QAService>().getSessionQuestions(
        widget.sessionId,
        isAnswered: _showOnlyUnanswered ? false : null,
      );
      
      setState(() => _questions = questions);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur de chargement: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Filter toggle
        SwitchListTile(
          title: Text('Afficher seulement les questions sans réponse'),
          value: _showOnlyUnanswered,
          onChanged: (value) {
            setState(() => _showOnlyUnanswered = value);
            _loadQuestions();
          },
        ),
        
        // Questions list
        Expanded(
          child: _isLoading
              ? Center(child: CircularProgressIndicator())
              : _questions.isEmpty
                  ? Center(child: Text('Aucune question'))
                  : ListView.builder(
                      itemCount: _questions.length,
                      itemBuilder: (context, index) {
                        return QuestionCard(question: _questions[index]);
                      },
                    ),
        ),
        
        // Ask question button
        Padding(
          padding: EdgeInsets.all(16),
          child: ElevatedButton.icon(
            onPressed: () => _showAskDialog(),
            icon: Icon(Icons.question_answer),
            label: Text('Poser une question'),
          ),
        ),
      ],
    );
  }
  
  void _showAskDialog() {
    showDialog(
      context: context,
      builder: (context) => AskQuestionDialog(
        sessionId: widget.sessionId,
        sessionTitle: 'Session Title', // Pass from parent
      ),
    ).then((_) => _loadQuestions()); // Reload after asking
  }
}
```

#### 5. Question Card Widget

```dart
class QuestionCard extends StatelessWidget {
  final SessionQuestion question;
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Question header
          ListTile(
            leading: CircleAvatar(
              child: Icon(Icons.person),
            ),
            title: Text(question.participantName),
            subtitle: Text(_formatTime(question.askedAt)),
            trailing: question.isAnswered
                ? Icon(Icons.check_circle, color: Colors.green)
                : Icon(Icons.help_outline, color: Colors.grey),
          ),
          
          // Question text
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              question.questionText,
              style: TextStyle(fontSize: 16),
            ),
          ),
          
          // Answer (if available)
          if (question.isAnswered) ...[
            Divider(),
            ListTile(
              leading: Icon(Icons.chat, color: Colors.blue),
              title: Text('Réponse de ${question.answeredByName}'),
              subtitle: Text(_formatTime(question.answeredAt!)),
            ),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue[50],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  question.answerText!,
                  style: TextStyle(fontSize: 15),
                ),
              ),
            ),
          ],
          
          SizedBox(height: 8),
        ],
      ),
    );
  }
  
  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final diff = now.difference(time);
    
    if (diff.inMinutes < 1) return 'À l\'instant';
    if (diff.inMinutes < 60) return 'Il y a ${diff.inMinutes} min';
    if (diff.inHours < 24) return 'Il y a ${diff.inHours}h';
    return 'Il y a ${diff.inDays}j';
  }
}
```

#### 6. Real-time Updates (Polling)

```dart
class SessionQAListWithPolling extends StatefulWidget {
  final String sessionId;
  
  @override
  _SessionQAListWithPollingState createState() => _SessionQAListWithPollingState();
}

class _SessionQAListWithPollingState extends State<SessionQAListWithPolling> {
  Timer? _pollingTimer;
  
  @override
  void initState() {
    super.initState();
    _loadQuestions();
    
    // Poll every 30 seconds during live sessions
    _pollingTimer = Timer.periodic(
      Duration(seconds: 30),
      (_) => _loadQuestions(),
    );
  }
  
  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }
  
  Future<void> _loadQuestions() async {
    // Load questions (same as before)
  }
  
  @override
  Widget build(BuildContext context) {
    // Same UI as SessionQAList
    return Container();
  }
}
```

---

## Testing the Integration

### YouTube Live Streaming

1. **Create test session** with YouTube URL:
   ```bash
   POST /api/sessions/
   {
     "title": "Test Live Stream",
     "youtube_live_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
   }
   ```

2. **Mark session as live**:
   ```bash
   POST /api/sessions/{id}/start/
   ```

3. **Fetch session** and verify `is_live=true` and `youtube_live_url` is present

4. **Test in Flutter**: Display live indicator and YouTube button/player

### Q&A System

1. **Ask question as participant**:
   ```bash
   POST /api/session-questions/
   {
     "session": "session-uuid",
     "question_text": "Test question?"
   }
   ```

2. **List questions**:
   ```bash
   GET /api/session-questions/?session=session-uuid
   ```

3. **Answer as gestionnaire**:
   ```bash
   POST /api/session-questions/{id}/answer/
   {
     "answer_text": "Test answer"
   }
   ```

4. **Verify in Flutter**: Question shows as answered

---

## Best Practices

### YouTube Live

✅ **Always check** if `youtube_live_url` is null before displaying player  
✅ **Validate URL** format before opening  
✅ **Provide fallback** if YouTube app not installed  
✅ **Show live indicator** only when `is_live=true`  
✅ **Test on both** Android and iOS devices  

### Q&A System

✅ **Validate** question text (not empty, max 1000 chars)  
✅ **Show loading states** when submitting/fetching  
✅ **Poll for updates** during live sessions (every 30s)  
✅ **Filter by answered status** for better UX  
✅ **Display timestamps** in relative format ("2h ago")  
✅ **Handle permissions** (only gestionnaires can answer)  

---

## Support

For issues or questions:
- Check `BACKEND_DOCUMENTATION.md` for full API reference
- Test endpoints in Swagger UI: http://127.0.0.1:8000/swagger/
- Contact backend team for assistance

**Backend Status:** ✅ Production Ready  
**Last Updated:** November 29, 2025
