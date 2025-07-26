# CentralArr

**CentralArr** est une application web auto-hébergée permettant de centraliser et proxy différentes applications multimédia (Jellyfin, Navidrome, etc) accessible depuis tout appareil : PC, TV, tablette, smartphone, avec interface web et application Android.
Le projet est conçu pour être facile à développer et simple à déployer via `.deb` ou Docker.

---

## Sommaire

- [Développement](#développement)
  - [Dev Container (VS Code)](#dev-container-vs-code)
  - [Développement natif (Makefile)](#développement-natif-makefile)
- [Production](#production)
  - [Déploiement natif (.deb)](#déploiement-natif-deb)
  - [Déploiement Docker (et Docker Compose)](#déploiement-docker-et-docker-compose)
- [Arborescence du projet](#arborescence-du-projet)

---

## Développement

### Dev Container (VS Code)

1. **Prérequis :**

   - Docker installé et opérationnel sur votre machine
   - VS Code + extension [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. **Lancer le dev container**

   - Ouvrez le projet dans VS Code.
   - Cliquez sur “Reopen in Container”/« Rouvrir dans le conteneur » (ou utilisez la palette de commande).
3. **Le conteneur va :**

   - Créer l’environnement Python + Node
   - Installer toutes les dépendances grâce au `Makefile`
   - Vous fournir un shell prêt à lancer :
     ```sh
     make dev
     ```

     pour démarrer le serveur Flask (backend) **et** le frontend Vue.js en hot reload.

---

### Développement natif (Makefile)

1. **Prérequis**

   - Python 3.8+ et `python3-venv`
   - Node.js 18+ et npm
2. **Installer les dépendances**

   ```sh
   make dev-install
   ```

   (crée le venv Python, installe requirements, installe les dépendances Node)
3. **Lancer le mode développement**

   ```sh
   make dev
   ```

   Cela démarre le backend Flask en `localhost:5000`
   et le frontend Vue.js en hot reload (`localhost:5173`)
4. **Nettoyer l'environnement**

   ```sh
   make clean
   ```

---

## Production

### Déploiement natif (.deb)

1. **Récupérer le .deb depuis les releases GitHub**

   - Rendez-vous sur la page [Releases du projet](https://github.com/pikatsuto/centralarr/releases)
   - Téléchargez la dernière version stable (`centralarr_<version>.deb`)
2. **Installer le paquet**

   ```sh
   sudo dpkg -i centralarr_<version>.deb
   sudo apt --fix-broken install     # au cas où des dépendances systèmes sont requises
   ```
3. **Le service sera automatiquement démarré** (via systemd)

   - L’application sera accessible sur le port 5000
4. **Contrôler le service**

   ```sh
   sudo systemctl status centralarr
   sudo systemctl restart centralarr
   ```

---

### Déploiement Docker (et Docker Compose)

#### Prérequis

- Docker récent installé

#### Exemple de `docker-compose.yml` minimal (adapté à ce projet)

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

1. **Copiez ce fichier dans le dossier de votre choix.**
2. **Lancez le conteneur**
   ```sh
   docker compose up -d
   ```
3. **L’app sera accessible sur `http://localhost:5000` (port ajustable dans compose).

---

## Arborescence du projet

```
centralarr/
├── .devcontainer/           # Config VS Code dev container
│   └── Dockerfile.dev       # Dockerfile pour développement
├── backend/
│   ├── __init__.py          # pour l'initialisation de l'app Flask
│   ├── main.py              # point d’entrée du serveur Flask
│   ├── crud.py              # configuration générale
│   ├── proxy.py             # gestion du proxy inverse
│   ├── models.py            # BDD, ORM, gestion des données
│   └── auth.py              # gestion de l’authentification (local & SSO)
├── frontend/
│   ├── package.json         # config npm / Vue.js
│   ├── src/                 # source code Vue.js
│   └── build/ (ou dist/)    # build final (produits finaux) à copier dans Flask static
├── makedeb/                 # Génération du .deb
├── android/                 # Appli Android (webview)
├── Dockerfile               # Dockerfile de production
├── docker-compose.yml   
├── Makefile                 # Commandes build/dev/clean
└── ...
```

---

## Pour aller plus loin

- [Documentation développeurs](docs/)
- [Contribuer](CONTRIBUTING.md)
- [FAQ](docs/FAQ.md)

---

**En cas de besoin, consultez les issues du repo ou ouvrez une discussion.
Bon déploiement avec CentralArr !**
