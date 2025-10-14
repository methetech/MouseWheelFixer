# Contributing to Scroll Lock App

We welcome contributions to the Scroll Lock App! Here are some guidelines to help you get started.

## How to Contribute

### Reporting Bugs

*   **Check existing issues**: Before opening a new issue, please check if a similar bug has already been reported.
*   **Provide detailed information**: When reporting a bug, include:
    *   A clear and concise description of the bug.
    *   Steps to reproduce the behavior.
    *   Expected behavior.
    *   Screenshots or videos if applicable.
    *   Your operating system and Python version.

### Suggesting Enhancements

*   **Check existing suggestions**: See if your idea has already been proposed.
*   **Describe your idea**: Clearly explain the enhancement and why it would be beneficial.

### Code Contributions

1.  **Fork the repository**.
2.  **Create a new branch** for your feature or bug fix.
    ```bash
    git checkout -b feature/your-feature-name
    ```
    or
    ```bash
    git checkout -b bugfix/your-bug-fix-name
    ```
3.  **Make your changes**.
4.  **Write clear, concise commit messages**.
5.  **Test your changes** thoroughly.
6.  **Submit a Pull Request (PR)**:
    *   Ensure your branch is up-to-date with the `main` branch.
    *   Provide a clear description of your changes.
    *   Reference any related issues.

## Code Style

*   Follow PEP 8 for Python code.
*   Use clear and descriptive variable and function names.
*   Add comments where necessary to explain complex logic.

## Development Setup

To set up your development environment, follow the installation steps in `README.md`.

When running the application for development, it is recommended to use the `--no-watchdog` flag. This will prevent the watchdog from restarting the application if it crashes or is closed.

```bash
python wheel.py --no-watchdog
```

Thank you for contributing!
