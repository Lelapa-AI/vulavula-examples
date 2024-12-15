# Overview
This project has two packages that demonstrate how to integrate with two different features that could be used in tandem 
to satisfy higher order use cases. In particular, we will demonstrate how to use the 
**Intent Detection And Language Switching** feature and the **Knowledge base Search feature**


## Setup

### Install dependencies
```commandline
pdm install -p .
```

### Setup .env
Take a look at the `example.env`. We need to create a file called `.env` with the same variables as the `example.env`.
Create your `VULAVULA_API_KEY` and add it to the `.env` file.

### Intent Detection and Language Switching

#### Run main.py file
The `main.py` file acts as the entrypoint for this demo application.
```commandline
pdm run python src/intent_detection_and_language_switching/main.py
```

### Knowledge base search

#### Run main.py file
The `main.py` file acts as the entrypoint for this demo application. 
```commandline
pdm run python src/knowledge_base_search/main.py
```