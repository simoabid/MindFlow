# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of MindFlow seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to [INSERT EMAIL ADDRESS].

You should receive a response within 48 hours. If for some reason you do not, please follow up to ensure we received your original message.

### What to Include

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### What to Expect

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will provide an estimated timeline for a fix
- We will notify you when the vulnerability is fixed
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Considerations

### API Key Storage

MindFlow stores the Gemini API key in plaintext in `~/.config/mindflow/config.json`. This file should have restricted permissions:

```bash
chmod 600 ~/.config/mindflow/config.json
```

### Input Method Security

MindFlow runs as an IBus input method engine. This means:

- It can observe keystrokes when active (this is by design for autocomplete)
- It sends text context to the Gemini API for predictions
- It runs with user permissions (no root required)
- It does not log or store typed text permanently

### Network Communication

MindFlow communicates with:

- **Google Gemini API** — For text predictions (HTTPS)
- **IBus D-Bus** — For input method functionality (local only)

### Recommendations

1. **Keep your API key secure** — Don't commit it to version control
2. **Use environment variables** — Set `GEMINI_API_KEY` instead of config file
3. **Review predictions** — Be aware that text is sent to Google's servers
4. **Keep updated** — Use the latest version for security fixes

## Security Best Practices for Contributors

- Never commit API keys, passwords, or secrets
- Use environment variables for sensitive configuration
- Validate all user input
- Use parameterized queries (if applicable)
- Follow the principle of least privilege
- Keep dependencies updated

## Acknowledgments

We appreciate the security research community and will acknowledge researchers who responsibly disclose vulnerabilities.

## Contact

For security concerns, please contact [INSERT EMAIL ADDRESS].

For general questions, please open an issue on GitHub.
