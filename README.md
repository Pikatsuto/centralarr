[🇫🇷 Lire la documentation en français (README_FR.md)](README_FR.md)

# CentralArr

**CentralArr** is a self-hosted web application designed to centralize and securely proxy various media services (Jellyfin, Navidrome, etc.), accessible from any device: PC, TV, tablet, smartphone, via a responsive web interface and an Android app.
The project is built to be easy for developers and simple to deploy, either as a `.deb` package or as a Docker container.

---

## Table of Contents

- [Development](#development)
  - [Dev Container (VS Code)](#dev-container-vs-code)
  - [Native Development (Makefile)](#native-development-makefile)
- [Production](#production)
  - [Native Deployment (.deb)](#native-deployment-deb)
  - [Docker Deployment (with Docker Compose)](#docker-deployment-with-docker-compose)
- [Project Structure](#project-structure)

---

## Development

### Dev Container (VS Code)

1. **Prerequisites:**

   - Docker installed and running
   - VS Code + [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. **Start with the dev container:**

   - Open the project in VS Code.
   - Click “Reopen in Container” when prompted, or use the Command Palette.
3. **The container will:**

   - Set up Python and Node environments
   - Install all dependencies using the `Makefile`
   - Provide a ready-to-use shell. To start development servers, run:

     ```sh
     make dev
     ```

     This starts both the Flask backend (with hot-reload) and the Vue.js frontend in development mode (hot-reload).

---

### Native Development (Makefile)

1. **Prerequisites**

   - Python 3.8+ with `python3-venv`
   - Node.js 18+ and npm
2. **Install dependencies**

   ```sh
   make dev-install
   ```

   (Sets up Python virtualenv, installs Python and Node dependencies.)
3. **Start development servers**

   ```sh
   make dev
   ```

   This will launch the Flask backend on `localhost:5000`
   and the Vue.js frontend in hot-reload mode (`localhost:5173`).
4. **Clean your environment**

   ```sh
   make clean
   ```

---

## Production

### Native Deployment (.deb)

1. **Get the latest .deb release from GitHub**

   - Go to the [project Releases page](https://github.com/pikatsuto/centralarr/releases)
   - Download the latest stable version (`centralarr_<version>.deb`)
2. **Install the package**

   ```sh
   sudo dpkg -i centralarr_<version>.deb
   sudo apt --fix-broken install     # in case of missing dependencies
   ```
3. **The service will start automatically** (via systemd)

   - The app will be available on port 5000
4. **Manage the service**

   ```sh
   sudo systemctl status centralarr
   sudo systemctl restart centralarr
   ```

---

### Docker Deployment (with Docker Compose)

#### Prerequisites

- Recent Docker installed

#### Example minimal `docker-compose.yml` (copy-paste ready)

```yaml
version: '3.8'
services:
  centralarr:
    image: ghcr.io/pikatsuto/centralarr/centralarr:latest
    container_name: centralarr
    ports:
      - "5000:5000"
    volumes:
      - ./data:/opt/centralarr/db
    environment:
      FASTAPI_ENV: prod
      PORT: 5000
    restart: unless-stopped
```

1. **Copy this file next to your project or wherever you want to deploy.**
2. **Start the container**
   ```sh
   docker compose up -d
   ```
3. **The app will be available at `http://localhost:5000` (adjust the port if needed).**

---

## Project Structure

```
centralarr/
├── .devcontainer/           # VS Code dev container configuration
│   └── Dockerfile.dev       # Dockerfile for development environment
├── backend/
│   ├── __init__.py          # Flask app initialization
│   ├── main.py              # Flask server entry point
│   ├── crud.py              # Global configuration
│   ├── proxy.py             # Reverse proxy logic
│   ├── models.py            # Database, ORM, data management
│   └── auth.py              # Authentication (local & SSO)
├── frontend/
│   ├── package.json         # NPM / Vue.js configuration
│   ├── src/                 # Vue.js source code
│   └── build/ (or dist/)    # Final frontend build to be served by Flask static
├── makedeb/                 # .deb package generation scripts
├── android/                 # Android app (WebView)
├── Dockerfile               # Production Dockerfile
├── docker-compose.yml   
├── Makefile                 # Build/dev/clean commands
└── ...
```

---

## Further reading

- [Developer documentation](docs/)
- [Contributing](CONTRIBUTING.md)
- [FAQ](docs/FAQ.md)

---

**For any questions, check the issues section or open a new discussion.
Happy deploying with CentralArr!**

---

Let me know if you want advanced deployment guides, security/admin hints, or user-oriented documentation!
