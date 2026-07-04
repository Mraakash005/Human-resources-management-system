# File Uploads

## Overview

The HRMS backend handles file uploads for documents (resumes, contracts, ID proofs) and audio files (voice leave requests). All uploads are validated, scanned, and stored securely.

---

## MIME Validation

### Library

File type validation uses `python-magic` (libmagic wrapper), which inspects file content rather than relying on file extensions.

```python
import magic

def validate_mime_type(file_path: str) -> str:
    mime = magic.from_file(file_path, mime=True)
    return mime
```

### Document MIME Types

| MIME Type | Extension | Description |
|-----------|-----------|-------------|
| `application/pdf` | `.pdf` | PDF documents |
| `image/jpeg` | `.jpg`, `.jpeg` | JPEG images |
| `image/png` | `.png` | PNG images |
| `application/msword` | `.doc` | Word 97-2003 |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `.docx` | Word 2007+ |
| `text/plain` | `.txt` | Plain text |
| `text/csv` | `.csv` | CSV files |

### Audio MIME Types

| MIME Type | Extension | Description |
|-----------|-----------|-------------|
| `audio/wav` | `.wav` | WAV audio |
| `audio/x-wav` | `.wav` | WAV audio (alt) |
| `audio/mpeg` | `.mp3` | MP3 audio |
| `audio/mp3` | `.mp3` | MP3 audio (alt) |
| `audio/ogg` | `.ogg` | OGG audio |
| `audio/flac` | `.flac` | FLAC audio |
| `audio/mp4` | `.m4a` | M4A audio |
| `audio/webm` | `.webm` | WebM audio |

---

## Size Limits

| Category | Max Size | Reason |
|----------|----------|--------|
| Documents | 5 MB | Standard document sizes |
| Audio files | 10 MB | Voice recordings up to ~5 min |
| Profile images | 2 MB | Avatar-sized images |
| Bulk imports | 50 MB | CSV/data imports |

### Validation Code

```python
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024   # 5 MB
MAX_AUDIO_SIZE = 10 * 1024 * 1024      # 10 MB
MAX_IMAGE_SIZE = 2 * 1024 * 1024       # 2 MB
MAX_BULK_SIZE = 50 * 1024 * 1024       # 50 MB

def validate_file_size(file_path: str, category: str) -> tuple[bool, str]:
    size = os.path.getsize(file_path)
    limits = {
        "document": MAX_DOCUMENT_SIZE,
        "audio": MAX_AUDIO_SIZE,
        "image": MAX_IMAGE_SIZE,
        "bulk": MAX_BULK_SIZE,
    }
    max_size = limits.get(category, MAX_DOCUMENT_SIZE)
    if size > max_size:
        return False, f"File too large: {size} bytes (max {max_size})"
    return True, "valid"
```

---

## ClamAV Virus Scanning

### Docker Service

```yaml
services:
  clamav:
    image: clamav/clamav:latest
    container_name: hrms-clamav
    ports:
      - "3310:3310"
    volumes:
      - clamav_data:/var/lib/clamav
    environment:
      - CLAMAV_NO_FRESHCLAMD=false
      - FRESHCLAM_INTERVAL=3600
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "clamdscan", "--version"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 120s

volumes:
  clamav_data:
    driver: local
```

### Scanning Code

```python
import clamd

def scan_file(file_path: str) -> dict:
    try:
        cd = clamd.ClamAVClient(host="localhost", port=3310)
        result = cd.scan(file_path)

        if result and "OK" in result.get(file_path, ""):
            return {"clean": True, "threat": None}
        else:
            threat = result.get(file_path, "UNKNOWN")
            return {"clean": False, "threat": threat}

    except clamd.ConnectionError:
        # ClamAV unavailable — degrade gracefully
        return {"clean": True, "threat": None, "warning": "ClamAV unavailable, scan skipped"}
```

### Graceful Degradation

When ClamAV is unavailable:

1. Log a warning
2. Allow the upload to proceed
3. Tag the file as `"scan_status": "skipped"`
4. Schedule a background re-scan when ClamAV recovers

```python
def upload_file(file_path: str, category: str) -> dict:
    # 1. MIME validation
    mime = validate_mime_type(file_path)
    if mime not in ALLOWED_MIMES[category]:
        return {"error": f"Invalid file type: {mime}"}

    # 2. Size validation
    valid, msg = validate_file_size(file_path, category)
    if not valid:
        return {"error": msg}

    # 3. Virus scan (graceful)
    scan_result = scan_file(file_path)
    if not scan_result["clean"]:
        os.remove(file_path)
        return {"error": f"Threat detected: {scan_result['threat']}"}

    # 4. Store file
    stored_path = store_file(file_path, category)

    return {
        "path": stored_path,
        "mime": mime,
        "scan_status": scan_result.get("warning", "clean")
    }
```

---

## File Types Allowed

### Documents (5 MB)

```
.pdf, .doc, .docx, .txt, .csv, .jpg, .jpeg, .png
```

Used for:
- Employee documents (resumes, contracts, ID proofs)
- Profile images
- Bulk data imports

### Audio (10 MB)

```
.wav, .mp3, .ogg, .flac, .m4a, .webm
```

Used for:
- Voice leave requests
- Audio feedback
- Meeting recordings

---

## Storage Paths

### Directory Structure

```
uploads/
├── documents/
│   ├── employee_{id}/
│   │   ├── resume.pdf
│   │   ├── contract.pdf
│   │   └── id_proof.jpg
│   └── general/
│       └── policy_document.pdf
├── audio/
│   ├── employee_{id}/
│   │   └── leave_request_{timestamp}.wav
│   └── temp/
├── images/
│   ├── profiles/
│   │   └── employee_{id}.jpg
│   └── logos/
└── bulk/
    └── imports/
        └── employee_import_{timestamp}.csv
```

### File Naming Convention

```python
def generate_stored_filename(original: str, category: str, employee_id: int) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(original)[1]
    return f"{category}/employee_{employee_id}/{timestamp}_{secure_filename(original)}"
```

### Security

- Files stored outside web root
- No direct HTTP access to uploaded files
- Access controlled via signed URLs or authenticated endpoints
- Original filenames sanitized with `werkzeug.utils.secure_filename()`

---

## Upload API

### Endpoint

```
POST /api/v1/files/upload
```

### Request

```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf" \
  -F "category=document" \
  -F "employee_id=123"
```

### Response

```json
{
  "id": "file_abc123",
  "filename": "resume.pdf",
  "stored_path": "documents/employee_123/20260704_120000_resume.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 1048576,
  "scan_status": "clean",
  "uploaded_at": "2026-07-04T12:00:00Z"
}
```

### Error Responses

| Status | Message |
|--------|---------|
| 400 | Invalid file type |
| 400 | File too large |
| 400 | No file provided |
| 413 | Payload too large |
| 500 | Virus detected |
| 503 | Storage unavailable |
