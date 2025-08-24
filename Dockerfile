# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only the dependency definition files to leverage Docker layer caching
# Copy the dependency definition file
COPY pyproject.toml ./

# Install project dependencies
RUN poetry config virtualenvs.create false && poetry install --no-root --only main --no-interaction --no-ansi

# Copy the rest of the application's code
COPY . .

# Command to run the application
# Command to run the application using the telegram bot script
CMD ["python", "run_telegram_bot.py"]
