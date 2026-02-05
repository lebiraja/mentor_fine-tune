# Backend SSL Certificate Error - SOLUTION

## Problem
Backend is crashing with SSL error when downloading models from HuggingFace:
```
certificate verify failed: Hostname mismatch, certificate is not valid for 'huggingface.co'
```

## Quick Solutions

### Option 1: Disable SSL Verification (Quick Fix)
Add to docker-compose.yml backend environment:

```yaml
environment:
  - CURL_CA_BUNDLE=""
  - REQUESTS_CA_BUNDLE=""
  - SSL_CERT_FILE=""
  - HF_HUB_DISABLE_IMPLICIT_TOKEN=1
  - HF_HUB_OFFLINE=0
```

### Option 2: Pre-download Models on Host (Recommended)
Download models before starting Docker:

```bash
# Install transformers on host
pip install transformers

# Download models
python3 << 'PYTHON'
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
processor = AutoProcessor.from_pretrained("distil-whisper/distil-medium.en")
model = AutoModelForSpeechSeq2Seq.from_pretrained("distil-whisper/distil-medium.en")
print("Models downloaded to ~/.cache/huggingface/")
PYTHON

# Mount cache in docker-compose.yml
volumes:
  - ~/.cache/huggingface:/root/.cache/huggingface:ro
```

### Option 3: Use Different Network
The SSL error might be due to network proxy/firewall. Try:

```bash
# Check if you can reach huggingface.co
curl -v https://huggingface.co

# If behind corporate proxy, add to docker-compose.yml:
environment:
  - HTTP_PROXY=http://your-proxy:port
  - HTTPS_PROXY=http://your-proxy:port
  - NO_PROXY=localhost,127.0.0.1
```

## Apply Fix Now

Run this to update docker-compose.yml:
```bash
# Stop containers
docker-compose down

# I'll update the file...
```
