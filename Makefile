.PHONY: all build-deb clean-deb clean dev-install dev

all: build-deb

# Variable dev
VENV=venv
BACKEND_DIR=backend
FRONTEND_DIR=frontend
NODE_MODULES=$(FRONTEND_DIR)/node_modules
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
GUNICORN=$(VENV)/bin/gunicorn

# Folder variables
DEB_BUILD_DIR=makedeb/build
DEB_OUTPUT_DIR=makedeb/output

clean-deb:
    @echo "==> Cleaning up the .deb build"
    rm -rf $(DEB_BUILD_DIR)
    rm -rf $(DEB_OUTPUT_DIR)

build-deb: clean-deb
    @echo "==> Build the .deb"
    mkdir -p $(DEB_OUTPUT_DIR) $(DEB_BUILD_DIR)
    cd makedeb && ./build_deb.sh

clean:
    rm -rf $(VENV)
    rm -rf $(BACKEND_DIR)/*.egg-info
    rm -rf $(NODE_MODULES)
    rm -rf $(FRONTEND_DIR)/dist
    rm -rf $(FRONTEND_DIR)/build
    rm -rf makedeb/build makedeb/output

dev-install: $(VENV) $(NODE_MODULES)

# Create the venv and install Flask in editable mode + deps
$(VENV):
    python3 -m venv $(VENV)
    $(PIP) install -U pip
    cd $(BACKEND_DIR) && ../../$(PIP) install -r requirements.txt
    @echo “✅ Virtualenv and Python dependencies installed”

# Install Node.js dependencies (npm install)
$(NODE_MODULES):
    cd $(FRONTEND_DIR) && npm install
    @echo “✅ Node.js dependencies installed”

dev: dev-install
    @echo “🌱 Starting development mode”
    # Launch the frontend in dev mode (e.g., npm run serve) AND the backend in dev mode.
    # Use ‘concurrently’ to launch both if necessary (npm install --global concurrently).
    # Or open two terminals:
    cd $(FRONTEND_DIR) && npm run serve &
    . $(VENV)/bin/activate && cd $(BACKEND_DIR) && uvicorn main:create_app --host 0.0.0.0 --port 5000 --reload --factory