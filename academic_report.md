# Technical Report: Implementation of the StreamWave Serverless Media Platform Prototype

**Course / Assessment**: Senior Cloud Engineering Prototype Assessment  
**Project Title**: StreamWave Serverless Media Platform  
**Target Platform**: Vercel Serverless Functions & Vercel Blob Storage  
**Runtime**: Python 3.12 / FastAPI Framework  

---

## 1. Title of the Practical Solution
**StreamWave Serverless Media Platform**: An Academic Serverless Cloud Prototype for Media Cataloguing, Direct Asset Delivery, and Telemetry Event Ingestion using FastAPI and Vercel.

---

## 2. Purpose of the Implementation
The primary objective of this implementation is to design, construct, test, and deploy a responsive, event-driven web application prototype for a fictional Zimbabwean entertainment enterprise named **StreamWave Entertainment**. 

As digital content consumption expands across Southern Africa, media streaming platforms require cloud architectures that minimize infrastructure overhead, eliminate continuous compute costs during idle periods, and scale dynamically in response to erratic traffic bursts (FastAPI 2024). This project demonstrates how an enterprise media cataloguing and streaming platform can be hosted on serverless infrastructure without deploying traditional dedicated virtual machines, container orchestrators (e.g., Docker, Kubernetes), or continuously running database engines.

The prototype showcases:
1. Low-latency media catalogue retrieval filtered by type, genre, and search queries.
2. Serverless handling of client playback telemetry events using structured Python runtime logging (Vercel 2024c).
3. Direct static media delivery via edge networks and Vercel Blob storage, bypassing application server compute overhead (Vercel 2024d).

---

## 3. Justification for Selecting Vercel and FastAPI

### 3.1 FastAPI Framework Justification
FastAPI was selected as the backend Python web framework due to its high performance, native asynchronous support (`async/await`), automatic OpenAPI (`/docs`) schema generation, and strict data validation powered by Pydantic (FastAPI 2024). 

Compared to micro-frameworks such as Flask or full-stack monoliths like Django, FastAPI enforces type hints at runtime. This guarantees that malformed HTTP requests—such as missing parameters or excessively long payloads—are intercepted and rejected with HTTP `422 Unprocessable Entity` status codes before reaching business logic. Furthermore, FastAPI's lightweight memory footprint enables near-instantaneous cold starts when executed inside ephemeral serverless container environments (Vercel 2024b).

### 3.2 Vercel Serverless Platform Justification
Vercel was chosen as the cloud execution environment because of its zero-configuration Python serverless runtime and global Content Delivery Network (CDN) edge network (Vercel 2024a). 

Traditional server architectures require continuously running instances (e.g., AWS EC2 or Nginx on Ubuntu), incurring baseline running costs regardless of incoming user traffic. In contrast, Vercel Functions execute code on-demand within ephemeral micro-VM runtimes. This architectural model reduces operational maintenance and optimizes resource utilization for non-commercial academic demonstrations hosted on free-tier infrastructure (Vercel 2024a).

---

## 4. Functional Requirements Implemented

The platform fulfills the following core functional capabilities:
- **Media Catalogue Presentation**: Displays a curated catalogue of Zimbabwean entertainment assets including movies (*Cook Off*, *Neria*, *Gonarezhou*, *Shaina*) and music releases (*Winky D - Disappear*, *Jah Prayzah - Mudhara Vachida*, *Stella Chiweshe - Mbira Magic*, *Ammara Brown - Akiliz*).
- **Multi-Criteria Search & Filtering**: Provides real-time text query searching alongside filter controls for media type (`movie`, `music`) and genre (`Comedy`, `Drama`, `Action`, `Zimdancehall`, `Afro-pop`, `Traditional`).
- **Accessible Media Detail Inspection**: Implements an accessible HTML5 `<dialog>` modal interface presenting detailed descriptions, director/artist metadata, duration, release year, and media identifiers.
- **Client-Side Demonstration Audio Playback**: Integrates an HTML5 `<audio>` player capable of streaming a custom non-copyrighted synthesized WAV audio chime directly from static storage or Vercel Blob Storage (Vercel 2024d).
- **Structured Playback Telemetry**: Ingests `POST /api/play-events` requests, validates media presence, attaches server-side ISO 8601 UTC timestamps, and emits structured JSON event logs to Vercel runtime logs (Vercel 2024c).

