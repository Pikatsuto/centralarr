#!/bin/bash

set -e

# Variables
PACKAGE_NAME="centralarr"
VERSION="1.0.0"
BUILD_DIR="./build"

# Clean up the previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create the package structure
mkdir -p "$BUILD_DIR/DEBIAN" \
         "$BUILD_DIR/opt/centralarr/static"

# Copy your entire app to the package directory
cp -r ../backend/* "$BUILD_DIR/opt/centralarr/"
cp -r ../frontend/build/* "$BUILD_DIR/opt/centralarr/static/"

# Concatenate your control file
cat > "$BUILD_DIR/DEBIAN/control" <<EOF
Package: centralarr
Version: $VERSION
Section: web
Priority: optional
Architecture: amd64
Maintainer: TonNom <ton@mail.com>
Description: Application web CentralArr (Flask + Vue.js + systemd)
Depends: python3, python3-pip curl
EOF

# Postinst script
cat > "$BUILD_DIR/DEBIAN/postinst" <<EOF
#!/bin/bash
set -e
cd /opt/centralarr/
python -m venv venv
./venv/bin/pip install -r /opt/centralarr/requirements.txt
systemctl daemon-reload
systemctl enable centralarr
systemctl start centralarr
exit 0
EOF
chmod +x "$BUILD_DIR/DEBIAN/postinst"

# Script prerm
cat > "$BUILD_DIR/DEBIAN/prerm" <<EOF
#!/bin/bash
set -e
systemctl stop centralarr
systemctl disable centralarr
systemctl daemon-reload
exit 0
EOF
chmod +x "$BUILD_DIR/DEBIAN/prerm"

# Copy the systemd service
mkdir -p "$BUILD_DIR/lib/systemd/system"
cat > "$BUILD_DIR/lib/systemd/system/centralarr.service" <<EOF
[Unit]
Description=CentralArr FastAPI app
After=network.target

[Service]
ExecStart=/opt/centralarr/venv/bin/uvicorn main:create_app --host 0.0.0.0 --port 5000 --factory
WorkingDirectory=/opt/centralarr
User=debian
Restart=always
Environment=PORT=8000

[Install]
WantedBy=multi-user.target
EOF
# Building the package
dpkg-deb --build "$BUILD_DIR" "output/${PACKAGE_NAME}_${VERSION}.deb"

echo "Fini : ${PACKAGE_NAME}_${VERSION}.deb généré dans ../"