# Security Guidelines for TuneMeld

## Environment Variables & Credentials

### Local Development Setup

1. **Never commit credentials to version control**
2. **Use `.env.local` for local development**:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your actual credentials
   ```
3. **Keep `.env.local` in `.gitignore`** (already configured)

### Production Deployment

1. **Railway Environment Variables**:
   - Set all environment variables in Railway dashboard
   - Never use `.env.prod` in production
   - Use Railway's environment variable management

2. **Cloudflare Workers**:
   - Set environment variables in Cloudflare Worker dashboard
   - Remove hardcoded credentials from `wrangler.toml`

### Security Best Practices

1. **Credential Rotation**:
   - Rotate API keys regularly
   - Use different credentials for dev/staging/production
   - Monitor for exposed credentials

2. **Required Environment Variables**:
   - `SECRET_KEY`: Django secret key (required, no fallback)
   - `MONGO_URI`: MongoDB connection string
   - `MONGO_DATA_API_KEY`: MongoDB Data API key
   - All API keys (Spotify, Google, RapidAPI, etc.)

3. **GitHub Actions Secrets**:
   - Use GitHub repository secrets for CI/CD
   - Never log sensitive environment variables

## Incident Response

If credentials are exposed:
1. **Immediately rotate** all affected credentials
2. **Review access logs** for unauthorized usage
3. **Update environment variables** in all environments
4. **Monitor for security alerts**

## File Security

- ✅ `.env.local` - Local development (gitignored)
- ✅ `.env.test` - Test environment (fake credentials only)
- ❌ `.env.dev` - Should be replaced with `.env.local`
- ❌ `.env.prod` - Should use Railway environment variables

## Contact

Report security vulnerabilities to: [security contact information]