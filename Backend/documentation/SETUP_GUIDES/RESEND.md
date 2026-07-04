# Resend Email Setup Guide

## Account Creation

1. Go to https://resend.com/
2. Click "Get Started" or "Sign Up"
3. Enter your email address
4. Verify your email address
5. Complete the registration process

## Obtaining API Key

1. After logging in, go to the Resend Dashboard
2. Click on "API Keys" in the left sidebar
3. Click "Create API Key"
4. Enter a name for your API key (e.g., "HRMS Backend")
5. Select the appropriate permissions:
   - **Full Access**: Can send emails and manage domains
   - **Restricted**: Limited permissions
6. Click "Create"
7. **IMPORTANT**: Copy the API key immediately - it won't be shown again

### Add to Environment Variables
```env
# .env file
RESEND_API_KEY=re_your_api_key_here
```

### API Key Format
- Starts with `re_` (e.g., `re_live_...` for production)
- Keep this secret and never commit it to version control

## Verifying Email Domain

### Add Domain
1. In Resend Dashboard, go to "Domains"
2. Click "Add Domain"
3. Enter your domain name (e.g., `yourdomain.com`)
4. Click "Add"

### Configure DNS Records
Resend will provide DNS records to add to your domain:

#### SPF Record
```
Type: TXT
Host: @
Value: v=spf1 include:amazonses.com ~all
```

#### DKIM Record
```
Type: TXT
Host: resend._domainkey
Value: [provided by Resend]
```

#### DMARC Record (Optional but Recommended)
```
Type: TXT
Host: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

### Verify Domain
1. Add all DNS records to your domain registrar
2. Wait for DNS propagation (can take up to 48 hours)
3. Click "Verify" in Resend Dashboard
4. Check that all records are verified

### DNS Propagation Check
```bash
# Check SPF record
dig TXT yourdomain.com

# Check DKIM record
dig TXT resend._domainkey.yourdomain.com

# Check DMARC record
dig TXT _dmarc.yourdomain.com
```

## Testing Email Sending

### Using curl
```bash
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer re_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "onboarding@yourdomain.com",
    "to": ["test@example.com"],
    "subject": "Test Email",
    "html": "<h1>Hello!</h1><p>This is a test email from Resend.</p>"
  }'
```

### Using Python
```python
import requests

def send_test_email():
    api_key = "re_your_api_key"
    
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "from": "onboarding@yourdomain.com",
            "to": ["test@example.com"],
            "subject": "Test Email",
            "html": "<h1>Hello!</h1><p>This is a test email from Resend.</p>"
        }
    )
    
    return response.json()
```

### Check Email Status
```bash
# Get email by ID
curl https://api.resend.com/emails/email_id_here \
  -H "Authorization: Bearer re_your_api_key"
```

## Free Tier Limits

### What's Included
- **100 emails per day**
- **1,000 emails per month**
- **1 domain verification**
- **Basic analytics**

### Rate Limits
- **10 requests per second** (API calls)
- **100 emails per day** (sending)

### Exceeding Limits
If you exceed the free tier:
- Emails will be queued
- You'll receive a notification
- Consider upgrading to a paid plan

### Monitoring Usage
1. In Resend Dashboard, go to "Analytics"
2. Check emails sent today
3. Check emails sent this month
4. Monitor bounce rates and complaints

## Common Issues

### API Key Not Working
- Ensure the key starts with `re_`
- Check for typos
- Verify the key has the correct permissions
- Check if the key is active (not revoked)

### Emails Not Delivering
1. Check the "Emails" tab in Resend Dashboard
2. Look for bounce messages
3. Verify the recipient email address
4. Check spam folder
5. Verify domain is properly configured

### Domain Verification Failed
1. Ensure all DNS records are added correctly
2. Wait for DNS propagation (up to 48 hours)
3. Use `dig` commands to verify records
4. Check for typos in DNS records

### Rate Limiting
- Reduce the number of API calls
- Implement exponential backoff
- Queue emails instead of sending immediately
- Consider upgrading to a paid plan

### Emails Going to Spam
1. Verify your domain is properly configured
2. Check SPF, DKIM, and DMARC records
3. Avoid spammy content
4. Maintain good sending practices
5. Monitor bounce rates

## Environment Variables Reference

```env
# Required
RESEND_API_KEY=re_your_api_key_here

# Optional (for sending emails)
RESEND_FROM_EMAIL=noreply@yourdomain.com
RESEND_SUPPORT_EMAIL=support@yourdomain.com
```

## Useful Resources

- Resend Documentation: https://resend.com/docs
- Resend Dashboard: https://resend.com/domains
- Email Best Practices: https://resend.com/docs/introduction/best-practices

## Example Email Templates

### Welcome Email
```python
def send_welcome_email(to_email: str, user_name: str):
    html_content = f"""
    <h1>Welcome to HRMS, {user_name}!</h1>
    <p>Your account has been created successfully.</p>
    <p>You can now log in and start using the system.</p>
    <p>If you have any questions, please contact support.</p>
    """
    
    return send_email(
        to=to_email,
        subject="Welcome to HRMS",
        html=html_content
    )
```

### Password Reset Email
```python
def send_password_reset_email(to_email: str, reset_link: str):
    html_content = f"""
    <h1>Password Reset Request</h1>
    <p>You requested to reset your password.</p>
    <p>Click the link below to reset your password:</p>
    <p><a href="{reset_link}">Reset Password</a></p>
    <p>This link will expire in 1 hour.</p>
    <p>If you didn't request this, please ignore this email.</p>
    """
    
    return send_email(
        to=to_email,
        subject="Password Reset Request",
        html=html_content
    )
```
