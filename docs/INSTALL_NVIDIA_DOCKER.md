# 🎮 GPU Support Required - Install NVIDIA Container Toolkit

## Problem
You have GPU (`nvidia-smi` works) but Docker can't access it.

**Error:**
```
nvidia-container-cli: initialization error: load library failed: libnvidia-ml.so.1
```

## Solution: Install NVIDIA Container Toolkit

### Quick Install (Run these commands):

```bash
# 1. Add NVIDIA repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. Install toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 3. Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker

# 4. Restart Docker
sudo systemctl restart docker

# 5. Verify installation
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

### Then Start ClarityMentor

```bash
cd /home/lebi/projects/mentor
docker-compose up -d
```

---

## Alternative: Use CPU-Only Mode (No GPU Setup Needed)

If you don't want to install nvidia-container-toolkit:

```bash
# Use CPU version
docker-compose -f docker-compose.cpu.yml up -d
```

**Note:** CPU mode works but is slower (30-60s response time vs 2-5s with GPU)

---

## Verify GPU Access

After installation:
```bash
# Check Docker can see GPU
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Should show your RTX 4050
```
