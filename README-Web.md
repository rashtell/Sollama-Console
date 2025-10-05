# Sollama Web Interface

Web-based interface for Sollama with full feature support including streaming responses, TTS, and conversation memory.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch with defaults
python gradio_interface.py

# Launch with custom settings
python gradio_interface.py --share --model llama3.2:1b --speak-streaming
```

## Command Line Arguments

### Server Settings

| Argument         | Short | Default     | Description                          |
| ---------------- | ----- | ----------- | ------------------------------------ |
| `--host`         | `-H`  | `127.0.0.1` | Host to bind server to               |
| `--port`         | `-p`  | `None`      | Port (auto-select if not specified)  |
| `--share`        | -     | `False`     | Create public shareable link         |
| `--auth`         | -     | `None`      | Authentication (format: `user:pass`) |
| `--server-name`  | -     | `None`      | Custom server name                   |
| `--root-path`    | -     | `None`      | Root path for reverse proxy          |
| `--ssl-certfile` | -     | `None`      | SSL certificate file path            |
| `--ssl-keyfile`  | -     | `None`      | SSL key file path                    |

### Model Settings

| Argument       | Short | Default                  | Description       |
| -------------- | ----- | ------------------------ | ----------------- |
| `--model`      | `-m`  | `llama3.2`               | Ollama model name |
| `--ollama-url` | `-u`  | `http://localhost:11434` | Ollama server URL |

### TTS Settings

| Argument            | Short | Default | Description            |
| ------------------- | ----- | ------- | ---------------------- |
| `--speech-rate`     | `-r`  | `175`   | Speech rate (50-300)   |
| `--volume`          | `-v`  | `1.0`   | Volume level (0.0-1.0) |
| `--voice`           | -     | `0`     | Voice index            |
| `--mute`            | -     | `False` | Start with TTS muted   |
| `--speak-streaming` | -     | `False` | Auto-speak responses   |

### Memory Settings

| Argument          | Short | Default | Description                |
| ----------------- | ----- | ------- | -------------------------- |
| `--max-memory`    | `-mm` | `50`    | Max conversation exchanges |
| `--system-prompt` | `-sp` | `None`  | Custom system prompt       |
| `--load-memory`   | `-lm` | `None`  | Load memory from file      |

## Usage Examples

### Local Development

```bash
# Default local server
python gradio_interface.py

# Custom port
python gradio_interface.py --port 8080
```

### Public Sharing

```bash
# Create temporary public link
python gradio_interface.py --share

# Public server on all interfaces
python gradio_interface.py --host 0.0.0.0 --port 7860 --share
```

### Secure Deployment

```bash
# With authentication
python gradio_interface.py --auth admin:secretpassword

# With SSL/TLS
python gradio_interface.py --ssl-certfile cert.pem --ssl-keyfile key.pem --port 443

# Combined security
python gradio_interface.py --auth admin:pass --ssl-certfile cert.pem --ssl-keyfile key.pem
```

### Custom Model Configuration

```bash
# Smaller, faster model
python gradio_interface.py --model llama3.2:1b

# Coding-focused model
python gradio_interface.py --model codellama --system-prompt "You are a Python expert"

# Remote Ollama server
python gradio_interface.py --model mistral --ollama-url http://192.168.1.100:11434
```

### TTS Configuration

```bash
# Fast speech with specific voice
python gradio_interface.py --speech-rate 250 --voice 2

# Quiet mode
python gradio_interface.py --volume 0.3

# Auto-speak responses
python gradio_interface.py --speak-streaming

# Start muted
python gradio_interface.py --mute
```

### Memory Management

```bash
# Extended memory
python gradio_interface.py --max-memory 100

# Load previous conversation
python gradio_interface.py --load-memory session_20240101.json

# Custom personality
python gradio_interface.py --system-prompt "You are a creative writing coach specializing in science fiction"
```

### Combined Configurations

```bash
# Production-ready setup
python gradio_interface.py \
  --host 0.0.0.0 \
  --port 443 \
  --auth admin:secure_password \
  --ssl-certfile /etc/ssl/cert.pem \
  --ssl-keyfile /etc/ssl/key.pem \
  --model llama3.2 \
  --max-memory 100

# Optimized for speed
python gradio_interface.py \
  --model llama3.2:1b \
  --speech-rate 200 \
  --speak-streaming

# Public demo server
python gradio_interface.py \
  --share \
  --model llama3.2 \
  --system-prompt "You are a helpful AI assistant" \
  --speak-streaming
```

## Deployment Options

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "gradio_interface.py", "--host", "0.0.0.0", "--port", "7860"]
```

Run:

```bash
docker build -t sollama-gradio .
docker run -p 7860:7860 sollama-gradio
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name sollama.example.com;

    location /sollama/ {
        proxy_pass http://127.0.0.1:7860/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Launch with:

```bash
python gradio_interface.py --root-path /sollama
```

### Systemd Service

Create `/etc/systemd/system/sollama-gradio.service`:

```ini
[Unit]
Description=Sollama Gradio Interface
After=network.target

[Service]
Type=simple
User=sollama
WorkingDirectory=/opt/sollama
ExecStart=/usr/bin/python3 gradio_interface.py --host 0.0.0.0 --port 7860
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable sollama-gradio
sudo systemctl start sollama-gradio
```

## SSL Certificate Generation

### Self-Signed (Testing Only)

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### Let's Encrypt (Production)

```bash
certbot certonly --standalone -d sollama.example.com
python gradio_interface.py \
  --ssl-certfile /etc/letsencrypt/live/sollama.example.com/fullchain.pem \
  --ssl-keyfile /etc/letsencrypt/live/sollama.example.com/privkey.pem
```

## Environment Variables

You can also use environment variables instead of command-line arguments:

```bash
export SOLLAMA_HOST=0.0.0.0
export SOLLAMA_PORT=7860
export SOLLAMA_MODEL=llama3.2
export SOLLAMA_SPEECH_RATE=175
export SOLLAMA_VOLUME=1.0

python gradio_interface.py
```

## Troubleshooting

### Port Already in Use

```bash
# Let Gradio auto-select port
python gradio_interface.py

# Or specify different port
python gradio_interface.py --port 8080
```

### TTS Not Working

- Ensure pyttsx3 is installed: `pip install pyttsx3`
- On Windows, ensure pywin32 is installed: `pip install pywin32`
- Check audio output devices are working

### Connection Refused

- Verify Ollama is running: `ollama serve`
- Check Ollama URL is correct
- Test connection: `curl http://localhost:11434/api/tags`

### Slow Responses

- Use smaller model: `--model llama3.2:1b`
- Disable streaming temporarily
- Check Ollama server resources

## Performance Tips

1. **Use smaller models** for faster responses
2. **Disable TTS** if not needed (`--mute`)
3. **Reduce max memory** for lower RAM usage
4. **Use local Ollama server** to avoid network latency
5. **Enable streaming** for perceived faster responses

## Security Considerations

1. **Always use authentication** for public deployments
2. **Use SSL/TLS** for encrypted connections
3. **Set firewall rules** to restrict access
4. **Keep dependencies updated**: `pip install --upgrade -r requirements.txt`
5. **Monitor logs** for suspicious activity
6. **Use strong passwords** for authentication

## License
