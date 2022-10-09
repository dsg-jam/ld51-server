# LD51 Server

## Instructions

### Preparing your environment

1. Install [Python](https://www.python.org) version 3.10 or later.
2. Install [Poetry](https://python-poetry.org) version 1.2 or later.
3. Add [Poe the Poet](https://github.com/nat-n/poethepoet) plugin to Poetry:

   ```sh
   poetry self add 'poethepoet[poetry_plugin]'
   ```

4. Install project-specific dependencies:

   ```sh
   # run in project root directory
   poetry install
   ```

### Running the server

```sh
poetry poe run
```

### Workflow

Run the unit tests:

```sh
poetry poe test
```

Run all checks before pushing your changes:

```sh
poetry poe commit-flow
```
