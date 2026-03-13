# FAQ - Frequently Asked Support Questions

## Account and Access

### How do I create an account?
To create an account on our platform:
1. Go to our homepage and click "Sign Up"
2. Fill out the form with your name, email, and password
3. Verify your email by clicking the link we send you
4. That's it! You can now log in

The process takes less than 2 minutes and is completely free.

### How do I recover my password?
If you forgot your password:
1. Go to the login page
2. Click "Forgot your password?"
3. Enter your registered email
4. You will receive an email with a password reset link (valid for 1 hour)
5. Click the link and set a new password

If you do not receive the email within 5 minutes, check your spam folder.

### Can I change my email?
Yes, you can change your email from Settings > Profile > Email.
For security reasons, we will send a verification email to the new address.
The change is applied immediately after verification.

---

## Billing and Subscriptions

### What plans are available?
We offer three plans:

- **Basic Plan** ($9/month): Up to 1,000 queries/month, 1 user, email support
- **Professional Plan** ($29/month): Up to 10,000 queries/month, 5 users, priority support
- **Enterprise Plan** (custom pricing): Unlimited queries, unlimited users, guaranteed SLA, 24/7 support

All plans include a 14-day free trial with no credit card required.

### How do I cancel my subscription?
To cancel your subscription:
1. Go to Settings > Billing > My Plan
2. Click "Cancel subscription"
3. Select a cancellation reason (optional, but it helps us improve)
4. Confirm the cancellation

Your plan will remain active until the end of the billed period.
We do not provide partial refunds, but you keep full access until the expiration date.

### Can I switch plans at any time?
Yes. Plan changes are applied immediately:
- **Upgrade**: The prorated difference for the remaining time in the month is charged
- **Downgrade**: The new price applies starting with the next billing cycle

### What payment methods do you accept?
We accept:
- Credit/debit cards: Visa, Mastercard, American Express
- PayPal
- Bank transfer (Enterprise plans only)

Payments are processed securely by Stripe.

### Do you issue invoices?
Yes. Invoices are generated automatically each month and sent to your email.
You can also download them from Settings > Billing > Payment History.
For invoices with company tax details, update your information in Settings > Billing > Tax Information.

---

## Platform Usage

### How do I integrate the API into my application?
Our REST API is easy to integrate:

1. Get your API key in Settings > Developers > API Keys
2. Check our documentation at docs.tuempresa.com
3. Install our SDK:
   - Python: `pip install tuempresa-sdk`
   - Node.js: `npm install @tuempresa/sdk`
   - PHP: `composer require tuempresa/sdk`

Basic Python example:
```python
from tuempresa import Client
client = Client(api_key="tu_api_key")
response = client.query("¿Hola?")
```

### What are the API limits?
Limits depend on your plan:
- Basic: 100 requests/minute, 1,000/day
- Professional: 500 requests/minute, 10,000/day
- Enterprise: No limits (rate limiting configured by agreement)

If you exceed the limit, you will receive an HTTP 429 error. The `Retry-After` header indicates when you can make requests again.

### Do you have scheduled downtime?
We perform scheduled maintenance on Sundays between 2:00 AM and 4:00 AM UTC.
We provide 48 hours notice by email and on our status page: status.tuempresa.com.

---

## Privacy and Security

### How do you protect my data?
- All data is encrypted in transit (TLS 1.3) and at rest (AES-256)
- We comply with GDPR and CCPA
- We do not sell or share your data with third parties
- We perform quarterly security audits
- Servers are located in the EU (for European customers) or the US

### Can I export my data?
Yes. You can export all your data in JSON or CSV format from Settings > Privacy > Export my data. The process may take up to 24 hours for accounts with a lot of information.

### How do I delete my account?
To permanently delete your account:
1. Go to Settings > Privacy > Delete account
2. Read and confirm the consequences (all your data is deleted in 30 days)
3. Enter your password to confirm
4. Click "Delete my account"

Note: If you have an active subscription, you must cancel it first.

---

## Technical Support

### What are your support hours?
- **Basic Plan**: Email support, response within 24-48 hours (business days)
- **Professional Plan**: Email and chat support, response within 4 hours (business days)
- **Enterprise Plan**: 24/7 support by email, chat, and phone

### How do I contact support?
- Email: soporte@tuempresa.com
- Live chat: Available in the platform (chat icon in the bottom-right corner)
- Phone (Enterprise only): +1 (800) 123-4567

Before contacting us, check our knowledge base at help.tuempresa.com, where you will find tutorials and detailed guides.