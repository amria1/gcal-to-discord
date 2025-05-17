# README

1. Get the secret Google calendar URL.
2. Get a Discord bot token.
3. (Development) Build the image: `docker build -t gcal-to-discord .`
4. Run the container: `docker run -d --name gcal-to-discord --env-file .env gcal-to-discord`
