# Overview
Demonstrates how to use transcription.

## Setup

### Install dependencies
```commandline
pdm install -p .
```

### Setup .env
Take a look at the `.env.example`. We need to create a file called `.env` with the same variables as the `.env.example`.
Create your `VULAVULA_API_KEY` and add it to the `.env` file, optional you can add the `BASE_URL` which is already added in code.

### Fast Transcribe
Fast transcribe accepts a file upload and returns transcribed results.

To run fast transcribe, there is an added script in `pyproject.toml` that helps you run the file `__main__.py` which is the entry point. Run the command in your terminal root folder of the 3-transcription project
```commandline
pdm run fast
```

You can also execute the file using the command:
```commandline
pdm run python src/fast_transcription/__main__.py
```

or simply

```commandline
python src/fast_transcription/__main__.py
```