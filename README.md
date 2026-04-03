# Gewinn-

## Setup

To set up the Termux environment, run the following command:

```bash
bash setup.sh
```

This script will update packages, install necessary tools, create a project directory `nexus-core/`, set up a Python virtual environment, install required Python packages, and install Playwright browsers.

## API Keys

To add API keys, edit the file `nexus-core/config/keys.env` and add your keys in the format:

```
GEMINI_APIKEY=your_key1,your_key2,your_key3
GROQ_APIKEY=your_key1,your_key2
```

Replace with your actual API keys.