---

## 5. Architecture and Explanation of Components

```
+-----------------------------------------------------------------------------------+
|                                 CLIENT BROWSER                                    |
|   (Vanilla JS App / HTML5 Audio Player / Responsive Dark Graphite CSS Interface)  |
+----------------------------------------+------------------------------------------+
                                         |
               +-------------------------+-------------------------+
               | HTTP GET (Static Assets)|                         | HTTP REST API (/api/*)
               v                         |                         v
+------------------------------+         |      +-----------------------------------+
|  VERCEL EDGE CDN / STORAGE   |         |      |    VERCEL SERVERLESS FUNCTION     |
|                              |         |      |             (app.py)              |
|  - public/index.html         |         |      |  - FastAPI 0.110 (Python 3.12)    |
|  - public/css/styles.css     |         |      |  - Pydantic v2 Validation         |
|  - public/js/app.js          |         |      |  - GET /api/health                |
|  - public/media/demo.wav     |         |      |  - GET /api/media                 |
|  - Vercel Blob Storage CDN   |         |      |  - GET /api/media/{id}            |
|    (Direct Media Bytes)      |         |      |  - POST /api/play-events          |
+------------------------------+         |      +-----------------+-----------------+
               ^                         |                        |
               |                         |                        | Structured JSON Logs
               +-------------------------+                        v
                  Direct Media Stream              +--------------------------------+
               (No FastAPI Compute Proxy)          |      VERCEL RUNTIME LOGS       |
                                                   |  (logger.info / Event Stream)  |
                                                   +--------------------------------+
```

### 5.1 System Component Breakdown

