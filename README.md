<p align="center">
  <img src="app/static/images/logo.png" width="180" alt="CipherVision Logo">
</p>

<h1 align="center">CipherVision</h1>

<p align="center">
  <strong>AI-Powered Invisible Watermarking for Digital Ownership Protection</strong>
</p>

<p align="center">
  Protect digital artwork, photography, and creative assets using deep neural watermarking.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?logo=bootstrap)

</p>

---

## Overview

CipherVision is a full-stack AI-powered web application that enables creators to securely protect and verify ownership of digital images using invisible neural watermarking.

Unlike traditional visible watermarks that can be cropped, edited, or degrade image quality, CipherVision embeds an imperceptible ownership identifier directly into an image using a deep learning model. This identifier can later be extracted to authenticate ownership while preserving the original visual appearance of the image.

The platform combines artificial intelligence, computer vision, secure authentication, cloud databases, and modern web technologies into a complete digital ownership verification system.

## AI Model

CipherVision integrates the **PixelSeal** pretrained deep neural watermarking model for invisible image watermark embedding and extraction.

The model is loaded through Meta's `videoseal` library and its pretrained checkpoint is fetched via the Hugging Face Hub at runtime (not bundled in the repo). It is responsible for embedding an imperceptible ownership payload into an image and recovering it during verification. CipherVision extends this capability by integrating secure ownership management, BCH error correction, Google OAuth authentication, duplicate watermark detection, and a complete web application for digital ownership verification.

## Problem Statement

Digital artwork is shared across the internet at an unprecedented scale, making unauthorized copying, redistribution, and ownership disputes increasingly common.

Conventional watermarking techniques suffer from several limitations:

- Visible watermarks reduce visual quality.
- Watermarks can often be cropped or removed.
- Ownership verification usually depends on external metadata that can be altered or lost.

CipherVision addresses these challenges by embedding ownership information directly into image pixels using deep neural watermarking, enabling reliable ownership verification without affecting image quality.

---

## Features

### AI-Powered Invisible Watermarking
Embeds an invisible ownership identifier into digital images using a deep neural network, with no visible impact on image quality.

### Ownership Verification
Extracts embedded ownership information from protected images and verifies the registered owner against the database.

### Duplicate Watermark Prevention
Before embedding, CipherVision automatically analyzes uploaded images to determine whether they already contain ownership information.

If an existing watermark is detected:
- If it belongs to the current user, embedding is skipped and they're informed the image is already protected under their account.
- If it belongs to someone else, embedding is blocked and an ownership conflict message is shown.
- Ownership-overwriting attacks are prevented either way.

### Privacy-Aware Verification
Verification results display:
- Profile picture
- Owner's full name

The registered email address is revealed only when the authenticated owner verifies their own image.

### Secure Authentication
- Google OAuth 2.0
- JWT-based authentication
- Secure HTTP-only cookies
- Protected routes

### Modern User Experience
- Responsive dashboard
- Drag-and-drop image upload
- Upload progress indicators
- Loading animations
- Success and verification modals
- Mobile-friendly interface

---

## Technology Stack

### Backend
- FastAPI
- Uvicorn
- Jinja2 (`fastapi.templating`)
- Starlette `SessionMiddleware`
- python-dotenv
- python-multipart (file uploads)

### Database
- SQLAlchemy (ORM, `DeclarativeBase`)
- PostgreSQL (via `psycopg2-binary`)

