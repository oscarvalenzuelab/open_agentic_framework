# DigitalOcean Deployment Troubleshooting

## Environment Variables Not Working

### Issue: API Keys not being recognized

**Solution for App Platform:**

1. **In DigitalOcean Dashboard:**
   - Go to your app → Settings → App-Level Environment Variables
   - Make sure you have these EXACT keys set:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   OPENAI_ENABLED=true
   DEFAULT_LLM_PROVIDER=openai
   OPENAI_DEFAULT_MODEL=gpt-3.5-turbo
   OLLAMA_ENABLED=false
   ```

2. **Important:** App Platform does NOT run Ollama, so you must:
   - Set `OLLAMA_ENABLED=false`
   - Set `DEFAULT_LLM_PROVIDER=openai` (not ollama)
   - Use OpenAI as your primary provider

3. **After updating environment variables:**
   - Click "Save"
   - The app will automatically redeploy
   - Wait 5-10 minutes for the deployment to complete

### Verification Steps

1. **Check Provider Status:**
   ```bash
   curl https://your-app.ondigitalocean.app/providers
   ```

   Should show:
   ```json
   {
     "openai": {
       "enabled": true,
       "status": "connected"
     },
     "ollama": {
       "enabled": false
     }
   }
   ```

2. **Check Available Models:**
   ```bash
   curl https://your-app.ondigitalocean.app/models
   ```

   Should list OpenAI models like:
   - gpt-3.5-turbo
   - gpt-4
   - gpt-4-turbo

3. **Test the API Key:**
   ```bash
   curl -X POST https://your-app.ondigitalocean.app/models/test/gpt-3.5-turbo
   ```

### Common Issues and Fixes

#### Issue: "No LLM provider available"
**Fix:**
- Ensure `OPENAI_ENABLED=true`
- Ensure `OPENAI_API_KEY` starts with `sk-`
- Set `DEFAULT_LLM_PROVIDER=openai`

#### Issue: "Invalid API key"
**Fix:**
- Double-check your OpenAI API key
- Make sure there are no extra spaces
- Verify the key at https://platform.openai.com/api-keys

#### Issue: "Model not found"
**Fix:**
- Use `gpt-3.5-turbo` or `gpt-4` (not granite or ollama models)
- Set `DEFAULT_MODEL=gpt-3.5-turbo`
- Set `OPENAI_DEFAULT_MODEL=gpt-3.5-turbo`

### Environment Variables Reference

| Variable | Required | Value | Description |
|----------|----------|--------|-------------|
| `OPENAI_API_KEY` | Yes | `sk-...` | Your OpenAI API key |
| `OPENAI_ENABLED` | Yes | `true` | Enable OpenAI provider |
| `DEFAULT_LLM_PROVIDER` | Yes | `openai` | Set OpenAI as default |
| `OPENAI_DEFAULT_MODEL` | Yes | `gpt-3.5-turbo` | Default model to use |
| `OLLAMA_ENABLED` | Yes | `false` | Disable Ollama (not available in App Platform) |
| `LLM_FALLBACK_ENABLED` | No | `false` | Disable fallback to avoid errors |

### App Platform Limitations

App Platform does NOT support:
1. **Multiple containers** - Can't run Ollama alongside your app
2. **Local LLMs** - Ollama models won't work
3. **Docker Compose** - Single container only

**Solution:** Use OpenAI, OpenRouter, or AWS Bedrock as your LLM provider.

### Alternative: Use a Droplet

If you need Ollama support, deploy on a Droplet instead:

1. Create a Droplet with Docker
2. SSH into the droplet
3. Use docker-compose to run both services
4. This allows local Ollama models to work

### Getting Help

1. **Check Logs:**
   - DigitalOcean Dashboard → Your App → Runtime Logs
   - Look for "OPENAI_ENABLED" and "DEFAULT_LLM_PROVIDER" values

2. **Health Check:**
   ```bash
   curl https://your-app.ondigitalocean.app/health
   ```

3. **Support:**
   - DigitalOcean Support: https://www.digitalocean.com/support/
   - GitHub Issues: https://github.com/oscarvalenzuelab/open_agentic_framework/issues