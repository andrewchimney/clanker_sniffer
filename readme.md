## AI Lyrics Detector – Fullstack Architecture and DevOps Plan

### 🧩 Project Overview

A self-hosted, microservice-based web application that lets users upload `.mp3` files, runs vocal separation (Demucs), transcribes vocals to lyrics (Whisper), and classifies lyrics as AI- or human-generated.

clanker_sniffer/
├── app/               # frontend + API gateway (Next.js)
├── demucs-api/        # vocal separation microservice
├── whisper-api/       # transcription microservice
├── classifier-api/    # AI/human prediction microservice
├── db/                # optional: init.sql or migration files
├── docker-compose.yml
├── .env.local
├── .gitignore
└── README.md

### 🧱 Microservices

#### 1. `demucs-api`

- **POST /separate**
  - Input: `.mp3` or `.wav` file
  - Output: Paths to `vocals.wav` and `accompaniment.wav`

#### 2. `whisper-api`

- **POST /transcribe**
  - Input: `.wav` (vocals only)
  - Output: Raw transcription (lyrics), language code

#### 3. `classifier-api`

- **POST /classify**
  - Input: `lyrics` (string)
  - Output: `{ prediction: "AI" | "Human", confidence: float }`

#### 4. `db-api` (Main Backend)

- Next.js or FastAPI

- **POST /api/analyze**

  - Accepts: `.mp3` and flags to control pipeline steps
  - Optional flags:
    - `run_demucs`: bool
    - `run_whisper`: bool
    - `run_classifier`: bool
    - `store_result`: bool
  - Orchestrates the above 3 services
  - Stores result in Postgres

- **GET /api/songs** — list all processed songs

- **GET /api/songs/:id** — full song result

- **POST /api/songs** — manually insert song/lyrics

- **DELETE /api/songs/:id** — delete a record

### 🖼️ Frontend Features

Built in Next.js, the frontend allows users to:

- View a list of previously analyzed songs with details (lyrics, AI verdict, etc.)
- Add a new song by uploading an `.mp3` file
- Select which steps to run for each upload:
  - ✅ Vocal separation (Demucs)
  - ✅ Transcription (Whisper)
  - ✅ AI classification
- View individual song result pages with full info and media playback
- UI toggles for selecting partial/full pipeline (e.g. "Just get vocals")
- Live **Processing Queue View**:
  - Shows current tasks in progress
  - Indicates which microservice is active for each song
  - Useful for debugging and tracking task progress

> ⚙️ Yes, microservices can run concurrently if jobs are queued and dispatched correctly. For example, you can process multiple songs at once by scaling containers (e.g., 2 `demucs-api`, 3 `whisper-api`, etc.) or using a job queue.

### 🛠 DevOps Stack

- **Containerization**: Docker for all services
- **Orchestration**: Docker Compose for local + Goodwill laptop
- **CI/CD**: GitHub Actions
  - On push to `main`, SSH into Linux host
  - Run `git pull && docker-compose up --build -d`
- **Database**: Postgres, internal service
- **Secrets**: .env files locally, GitHub Secrets in CI

### 🛡️ Network Security

- Microservices are **not exposed to the public**
- Only `frontend` (Next.js app) is accessible
- Services communicate internally via Docker network

### 🗺️ Future Ideas

- Add Redis queue and task manager (Celery or RQ)
- Add Nginx or Traefik as reverse proxy with TLS
- Add Prometheus + Grafana for container monitoring
- Optional migration to Kubernetes (K3s)

---

Let me know if you want to expand this into a README or generate actual code/stubs.

