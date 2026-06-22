---
name: Bug Report
about: Report a bug to help us improve MindFlow
title: "[BUG] "
labels: bug
assignees: ''
---

## Describe the Bug

A clear and concise description of what the bug is.

## Steps to Reproduce

1. Go to '...'
2. Type '...'
3. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

A clear and concise description of what actually happened.

## Screenshots

If applicable, add screenshots to help explain your problem.

## Environment

- **OS:** [e.g., Ubuntu 24.04, Zorin OS 18.1]
- **Desktop Environment:** [e.g., GNOME 46, KDE Plasma 6]
- **Session Type:** [X11 / Wayland]
- **IBus Version:** [run `ibus version`]
- **Python Version:** [run `python3 --version`]
- **MindFlow Version:** [e.g., 0.1.0 or commit hash]

## Logs

If applicable, add logs to help explain your problem.

```bash
# Enable debug logging and reproduce the issue
export MINDFLOW_LOG_LEVEL=DEBUG
ibus engine mindflow 2>&1 | tee /tmp/mindflow.log

# Paste the relevant log output here
```

## Additional Context

Add any other context about the problem here.

## Checklist

- [ ] I have searched existing issues to avoid duplicates
- [ ] I have included my environment information
- [ ] I have included steps to reproduce
- [ ] I have included logs (if applicable)
