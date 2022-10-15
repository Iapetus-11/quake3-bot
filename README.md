# Discord.py template

## Features
- Comes with everything needed to start a Discord bot
- Configuration - auto loaded and validated using Pydantic, example file generation
- Database - sqlite database using aiosqlite, automatically setup on startup
- Error handling - command error handling is ready to go
- Basic structure - basic structure and boilerplate of the bot has already been layed out


## Usage
1. Make sure you have [Python](https://python.org) installed
2. Install [Poetry](https://python-poetry.org) with pip like `py -m pip install poetry` or if you're not on Windows `python3 -m pip install poetry`
2. Install dependencies with [Poetry](https://python-poetry.org) using the command `poetry install`
3. Create a file called `.env` based off the contents of `example.env`
4. Run the bot using `poetry run py -m bot` or if you're not on Windows `poetry run python3 -m bot`
