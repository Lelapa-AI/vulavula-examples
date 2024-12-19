# Vulavula Examples

Full API documentation is available at the [Vulavula documentation](https://docs.lelapa.ai/) page. This repository contains a collection of 
example applications that demonstrate how to consume a specific our APIs in various scenarios. Each example is organized
into its own directory, focusing on a particular use case or integration pattern.

## Repository Structure
The monorepo is structured as follows:
```
vulavula-examples/
  ├── 1-intent-detection-and-language-switching/
  │    ├── README.md
  │    ├── src/
  |    ├── tests/
  ├── 3-transcription
  │    ├── README.md
  │    ├── src/
  |    ├── tests/
  │    └── ...
  └── README.md
```
Each directory under `vulavula-examples/` represents a standalone use case, complete with its own `README.md` that 
provides details on the use case, setup instructions, and how to run the example.

## Getting Started
1. Clone the Repository:

    Clone this repository to your local machine:
    ```bash
   git clone https://github.com/Lelapa-AI/vulavula-examples.git
   cd vulavula-examples
   ```
2. Navigate to a directory that has an example you are interested in.

## Prerequisites
We use `pdm` for managing dependencies and as a script runner. Ensure you have `pdm` installed in your path.
```commandline
pip install --user pdm
```
Or if you are on macos:
```commandline
brew install pdm
```
More up-to-date installation instructions can be found [here](https://pdm-project.org/en/latest/).

## Examples
[1-intent-detection-and-language-switching](1-intent-detection-and-language-switching/)
[3-Transcription](3-transcription/)