### Authentication
- Google OAuth 2.0 (Authlib's `starlette_client`)
- JWT (`python-jose`)
- HTTP-only cookie sessions

### AI / Watermarking
- PyTorch + Torchvision
- `videoseal` (loads the pretrained PixelSeal checkpoint via `setup_model_from_checkpoint`)
- `huggingface-hub` (checkpoint retrieval)
- Pillow + NumPy (image I/O and tensor conversion)
- `bchlib` (BCH error correction for the encoded payload)

### Frontend
- Jinja2-rendered HTML templates
- Bootstrap 5.3.7 (via CDN)
- Google Fonts (Manrope, Parisienne)
- Vanilla JavaScript (upload interactions in `embed.html` / `verify.html`)

### Rate Limiting / Abuse Prevention
- SlowAPI (`Limiter`, per-route rate limits on `/embed` and `/verify`)

---

## System Architecture

```text
                        +----------------------+
                        |     Google OAuth     |
                        +----------+-----------+
                                   |
                                   v
                        +----------------------+
                        |      FastAPI App     |
                        +----------+-----------+
                                   |
            +----------------------+----------------------+
            |                                             |
            v                                             v
+---------------------------+                +---------------------------+
| Authentication Service    |                | Watermark Service         |
| JWT & Session Management  |                | Embed / Verify Pipeline   |
+---------------------------+                +-------------+-------------+
                                                           |
                             +-----------------------------+----------------------------+
                             |                                                          |
                             v                                                          v
                  Neural Watermark Encoder                               Neural Watermark Decoder
                             |                                                          |
                             +-----------------------------+----------------------------+
                                                           |
                                                           v
                                                 PostgreSQL Database
```

---

## Project Structure

```text
CipherVision/
│
├── app/
│   ├── api/                 # Route handlers (auth, dashboard, embed, verify)
│   ├── auth/                # Google OAuth (Authlib) + JWT helpers
│   ├── core/                # PixelSeal model loading (videoseal)
│   ├── database/            # SQLAlchemy models and CRUD operations
│   ├── services/            # Embed/detect services, BCH payload encode/decode
│   ├── static/               # CSS, JS, images
│   ├── templates/           # Jinja2 templates (login, dashboard, embed, verify)
│   └── main.py               # FastAPI app, middleware, router registration
│
├── scripts/                  # Dev/maintenance scripts (create_tables, BCH & JWT
│                              # tests, DB/CRUD checks) — not a pytest test suite
│
├── requirements.txt
└── README.md
```

Uploaded files and generated watermarked images are written to the system temp
directory at request time (`tempfile`), not to project folders. `.env` (secrets)
and the downloaded PixelSeal checkpoint are gitignored and not part of the repo.

---

## Core Workflow

```text
                Google Sign-In
                       |
                       v
                User Dashboard
                       |
          +------------+------------+
          |                         |
          v                         v
   Embed Watermark           Verify Ownership
          |                         |
          v                         v
Duplicate Watermark         Decode Watermark
      Detection                    |
          |                        v
          v                 BCH Error Correction
Generate Owner ID                  |
          |                        v
          v                 Retrieve Owner Details
Neural Watermarking                |
          |                        v
          v                 Display Verification
 Download Protected Image
```

---

## Installation and Setup

### Prerequisites
- Python 3.11+
- PostgreSQL database (any provider — connected via `DATABASE_URL`)
- Google Cloud project with OAuth 2.0 credentials

### Steps

```bash
# Clone the repository
git clone https://github.com/<your-username>/CipherVision.git
cd CipherVision

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Create a .env file in the project root with:
#   DATABASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET, ENV

# Create the database tables
python scripts/create_tables.py

# Start the application
uvicorn app.main:app --reload
```

The application will be available at `http://localhost:8000`. On first run, the
PixelSeal checkpoint is downloaded automatically via `videoseal`/Hugging Face Hub.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Login / landing page |
| GET | `/login` | Redirects to Google OAuth consent screen |
| GET | `/auth/callback` | Handles OAuth callback, creates/looks up the user, and sets the JWT cookie |
| GET | `/logout` | Clears the session cookie and logs the user out |
| GET | `/dashboard` | Authenticated user's dashboard |
| GET | `/embed` | Embed page (requires auth) |
| POST | `/embed` | Uploads an image, checks for an existing watermark, embeds a new one, and stores a `Watermark` record |
| GET | `/download/{filename}` | Downloads the generated watermarked image |
| GET | `/verify` | Verify page (requires auth) |
| POST | `/verify` | Uploads an image, extracts and BCH-decodes the payload, and returns owner details |

---

## Database Schema (Overview)

```text
Users
------------------
id (PK, UUID)
google_id (unique)
email (unique)
full_name
picture_url
owner_id (unique, 16-char identifier — assigned once per user)
created_at

Watermarks
------------------
id (PK)
user_id (FK -> Users.id)
filename
owner_identifier (matches the owning user's owner_id)
verified_count
created_at
```

Note: `owner_id` is generated once per user at account creation and reused for
every image they protect — it is not regenerated per watermark. The BCH-encoded
payload itself is computed on the fly during embed/verify and is not persisted.

---

## Security Considerations

- All uploaded images pass extension, MIME type, and Pillow-based validation before processing.
- File size limits are enforced to prevent abuse.
- SlowAPI rate limiting protects endpoints from brute-force and abuse patterns.
- Sessions use secure, HTTP-only cookies in production.
- Ownership data is disclosed under strict privacy rules: only name and profile picture are shown to third parties; email is revealed only to the verified owner.
- Duplicate watermark detection prevents ownership-overwriting attacks.

---

## Future Enhancements

- Improve neural watermark robustness against aggressive compression and cropping
- Add batch upload and bulk verification
- Support video watermarking in addition to images
- Add API key access for programmatic/third-party integrations
- Add key rotation and revocation for ownership identifiers

---

## Acknowledgements

CipherVision uses the pretrained **PixelSeal** neural watermarking model for invisible watermark embedding and extraction.

We acknowledge the authors of PixelSeal for their contribution to neural image watermarking research.
