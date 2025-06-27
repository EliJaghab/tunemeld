# Django Backend Configuration

## Security Configuration

### SECRET_KEY Requirement

The Django `SECRET_KEY` is a critical security setting that must be properly configured for each environment. This key is used for:

- Signing session cookies
- Password reset tokens
- Any other cryptographic signing
- CSRF token generation

**IMPORTANT**: The `SECRET_KEY` must be:

- Unique for each environment (development, test, production)
- Never hardcoded in the source code
- Never committed to version control
- At least 50 characters long and randomly generated

### Setting up SECRET_KEY

1. **Environment Variables**: The application requires `SECRET_KEY` to be set as an environment variable. The application will fail to start if this is not provided.

2. **Generating a new SECRET_KEY**: Use Django's built-in utility:

   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```

3. **Environment Files**: Add the SECRET_KEY to your environment file:

   - `.env.dev` - Development environment
   - `.env.test` - Test environment
   - `.env.prod` - Production environment (never commit this!)

   Example:

   ```
   SECRET_KEY=your-unique-secret-key-here
   ```

### Security Best Practices

1. **Never use the same SECRET_KEY across environments**
2. **Rotate SECRET_KEY periodically in production**
3. **Use a secure key management service in production (e.g., Railway secrets, AWS Secrets Manager)**
4. **Monitor for any exposed keys in version control history**

### Error Handling

If `SECRET_KEY` is not set, the application will raise a `ValueError` with a clear message:

```
SECRET_KEY environment variable is required but not set. Please set it in your .env file or environment variables.
```

This fail-safe approach ensures the application cannot run with an insecure configuration.
