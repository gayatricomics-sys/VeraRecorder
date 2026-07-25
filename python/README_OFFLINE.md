# Offline Installation Guide

This directory contains all the Python dependencies downloaded as wheel (`.whl`) files in the `wheels/` directory.

To install these dependencies on a machine without internet access, run the following command:

```bash
# Ensure your virtual environment is activated
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install from the downloaded wheels without hitting the internet
pip install --no-index --find-links=wheels/ -r requirements.txt
```
