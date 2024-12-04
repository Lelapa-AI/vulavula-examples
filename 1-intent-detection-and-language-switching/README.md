# Intent Detection And Language Switching

In this project we show you how to use the intent detection feature on the Vulavula API.

## Setup

### Install dependencies
```commandline
pdm install -p .
```

### Setup .env
Take a look at the `example.env`. We need to create a file called `.env` with the same variables as the `example.env`.
Create your `VULAVULA_API_KEY` and add it to the `.env` file.

### Run main.py file
The `main.py` file acts as the entrypoint for this demo application.
```commandline
pdm run python src/intent_detection_and_language_switching/main.py
```