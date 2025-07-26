# Contributing to CentralArr

Thank you for considering contributing to CentralArr!  
We welcome all kinds of contributions: bug reports, suggestions, code, documentation, and more.

---

## Getting Started

### 1. Fork the Repository

Click “Fork” at the top right of the GitHub repository and clone your copy:

```sh
git clone https://github.com/YOUR_USERNAME/centralarr.git
cd centralarr
```

### 2. Install Dev Environment

See the [README](README.md) for detailed instructions to set up the development environment (Dev Container, Makefile, Docker, or native).

---

## Contribution Guidelines

### Bug Reports & Feature Requests

- Open an [issue](https://github.com/pikatsuto/centralarr/issues) and use the appropriate template.
- Clearly describe the problem or suggestion.
- Include logs, screenshots, or reproduction steps if helpful.

### Code Contributions

#### Workflow

1. Always **create a new branch** from `main` for your work:
    ```sh
    git checkout main
    git pull
    git checkout -b feature/my-feature
    ```

2. Make your changes.  
   - Follow [PEP8](https://www.python.org/dev/peps/pep-0008/) for Python code.
   - Use clear commit messages.
   - Write or update tests if possible.

3. If you add or change dependencies, update relevant files (`requirements.txt`, `package.json`).

4. **Lint and test your code**. If a test or lint fails, fix it before submitting:
    ```sh
    make clean
    make dev-install
    make test         # (if tests are available)
    ```

5. **Push your branch**
    ```sh
    git push origin feature/my-feature
    ```

6. Make a **Pull Request** to the main repo.  
   Provide a clear description and link to any related issues.

---

### Code of Conduct

Help us keep the project inclusive and respectful.  
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for our code of conduct.

---

## Help and Questions

- Check the [FAQ](docs/FAQ.md)
- Open an [issue](https://github.com/pikatsuto/centralarr/issues)
- Join the project discussions if available

Thank you for making CentralArr better!