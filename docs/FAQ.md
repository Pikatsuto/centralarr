# CentralArr – FAQ

### What is CentralArr?

CentralArr is a self-hosted web app for centralizing and proxying other applications, like Jellyfin or Navidrome, with a responsive interface and native/Android support.

---

### Development

**Q: How can I start developing or testing locally?**  
A: Check the [README.md](../README.md) for a full guide. You can use VS Code Dev Containers, Docker, or make/native setup.

**Q: What languages and tech does the project use?**  
A:  
- Backend: Python (Flask, SQLAlchemy)
- Frontend: Vue.js with Vuetify
- Packaging: make/deb/Docker
- (Optional) Android (WebView app)

---

### Packaging & Deployment

**Q: How can I get the latest .deb package?**  
A: Download it from the [GitHub Releases page](https://github.com/pikatsuto/centralarr/releases).

**Q: How do I persist the database?**  
A:  
- With Docker: Mount a host folder (see docker-compose.yml).  
- Native: SQLite database is local in `/opt/centralarr/db`.

**Q: Can I deploy with Docker Compose?**  
A: Yes, see the example in the [README.md](../README.md).

---

### Authentication & Security

**Q: Does CentralArr support SSO or OpenID Connect?**  
A: Yes, see the `auth.py` and documentation for current authentication/SSO integration status.

**Q: Can users and groups be managed?**  
A: Yes. User, group, and permission management is provided within the app.

---

### Troubleshooting

**Q: The app won’t start (service or container)**  
A:  
- Check logs (`systemctl status centralarr` or `docker logs centralarr`)
- Ensure dependencies are installed
- Try `make clean` and `make dev-install` for a fresh dev environment

**Q: Something isn’t working, or I found a bug!**  
A: Please [open an issue](https://github.com/pikatsuto/centralarr/issues) and provide as much detail as possible.

---

### More Questions?

- See the [README](../README.md)
- Join project discussions
- Open an issue

---

Thank you for using and contributing to CentralArr!