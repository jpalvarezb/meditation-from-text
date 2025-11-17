# Minday

*AI-Powered Personalized Meditation Generation*

**Note: This project is for exploratory, educational, and innovative purposes only, not for monetary gain. The website is accessible for demonstration but production has been halted.**

Minday is a technical exploration that transforms journal entries into personalized meditation sessions through advanced AI and audio processing. The system combines emotion analysis, generative AI, and sophisticated audio engineering to create custom meditation experiences.

## Technical Features

- **Emotion Classification**: ONNX-optimized transformer model for real-time emotional state analysis
- **Generative AI**: Google Gemini 2.0 Flash for context-aware meditation script generation
- **Neural TTS**: OpenAI's GPT-4-Mini-TTS with custom voice instructions
- **Audio Processing**: PyDub and Aeneas for precise text-audio alignment and mixing
- **Adaptive Sound Design**: Dynamic background composition based on emotional profiles
- **Multi-duration Support**: 1-7 minute sessions with word count optimization
- **User Authentication**: Supabase Auth with Row Level Security
- **Data Persistence**: PostgreSQL via Supabase for user sessions and feedback

## System Architecture

### Frontend Stack
- **Next.js 15**: App Router, TypeScript, Styled JSX
- **Authentication**: Supabase Auth with protected routes
- **Database**: Supabase PostgreSQL with RLS
- **UI Libraries**: Three.js for WebGL animations, Lucide React icons
- **State Management**: React hooks, session storage
- **Deployment**: Vercel with automatic branch deployments

### Backend Stack
- **FastAPI**: Async API with automatic OpenAPI documentation
- **AI Services**: Google Gemini 2.0 Flash, OpenAI GPT-4-Mini-TTS
- **Audio Processing**: 
  - PyDub for audio manipulation
  - Aeneas for forced alignment
  - FFmpeg for audio format conversion
- **ML Pipeline**: HuggingFace transformers with ONNX optimization
- **Storage**: Google Cloud Storage with signed URLs
- **Caching**: Request-based caching for meditation assets
- **Deployment**: Google Cloud Run with Docker containers

### Processing Pipeline
1. **Text Preprocessing**: Normalize and clean journal input
2. **Emotion Classification**: Multi-label classification using fine-tuned BERT
3. **Prompt Engineering**: Context-aware prompt construction for Gemini
4. **Script Generation**: AI-generated meditation with word count validation
5. **TTS Synthesis**: OpenAI TTS with custom voice parameters
6. **Audio Alignment**: Precise phoneme-level text-audio mapping
7. **Sound Engineering**: Dynamic mixing with emotion-responsive soundscapes
8. **Asset Management**: Cloud storage with CDN delivery

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

1. **Environment Setup** (local dev):
   ```bash
   # Install Python 3.11
   pyenv install 3.11.9
   pyenv local 3.11.9
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   cd backend
   # Torch CPU wheels often need the official index
   pip install -r requirements.txt -f https://download.pytorch.org/whl/torch_stable.html
   ```

   Or run the full pipeline via Docker (recommended for aeneas):
   ```bash
   cd backend
   docker compose up --build
   ```

2. **Environment Variables**:
   Copy `backend/.env.example` to `backend/.env` and set values. Key vars:
   ```env
   # AI Services
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_google_genai_api_key
   
   # Security
   BACKEND_API_KEY=your_secure_api_key
   
   # Google Cloud (for production)
   GOOGLE_APPLICATION_CREDENTIALS=... # JSON or Workload Identity
   AUDIO_BUCKET=your_storage_bucket
   
   # Environment
   ENV=dev  # set to prod in production
   ```

3. **Start Development Server (local)**:
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
   Copy `frontend/.env.local.example` to `frontend/.env.local` and set:
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

## Technical Workflow

1. **User Input**: Journal text processed through emotion classification model
2. **Configuration**: Duration and meditation type selection
3. **AI Processing**: Gemini generates personalized script with retry mechanisms
4. **Audio Synthesis**: TTS generation with custom voice parameters
5. **Post-Processing**: Audio alignment and dynamic sound mixing
6. **Delivery**: Signed URL generation for secure audio streaming

Note on development: in dev (ENV!=prod) the final mix is written to `backend/assets/audio/output/` and served by the frontend via `/output/<file>.mp3`. In production, artifacts are stored in GCS and served via signed URLs.

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
# Build and run with Docker Compose v2
cd backend
docker compose up --build
```

## Deployment

### Production Considerations

- **Environment Variables**: Set `ENV=prod` to enable production behavior (signed URLs, temp paths)
- **Google Cloud Storage**: Required for production audio file storage
- **Caching**: Redis recommended for production caching
- **Monitoring**: Implement logging and error tracking
- **Security**: Use strong API keys and HTTPS in production

### Deployment Options

- **Backend**: Google Cloud Run, AWS Lambda, or traditional VPS
- **Frontend**: Vercel, Netlify, or static hosting
- **Database**: Supabase (managed) or self-hosted PostgreSQL

## Project Status

This is an educational and exploratory project demonstrating advanced AI audio processing capabilities. The system is not intended for commercial use.

### Current Implementation
- ✅ Complete emotion classification pipeline
- ✅ Generative AI script creation with validation
- ✅ Neural TTS with custom voice synthesis
- ✅ Advanced audio processing and mixing
- ✅ User authentication and data persistence
- ⚠️ Limited production functionality due to API costs

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Technology Stack

- **OpenAI** - GPT-4-Mini-TTS for neural voice synthesis
- **Google** - Gemini 2.0 Flash for generative AI
- **HuggingFace** - Transformer models and ONNX optimization
- **Supabase** - PostgreSQL database, authentication, and RLS
- **Google Cloud** - Storage, compute, and deployment infrastructure
- **Aeneas** - Forced alignment for precise text-audio mapping

## Troubleshooting

- aeneas not installed: Use Docker (`docker compose up`) or install `aeneas==1.7.3.0`. The backend raises a clear error if it’s missing.
- Emotion model missing: If `backend/emotion_model/` isn’t present, the app falls back to a public HuggingFace model.
- Final mix not found in dev: Ensure the backend writes to `backend/assets/audio/output/` and the frontend serves `/output/<filename>.mp3`.
- Torch wheel install: On some platforms, add `-f https://download.pytorch.org/whl/torch_stable.html` when installing requirements.

## Security & Privacy

- Prototype only; do not enter sensitive personal data.
- No secrets are committed. Use `.env` files or Docker secrets.
- In production, prefer GCP Workload Identity (avoid embedding service account JSON).

## Roadmap / Next Steps

- Structured logging + request IDs, metrics, and alerting
- Background job/queue for long-running generations
- Cost controls and rate limiting per user
- E2E tests and golden-audio regression checks

## Support

For support, please open an issue on GitHub.

---

*"Choose to be optimistic, it feels better." – Dalai Lama*

Made with care for mindful living.
