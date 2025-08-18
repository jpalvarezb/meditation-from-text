# Minday

*AI-Powered Personalized Meditation from Your Daily Reflections*

Minday transforms your personal journal entries into custom-guided meditations tailored to your emotional state and meditation preferences. Using advanced emotion analysis, AI-generated scripts, and sophisticated audio engineering, Minday creates deeply personal meditation experiences that resonate with your daily life.

## Key Features

- **Emotion-Aware Analysis**: Advanced NLP models analyze your journal entries to understand your emotional state
- **AI Script Generation**: Google Gemini creates personalized meditation scripts based on your emotions and preferences  
- **Professional Text-to-Speech**: OpenAI's premium TTS generates soothing guided audio
- **Adaptive Sound Design**: Dynamic background music and soundscapes that respond to your emotional profile
- **Flexible Duration**: Choose from 1, 3, 5, or 7-minute sessions
- **Meditation Types**: Morning, evening, sleep, stress release, conflict resolution, self-love, and focus reset
- **Privacy-First**: Your personal reflections stay secure with you
- **Responsive Design**: Beautiful, minimalist interface that works on all devices

## Architecture

Minday is a full-stack application built with modern technologies:

### Frontend (Next.js 15)
- **Framework**: Next.js 15 with App Router
- **Authentication**: Supabase Auth
- **UI**: Custom React components with Three.js animations
- **Styling**: Styled JSX with responsive design
- **State Management**: React hooks and session storage

### Backend (FastAPI)
- **API Framework**: FastAPI with automatic API documentation
- **AI Integration**: Google Gemini 2.0 for script generation
- **TTS**: OpenAI GPT-4-Mini-TTS for audio synthesis
- **Audio Processing**: PyDub with Aeneas for text-audio alignment
- **Emotion Analysis**: Optimized ONNX model for real-time emotion classification
- **Cloud Storage**: Google Cloud Storage for production assets
- **Caching**: Intelligent caching system to optimize response times

### Audio Pipeline
1. **Emotion Scoring**: HuggingFace transformer model analyzes journal text
2. **Script Generation**: AI creates personalized meditation narratives
3. **TTS Generation**: Premium voice synthesis with custom pacing
4. **Audio Alignment**: Precise text-to-audio synchronization
5. **Sound Engineering**: Dynamic mixing with ambient soundscapes and chimes

## Project Structure

```
meditation-from-text/
├── frontend/                    # Next.js React application
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   │   ├── api/           # Next.js API routes (proxy)
│   │   │   ├── journal/       # Journal entry page
│   │   │   ├── prepare/       # Meditation preferences
│   │   │   ├── meditation/    # Audio playback interface
│   │   │   └── feedback/      # Post-session feedback
│   │   ├── components/        # Reusable React components
│   │   ├── lib/              # Utility functions & Supabase client
│   │   └── providers/        # Context providers
│   └── public/               # Static assets
├── backend/                  # FastAPI Python application
│   ├── api/                 # FastAPI routes and schemas
│   ├── app/                 # Core application logic
│   │   ├── emotion_scoring.py     # Emotion analysis
│   │   ├── script_generator.py    # AI script generation
│   │   ├── tts_generator.py       # Text-to-speech
│   │   ├── sound_engineer.py      # Audio mixing
│   │   └── audio_utils.py         # Audio processing utilities
│   ├── config/              # Configuration and constants
│   └── emotion_model/       # Pre-trained emotion classification model
└── README.md               # This file
```

## Getting Started

### Prerequisites

- **Python 3.11+** (managed with pyenv)
- **Node.js 18+**
- **FFmpeg** (for audio processing)
- **Espeak** (for text-to-speech alignment)

### Backend Setup

1. **Environment Setup**:
   ```bash
   # Install Python 3.11
   pyenv install 3.11.9
   pyenv local 3.11.9
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create `.env` in the backend directory:
   ```env
   # AI Services
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_google_genai_api_key
   
   # Security
   BACKEND_API_KEY=your_secure_api_key
   
   # Google Cloud (for production)
   GOOGLE_CLOUD_PROJECT=your_project_id
   GCS_BUCKET=your_storage_bucket
   
   # Environment
   IS_PROD=False  # Set to True for production
   ```

4. **Start Development Server**:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

### Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Environment Variables**:
   Create `.env.local`:
   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   BACKEND_API_KEY=your_secure_api_key
   
   # Supabase (for authentication & data)
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

3. **Start Development Server**:
   ```bash
   npm run dev
   ```

4. **Access the Application**:
   Open [http://localhost:3000](http://localhost:3000)

## API Endpoints

### Core Meditation API

**POST** `/meditate`
- **Description**: Generate a personalized meditation from journal entry
- **Headers**: `x-api-key: YOUR_API_KEY`
- **Request**:
  ```json
  {
    "journal_entry": "Today I felt overwhelmed by meetings but hopeful for the future.",
    "duration_minutes": 5,
    "meditation_type": "stress release",
    "mode": "tts"
  }
  ```
- **Response**:
  ```json
  {
    "final_signed_url": "https://...",
    "final_audio_path": "/path/to/audio.mp3",
    "emotion_summary": {"stress": 0.7, "hope": 0.3},
    "script_path": "/path/to/script.txt",
    "tts_path": "/path/to/tts.wav",
    "alignment_path": "/path/to/alignment.json"
  }
  ```

**POST** `/feedback`
- **Description**: Submit user feedback
- **Request**:
  ```json
  {
    "star_rating": 5,
    "feedback_text": "This meditation was exactly what I needed!"
  }
  ```

### Meditation Types

- `morning` - Energizing start to your day
- `evening` - Peaceful wind-down sessions  
- `sleep` - Deep relaxation for better rest
- `stress release` - Tension relief and emotional unwinding
- `conflict resolution` - Healing from difficult situations
- `self-love` - Nurturing self-compassion
- `focus reset` - Mental clarity and concentration

## Usage

1. **Journal Entry**: Write about your current thoughts, feelings, or experiences
2. **Customize Session**: Choose duration (1-7 minutes) and meditation type
3. **AI Generation**: The system analyzes your emotions and creates a personalized script
4. **Audio Experience**: Listen to your custom meditation with adaptive soundscapes
5. **Feedback**: Share your experience to help improve future sessions

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests  
cd frontend
npm test
```

### Code Quality
```bash
# Backend linting
cd backend
flake8 app/ api/ config/

# Frontend linting
cd frontend
npm run lint
```

### Docker Development
```bash
# Build and run with Docker Compose
cd backend
docker-compose up --build
```

## Deployment

### Production Considerations

- **Environment Variables**: Set `IS_PROD=True` for cloud storage
- **Google Cloud Storage**: Required for production audio file storage
- **Caching**: Redis recommended for production caching
- **Monitoring**: Implement logging and error tracking
- **Security**: Use strong API keys and HTTPS in production

### Deployment Options

- **Backend**: Google Cloud Run, AWS Lambda, or traditional VPS
- **Frontend**: Vercel, Netlify, or static hosting
- **Database**: Supabase (managed) or self-hosted PostgreSQL

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code style and conventions
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **OpenAI** for advanced text-to-speech capabilities
- **Google** for Gemini AI and cloud services
- **HuggingFace** for emotion classification models
- **Aeneas** for precise audio-text alignment
- **Supabase** for authentication and database services

## Support

For support, please open an issue on GitHub or contact the development team.

---

*"Choose to be optimistic, it feels better." – Dalai Lama*

Made with care for mindful living.