1. **`app.py` (Serverless Application Entry Point)**:
   Exposes the root `app = FastAPI(...)` object. It handles API routing, security response middleware (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`), and static file mounting fallback for local execution (Vercel 2024a).

2. **`data/media.json` (Read-Only Data Store)**:
   A static JSON document storing the media catalogue. In compliance with serverless constraints, this file is read-only and loaded using Python's `pathlib.Path`.

3. **`public/` (Static Frontend Web Interface)**:
   Contains `index.html`, `css/styles.css`, `js/app.js`, and `media/demo.wav`. The user interface features a dark graphite theme (`#121214`), restrained red accenting (`#e50914`), clean rectangular cards, and mobile/desktop responsive CSS Grid/Flexbox layouts.

4. **`scripts/generate_demo_audio.py` (Audio Synthesis Engine)**:
   A standard-library Python script utilizing `wave`, `struct`, and `math` to synthesize a 3-second PCM 16-bit 44.1kHz mono WAV musical chime, guaranteeing that no copyrighted commercial audio is used.

5. **`scripts/upload_to_vercel_blob.py` (Vercel Blob Storage Utility)**:
   An uploader script interfacing with the Vercel Blob REST API to upload non-copyrighted media assets to public cloud storage when a `BLOB_READ_WRITE_TOKEN` is supplied (Vercel 2024d).

---

## 6. Development and Deployment Procedure

### 6.1 Local Development Workflow
1. **Virtual Environment Setup**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. **Dependency Installation**: Pinned dependencies installed via `pip install -r requirements.txt`.
3. **Asset Generation**: Synthesized WAV asset generated via `python scripts/generate_demo_audio.py`.
4. **Automated Testing**: Test suite executed via `pytest tests/test_api.py -v`.
5. **Local Server Execution**: Local development server started using `uvicorn app:app --reload`.

### 6.2 Vercel Deployment Workflow
The project adheres to Vercel's zero-configuration FastAPI deployment process (Vercel 2024a):
1. Root [`app.py`](file:///C:/Users/dell/.gemini/antigravity/brain/228fe0bc-0a77-489e-a1ba-57d617247457/app.py) exports `app = FastAPI(...)`.
2. [`pyproject.toml`](file:///C:/Users/dell/.gemini/antigravity/brain/228fe0bc-0a77-489e-a1ba-57d617247457/pyproject.toml) defines `requires-python = ">=3.12, <3.13"`.
3. Obsolete `vercel.json` build definitions are omitted to prevent deployment conflicts.
4. Deployment is executed via Vercel CLI (`npx vercel --prod`) or Vercel GitHub integration.

---

## 7. Testing Performed and Actual Results

The automated test suite in [`tests/test_api.py`](file:///C:/Users/dell/.gemini/antigravity/brain/228fe0bc-0a77-489e-a1ba-57d617247457/tests/test_api.py) executes 10 test cases using Pytest and Starlette `TestClient`:

| Test Suite Case | Target Feature | Expected Behavior | Verification Status |
| :--- | :--- | :--- | :--- |
| `test_health_endpoint` | `GET /api/health` | Returns HTTP 200 OK, `status: "ok"`, platform string, and server UTC ISO timestamp. | **PASSED (200)** |
| `test_get_complete_media_catalogue` | `GET /api/media` | Returns HTTP 200 OK and array of 8 media objects with valid schema keys. | **PASSED (200)** |
| `test_media_search_filter_stream` | `GET /api/media?query=stream` | Filters items containing "stream" in metadata. | **PASSED (200)** |
| `test_media_type_filter_music` | `GET /api/media?type=music` | Returns 4 items matching `type == "music"`. | **PASSED (200)** |
| `test_media_genre_filter` | `GET /api/media?genre=Zimdancehall` | Returns items matching `genre == "Zimdancehall"`. | **PASSED (200)** |
| `test_get_valid_media_detail_id_1` | `GET /api/media/1` | Returns single `MediaItem` for ID `"1"` (*Cook Off*). | **PASSED (200)** |
| `test_get_unknown_media_detail_404` | `GET /api/media/999` | Returns HTTP 404 Not Found with error detail. | **PASSED (404)** |
| `test_valid_play_event` | `POST /api/play-events` | Accepts valid payload, generates server timestamp, returns HTTP 201 Created. | **PASSED (201)** |
| `test_play_event_unknown_media_404` | `POST /api/play-events` | Rejects unknown `media_id` with HTTP 404. | **PASSED (404)** |
| `test_play_event_invalid_body_422` | `POST /api/play-events` | Rejects missing body fields with HTTP 422 Unprocessable Entity. | **PASSED (422)** |

---

## 8. Security Controls Implemented

1. **Security Headers Middleware**: FastAPI injects defensive HTTP response headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`) on all routes.
2. **Pydantic Boundary Validation**: Maximum string length constraints (`max_length`) are strictly enforced on all path parameters, query strings, and POST request body fields.
3. **Same-Origin Policy**: Unrestricted CORS wildcard headers (`*`) are omitted since API endpoints and static frontend assets share the same Vercel origin.
4. **Secret Isolation & Git Protections**: Secrets (e.g., `BLOB_READ_WRITE_TOKEN`, `.env`) are excluded from version control via `.gitignore`.
5. **No Runtime Filesystem Writes**: Prevents unauthorized file write attacks on ephemeral serverless storage.

---

## 9. Evidence List (Numbered Screenshot Placeholders)

- **[Screenshot 1 Placeholder]**: Terminal execution output showing `pytest tests/test_api.py -v` passing 10/10 automated unit tests.
- **[Screenshot 2 Placeholder]**: Desktop web interface displaying StreamWave Entertainment header, hero release banner, search controls, and dark graphite media card grid.
- **[Screenshot 3 Placeholder]**: Mobile responsive view (<768px width) demonstrating collapsed toolbar, single-column media grid, and fixed bottom audio player.
- **[Screenshot 4 Placeholder]**: Open accessible `<dialog>` modal showing full metadata for *Cook Off*.
- **[Screenshot 5 Placeholder]**: Browser DevTools Network tab confirming direct static delivery of `/media/demo.wav` alongside active HTML5 playback.
- **[Screenshot 6 Placeholder]**: Interactive OpenAPI Swagger documentation at `/docs`.
- **[Screenshot 7 Placeholder]**: Vercel Project Dashboard indicating successful production deployment status.
- **[Screenshot 8 Placeholder]**: Vercel Runtime Log stream displaying structured JSON output from `POST /api/play-events`.

---

## 10. Integration into the Wider StreamWave Platform Architecture

In an enterprise production ecosystem, this serverless prototype would integrate into a broader cloud architecture as illustrated below:

```
[ Client Browser / Mobile App ]
              |
              +---> [ API Gateway / Cloudflare WAF ]
                          |
     +--------------------+--------------------+
     |                                         |
     v                                         v
[ Auth Service ]                     [ Serverless API Service ]
(OAuth2 / OIDC / JWT)                (FastAPI / Vercel / AWS Lambda)
                                               |
     +--------------------+--------------------+--------------------+
     |                    |                    |                    |
     v                    v                    v                    v
[ PostgreSQL / CockroachDB ] [ Kafka / EventBridge ] [ AWS CloudFront CDN ] [ DRMed HLS Video Transcoder ]
  (User / Media Database)    (Analytics Ingestion)   (Signed Cookie Access)  (AWS Elemental MediaConvert)
```

1. **Identity & Access Management**: Authentication via OAuth2 / OpenID Connect (OIDC) issuing JWT tokens.
2. **Persistent Database Systems**: Transition from static JSON files to distributed databases (e.g., PostgreSQL, CockroachDB) managed via SQLAlchemy ORM.
3. **Event Stream Ingestion**: Routing telemetry events from Vercel runtime logs to real-time analytics engines (Apache Kafka, AWS EventBridge, Datadog).
4. **Protected Content Delivery & DRM**: Video assets transcoded into adaptive bitrate HLS/DASH streams, encrypted with Widevine/FairPlay DRM, and served via AWS CloudFront with signed URLs.

---

## 11. Limitations of the Prototype

1. **Ephemeral Event Storage**: Playback events received at `POST /api/play-events` are logged to stdout and captured by Vercel runtime logs (Vercel 2024c); they are not stored in a persistent database.
2. **Static Catalogue**: Media metadata is read from a static `data/media.json` file. Updating media items requires a code commit and re-deployment.
3. **Demonstration Audio Assets**: All media catalogue entries reference the synthesized 3-second WAV chime for academic compliance.
4. **Hobby Tier Resource Caps**: Hosted on the non-commercial Vercel Hobby plan, subject to execution timeout caps (10 seconds per function call) and bandwidth quotas.

---

## 12. Conclusion

The **StreamWave Serverless Media Platform** successfully demonstrates how Python 3.12 and FastAPI can be deployed as serverless functions on Vercel to deliver a high-performance, cost-efficient media streaming architecture. By separating API logic from media asset distribution, the platform delivers sample media directly to users via static edge infrastructure while handling API requests through auto-scaling, ephemeral serverless compute. This academic prototype provides a foundational model for modern, event-driven cloud streaming applications.

---

## 13. References

- FastAPI (2024) *FastAPI Framework Features*. Available at: https://fastapi.tiangolo.com/features/ (Accessed: 25 August 2026).
- Vercel (2024a) *FastAPI Framework Guide on Vercel*. Available at: https://vercel.com/docs/frameworks/backend/fastapi (Accessed: 25 August 2026).
- Vercel (2024b) *Python Serverless Runtime Reference*. Available at: https://vercel.com/docs/functions/runtimes/python (Accessed: 25 August 2026).
- Vercel (2024c) *Vercel Runtime Logs Documentation*. Available at: https://vercel.com/docs/logs/runtime (Accessed: 25 August 2026).
- Vercel (2024d) *Vercel Blob Storage Documentation*. Available at: https://vercel.com/docs/vercel-blob (Accessed: 25 August 2026).
