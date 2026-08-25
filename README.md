# StreamWave Serverless Media Platform

Academic prototype of a serverless media streaming application built for **StreamWave Entertainment** (a fictional Zimbabwean entertainment company). Constructed with **Python 3.12** and **FastAPI**, engineered specifically for deployment on **Vercel Functions** with **Vercel Blob Storage**, **5-Second MP4 Video Previews**, **Academic Payment Simulation**, and **Signed Cookie Access Control**.

---

## 🔒 Security & Payment Simulation Disclaimer

> [!IMPORTANT]
> **ACADEMIC SIMULATION NOTICE**
> - **Simulated Payment Gateway**: The payment checkout on `/checkout` is a pure academic simulation for assessment verification. No real money or credit card transactions take place, and no external payment gateway API (Stripe, EcoCash, PayPal, Visa/MasterCard API) is contacted.
> - **Zero Financial Data Collection**: Users are explicitly instructed not to enter genuine financial information. The backend accepts and logs ONLY the customer email address, plan ID, and selected method name (`ecocash`, `visa`, or `mastercard`). Mobile numbers, card numbers, expiry dates, and CVVs are never transmitted, logged, or stored.
> - **Demonstration Membership Cookie**: Successful simulated payments issue an HMAC-SHA256 signed HTTP-only cookie (`streamwave_session`) representing a demonstration membership. Any attempt to alter or tamper with the cookie payload immediately invalidates access (HTTP 401 Unauthorized).
> - **Static Asset DRM Limitations**: Demonstration audio (`/media/demo.wav`) and movie video previews (`/media/streamwave-preview.mp4`) are served directly as static assets for academic demonstration. This prototype does not implement commercial Digital Rights Management (DRM) or encrypted media streaming.
> - **Production Requirements**: A production-grade commercial platform would require an authorized payment processor integration (e.g., EcoCash merchant API, Stripe), a persistent database (PostgreSQL/MongoDB), private object storage (AWS S3 / Vercel Blob with signed URLs), widevine/PlayReady DRM media encryption, and formal third-party security auditing.

---

## 🚀 Key Features & Architectural Highlights

- **Vercel Serverless Native**: Designed without continuous background processes, SQLite, or runtime filesystem writes to respect Vercel's read-only/ephemeral execution model.
- **Public Landing Page (`/`)**: Original Zimbabwean streaming hero showcase (*"Zimbabwe’s stories, music and movies — all in one place."*), membership email registration, benefits grid, how-it-works workflow, and supported payment badges.
- **Academic Simulated Checkout (`/checkout`)**: Supports EcoCash (`077 000 0000`), Visa (`4242`), and MasterCard (`4444`) with interactive step sequence progress animations, simulated approval (`SW-DEMO-XXXXX` reference), and simulated decline testing.
- **Protected Member Library (`/library`)**: Gated access requiring a valid signed `streamwave_session` cookie. Protected endpoints (`/api/media`, `/api/media/{id}`, `/api/play-events`) reject unauthenticated requests with HTTP 401.
- **5-Second Movie Video Preview**: Movie titles (*Cook Off*, *Neria*, *Gonarezhou*, *Shaina*) present a 5-second StreamWave MP4 video preview (`/media/streamwave-preview.mp4`) in a dedicated modal player upon clicking **"▶ Watch"**.
- **Music Audio Demonstration**: Music items utilize the fixed HTML5 audio player (`/media/demo.wav` or Vercel Blob CDN) upon clicking **"▶ Play"**.
- **Structured Logged Playback & Payment Events**: Emits structured JSON telemetry directly to standard logger outputs without ephemeral filesystem writes.

---

## ☁️ Vercel Blob Integration & Setup

Reference Documentation:
- [Vercel Blob Overview](https://vercel.com/docs/vercel-blob)
- [Vercel CLI Blob Documentation](https://vercel.com/docs/cli/blob)

```bash
# Upload via Vercel CLI
npx vercel login
npx vercel blob upload public/media/streamwave-preview.mp4
```

---

## 📂 Project Structure

```
.
├── app.py                      # FastAPI entry point, plan config, signed cookies & access control
├── data/
│   └── media.json              # Read-only Zimbabwean media catalogue
├── public/
│   ├── index.html              # Public StreamWave landing page
│   ├── checkout.html           # Simulated academic checkout page (EcoCash, Visa, MasterCard)
│   ├── library.html            # Protected member catalogue & media player page
│   ├── css/
│   │   └── styles.css          # Responsive dark graphite stylesheet & modal styling
│   ├── js/
│   │   └── app.js              # Frontend logic, protected API client & media player
│   ├── images/
│   │   ├── streamwave-logo.png # Official StreamWave brand logo
│   │   └── favicon.png         # Browser tab icon
│   ├── media/
│   │   ├── demo.wav            # Generated demonstration WAV audio asset
│   │   └── streamwave-preview.mp4 # 5-second StreamWave MP4 video preview asset
│   └── favicon.ico             # Browser icon fallback
├── scripts/
│   ├── copy_preview_video.py   # Utility locating and copying streamwave-preview.mp4
│   ├── create_favicon.py       # Utility creating favicon assets from brand logo
│   ├── generate_demo_audio.py  # Python script generating synthesized WAV chime
│   └── run_tests.py            # Automated test runner executing pytest programmatically
├── tests/
│   └── test_api.py             # Pytest suite covering landing, checkout, session cookies, 401s
├── pyproject.toml              # Python 3.12 environment & tool configurations
├── requirements.txt            # Pinned dependencies (FastAPI, Uvicorn, Pydantic, Pytest, HTTPX)
├── .gitignore                  # Source control ignore file
└── README.md                   # Technical documentation & security disclaimer
```

---

## 🛠️ Local Execution & Testing

### Run Automated Tests
```bash
.venv\Scripts\python.exe -m pytest tests/test_api.py -v
```

### Start Development Server
```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8001
```

- Public Landing Page: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)
- Simulated Checkout Page: [http://127.0.0.1:8001/checkout](http://127.0.0.1:8001/checkout)
- Member Library Page: [http://127.0.0.1:8001/library](http://127.0.0.1:8001/library)
- OpenAPI Swagger Docs: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
