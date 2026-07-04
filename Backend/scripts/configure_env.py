"""
HRMS Environment Configuration Script
Automates .env creation and third-party service setup.
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path


def generate_secret_key() -> str:
    return secrets.token_urlsafe(48)


def create_env_file(env_path: Path = Path(".env")) -> None:
    """Create .env file from template with generated secrets."""
    if env_path.exists():
        resp = input(f"{env_path} already exists. Overwrite? [y/N]: ")
        if resp.lower() != "y":
            print("Aborted.")
            return

    secret_key = generate_secret_key()
    postgres_password = secrets.token_urlsafe(16)

    env_content = f"""# HRMS Environment — Auto-generated
APP_NAME=HRMS Enterprise
APP_VERSION=3.0.0
ENVIRONMENT=development
DEBUG=true
SECRET_KEY={secret_key}
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

DATABASE_URL=postgresql+asyncpg://hrms:{postgres_password}@localhost:5432/hrms_db
REDIS_URL=redis://localhost:6379/0

CLERK_PUBLISHABLE_KEY=pk_test_REPLACE_ME
CLERK_SECRET_KEY=sk_test_REPLACE_ME
CLERK_JWT_VERIFICATION_KEY="-----BEGIN PUBLIC KEY-----\\nREPLACE_ME\\n-----END PUBLIC KEY-----"
CLERK_WEBHOOK_SECRET=whsec_REPLACE_ME

RESEND_API_KEY=re_REPLACE_ME
EMAIL_FROM=hrms@yourdomain.com
HR_EMAIL=hr@yourdomain.com

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3
OLLAMA_CHATBOT_MODEL=mistral
WHISPER_URL=http://localhost:9000
CLAMAV_URL=http://localhost:3310

R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=hrms-assets
R2_PUBLIC_BASE_URL=

OFFICE_LAT=12.9716
OFFICE_LNG=77.5946
GEOFENCE_RADIUS_METERS=150
COMPANY_NAME=Your Company Ltd

POSTGRES_PASSWORD={postgres_password}
"""

    env_path.write_text(env_content)
    print(f"✅ Created {env_path}")
    print(f"   PostgreSQL password: {postgres_password}")
    print()
    print("⚠️  NEXT STEPS:")
    print("   1. Fill in CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY")
    print("   2. Fill in CLERK_JWT_VERIFICATION_KEY (from Clerk dashboard)")
    print("   3. Fill in RESEND_API_KEY (from resend.com)")
    print("   4. Optionally fill in R2 credentials for profile pictures")
    print()


def create_ssl_directory() -> None:
    """Create SSL directory for nginx."""
    ssl_dir = Path("ssl")
    ssl_dir.mkdir(exist_ok=True)

    cert_path = ssl_dir / "cert.pem"
    key_path = ssl_dir / "key.pem"

    if not cert_path.exists() or not key_path.exists():
        print("Generating self-signed SSL certificate for development...")
        os.system(
            f"openssl req -x509 -newkey rsa:2048 -keyout {key_path} -out {cert_path} "
            f"-days 365 -nodes -subj '/CN=localhost' 2>/dev/null"
        )
        print(f"✅ Created {cert_path} and {key_path}")
    else:
        print(f"✅ SSL certificates already exist in {ssl_dir}/")


def main() -> None:
    print("═" * 60)
    print("  HRMS Environment Configuration")
    print("═" * 60)
    print()

    create_env_file()
    create_ssl_directory()

    print()
    print("═" * 60)
    print("  Configuration complete!")
    print("═" * 60)
    print()
    print("Next: docker compose up --build")


if __name__ == "__main__":
    main()
