# Resend Email Service Setup

## Overview

Resend is used for transactional email delivery in the HRMS backend. It provides a simple API for sending emails with high deliverability.

---

## Account Creation

1. Visit [resend.com](https://resend.com)
2. Sign up for a free account
3. Verify your email address
4. Complete account setup

### Domain Verification (Production)

1. Add your domain in the Resend dashboard
2. Configure DNS records (SPF, DKIM, DMARC)
3. Wait for verification (usually < 24 hours)
4. Use `noreply@yourdomain.com` as the sender

---

## API Key Setup

### Create API Key

1. Go to **Settings → API Keys**
2. Click **Create API Key**
3. Name: `hrms-production` (or `hrms-development`)
4. Permission: **Full Access** or **Send Access**
5. Copy the key immediately (shown only once)

### Environment Variable

```bash
# .env
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Never Commit API Keys

```python
# Correct — loaded from environment
api_key = os.environ.get("RESEND_API_KEY")

# Wrong — hardcoded key (NEVER do this)
api_key = "re_abc123..."
```

---

## Email Templates

### Welcome Email

Triggered when a new employee is added to the system.

**Template variables:**
- `{{employee_name}}` — Full name of the employee
- `{{department}}` — Department name
- `{{start_date}}` — Employment start date
- `{{manager_name}}` — Direct manager's name
- `{{login_url}}` — URL to the employee portal

**Subject:** Welcome to {{company_name}}, {{employee_name}}!

**Content:**
```html
<h2>Welcome to the team, {{employee_name}}!</h2>
<p>We're excited to have you join the <strong>{{department}}</strong> team.</p>
<p>Your employment begins on <strong>{{start_date}}</strong>.</p>
<p>Your manager, {{manager_name}}, will reach out with onboarding details.</p>
<p>
  <a href="{{login_url}}" style="background:#0066cc;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">
    Access Your Portal
  </a>
</p>
```

### Leave Notification

Triggered when a leave request is submitted, approved, or rejected.

**Template variables:**
- `{{employee_name}}` — Employee name
- `{{leave_type}}` — Type of leave
- `{{start_date}}` — Leave start date
- `{{end_date}}` — Leave end date
- `{{status}}` — pending / approved / rejected
- `{{approver_name}}` — Manager who approved/rejected
- `{{reason}}` — Leave reason (if provided)

**Subject:** Leave Request {{status}} — {{leave_type}}

**Content:**
```html
<h3>Leave Request Update</h3>
<table>
  <tr><td>Employee:</td><td>{{employee_name}}</td></tr>
  <tr><td>Type:</td><td>{{leave_type}}</td></tr>
  <tr><td>Dates:</td><td>{{start_date}} to {{end_date}}</td></tr>
  <tr><td>Status:</td><td style="color:{{status_color}};">{{status}}</td></tr>
  {{#if approver_name}}
  <tr><td>Reviewed by:</td><td>{{approver_name}}</td></tr>
  {{/if}}
</table>
```

### Pay Stub Notification

Triggered when a new pay stub is generated.

**Template variables:**
- `{{employee_name}}` — Employee name
- `{{pay_period}}` — Pay period (e.g., "June 1-15, 2026")
- `{{gross_pay}}` — Gross pay amount
- `{{net_pay}}` — Net pay amount
- `{{pay_date}}` — Payment date
- `{{pay_stub_url}}` — URL to download pay stub

**Subject:** Your pay stub for {{pay_period}} is ready

**Content:**
```html
<h3>Pay Stub Available</h3>
<p>Hi {{employee_name}},</p>
<p>Your pay stub for <strong>{{pay_period}}</strong> is now available.</p>
<table>
  <tr><td>Gross Pay:</td><td>{{gross_pay}}</td></tr>
  <tr><td>Net Pay:</td><td><strong>{{net_pay}}</strong></td></tr>
  <tr><td>Pay Date:</td><td>{{pay_date}}</td></tr>
</table>
<p>
  <a href="{{pay_stub_url}}" style="background:#0066cc;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">
    Download Pay Stub
  </a>
</p>
```

### Burnout Alert

Triggered when the burnout detection system identifies a high-risk employee.

**Template variables:**
- `{{employee_name}}` — Employee name
- `{{risk_level}}` — low / medium / high
- `{{risk_score}}` — Numeric score (0-100)
- `{{recommendation}}` — AI-generated recommendation
- `{{hr_contact}}` — HR contact email

**Subject:** Wellness Check Recommended — {{employee_name}}

**Content:**
```html
<h3>Employee Wellness Alert</h3>
<p>A wellness check is recommended for <strong>{{employee_name}}</strong>.</p>
<table>
  <tr><td>Risk Level:</td><td style="color:red;">{{risk_level}}</td></tr>
  <tr><td>Score:</td><td>{{risk_score}}/100</td></tr>
  <tr><td>Recommendation:</td><td>{{recommendation}}</td></tr>
</table>
<p>Please follow up with the employee or contact <a href="mailto:{{hr_contact}}">{{hr_contact}}</a>.</p>
```

---

## Retry Logic

### Configuration

| Parameter | Value |
|-----------|-------|
| Max retries | 3 |
| Initial delay | 1 second |
| Backoff multiplier | 2x |
| Max delay | 10 seconds |

### Implementation

```python
import resend
import time
import os

MAX_RETRIES = 3
INITIAL_DELAY = 1
BACKOFF_MULTIPLIER = 2

resend.api_key = os.environ.get("RESEND_API_KEY")

def send_email(to: str, subject: str, html: str) -> dict:
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            result = resend.Emails.send({
                "from": "HRMS <noreply@yourdomain.com>",
                "to": [to],
                "subject": subject,
                "html": html,
            })
            return {"success": True, "id": result["id"]}

        except resend.errors.RateLimitError as e:
            delay = INITIAL_DELAY * (BACKOFF_MULTIPLIER ** attempt)
            time.sleep(delay)
            last_error = e

        except resend.errors.ValidationError as e:
            # Don't retry validation errors
            return {"success": False, "error": str(e)}

        except Exception as e:
            delay = INITIAL_DELAY * (BACKOFF_MULTIPLIER ** attempt)
            time.sleep(delay)
            last_error = e

    return {"success": False, "error": f"Failed after {MAX_RETRIES} attempts: {last_error}"}
```

---

## Free Tier Limits

| Limit | Value |
|-------|-------|
| Emails per day | 100 |
| Emails per month | 3,000 |
| Domains | 1 |
| Team members | 1 |
| API rate limit | 10 requests/second |

### Rate Limit Handling

```python
def check_daily_limit() -> dict:
    """Track emails sent today to stay under free tier limit."""
    today = datetime.now().date()
    count = db.query(EmailLog).filter(
        EmailLog.sent_at >= today
    ).count()

    return {
        "sent_today": count,
        "remaining": max(0, 100 - count),
        "limit_reached": count >= 100
    }
```

### Upgrade Path

When approaching limits, the system logs a warning:

```python
if remaining < 20:
    logger.warning(f"Resend free tier: only {remaining} emails remaining today")
```

---

## Environment Variables

```bash
# Required
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional (defaults shown)
RESEND_FROM_EMAIL=noreply@yourdomain.com
RESEND_FROM_NAME=HRMS
RESEND_REPLY_TO=hr@yourdomain.com

# Rate limiting
RESEND_MAX_RETRIES=3
RESEND_RETRY_DELAY=1
RESEND_DAILY_LIMIT=100
```

### Configuration Class

```python
class ResendConfig:
    api_key: str = os.environ.get("RESEND_API_KEY", "")
    from_email: str = os.environ.get("RESEND_FROM_EMAIL", "noreply@yourdomain.com")
    from_name: str = os.environ.get("RESEND_FROM_NAME", "HRMS")
    reply_to: str = os.environ.get("RESEND_REPLY_TO", "hr@yourdomain.com")
    max_retries: int = int(os.environ.get("RESEND_MAX_RETRIES", "3"))
    daily_limit: int = int(os.environ.get("RESEND_DAILY_LIMIT", "100"))
```

---

## Testing

### Development Mode

Use Resend's test email feature:

```bash
# Send to any address (won't actually deliver)
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer re_test_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "onboarding@resend.dev",
    "to": ["delivered@resend.dev"],
    "subject": "Test Email",
    "html": "<p>This is a test.</p>"
  }'
```

### Mock in Tests

```python
@pytest.fixture
def mock_resend(monkeypatch):
    monkeypatch.setattr(resend.Emails, "send", lambda x: {"id": "test_email_123"})
```
