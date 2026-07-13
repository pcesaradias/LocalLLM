# Deploy LocalLLM on Google Cloud (no local GPU)

Runs the whole stack on external resources:
- **Services** (11 FastAPI + Redis + Chroma, CPU-only) → one small Compute Engine VM.
- **Inference** → Gemini or Groq (OpenAI-compatible, no GPU). See `.env.example`.
- **Training** → free Colab GPU with `cloud_training/AutoImprove_LoRA_Colab.ipynb`.

> **Billing note:** creating a GCE VM (even the free-tier `e2-micro`) requires a
> billing account attached to the project. Set that up once in the console —
> new accounts get **$300 free credits**. That step needs your payment method
> and cannot be automated for you.

## 1. One-time setup (Cloud Shell — the terminal button in the GCP console)

```bash
gcloud config set project <YOUR_PROJECT_ID>          # e.g. the "localllm" project
gcloud services enable compute.googleapis.com

# Create the VM (e2-small = 2GB RAM is enough; e2-medium if you also run Ollama)
gcloud compute instances create localllm \
  --machine-type=e2-small --zone=europe-west1-b \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-size=30GB --tags=localllm

# Open only the user-facing ports (UI, main API, orchestrator)
gcloud compute firewall-rules create localllm-web \
  --allow=tcp:3001,tcp:8080,tcp:8004 --target-tags=localllm --direction=INGRESS
```

## 2. On the VM

```bash
gcloud compute ssh localllm --zone=europe-west1-b     # from Cloud Shell

# install docker + compose plugin
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker

# get the code and configure
git clone https://github.com/Paulocadias/LocalLLM.git && cd LocalLLM
cp .env.example .env
# edit .env: set REDIS_PASSWORD, LOCALLLM_API_KEY, INTERNAL_API_KEY (openssl rand -base64 32),
# and the inference backend (Gemini/Groq) — see .env.example.
nano .env

docker compose --env-file .env -f docker-compose-simplified.yml up -d --build
```

## 3. Access

- UI: `http://<VM_EXTERNAL_IP>:3001` (log in with `LOCALLLM_API_KEY`)
- API: `http://<VM_EXTERNAL_IP>:8080`  ·  Orchestrator: `:8004`

Get the IP: `gcloud compute instances describe localllm --zone=europe-west1-b --format='get(networkInterfaces[0].accessConfigs[0].natIP)'`

**Recommended:** put an HTTPS reverse proxy (Caddy/Nginx) in front and restrict
the firewall to your IP — the ports above are otherwise open to the internet.

## 4. Alternatives

- **No billing / free:** deploy the same compose to **Railway** or **Fly.io** free
  tiers; Redis via **Upstash** (free), vector DB via **Qdrant Cloud** (free). Point
  inference at Gemini/Groq. No GPU anywhere.
- **Self-hosted model on a rented GPU:** run vLLM/Ollama on **Modal / RunPod**, set
  `OPENAI_BASE_URL` (or `OLLAMA_BASE_URL`) to it. Only needed if you want to serve
  *your own* fine-tuned model instead of a hosted API.

## 5. The improvement loop end-to-end

1. Run the stack; call `POST /improve/test-model` (or let the orchestrator do it) —
   `automatic_tester` compares your model vs the reference and writes
   `datasets/lora_profiles/auto_*.jsonl`.
2. Open `cloud_training/AutoImprove_LoRA_Colab.ipynb` in Colab (free T4), upload that
   JSONL, Run all → get a LoRA adapter + GGUF.
3. Import the GGUF to Ollama (`ollama create ...`) and point LocalLLM at it, or keep
   using the hosted API. Repeat.
