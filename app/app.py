import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from dns_client import UltraDNSClient
from inf_client import InferenceClient

# Step 1: Load environment variables
load_dotenv()

# Step 2: Retrieve required environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
ULTRADNS_USERNAME = os.getenv("ULTRADNS_USERNAME")
ULTRADNS_PASSWORD = os.getenv("ULTRADNS_PASSWORD")

# Step 3: Validate environment variables
if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError("Missing SLACK_BOT_TOKEN or SLACK_APP_TOKEN environment variables.")
if not OPENAI_KEY:
    raise ValueError("Missing OPENAI_KEY environment variable.")
if not ULTRADNS_USERNAME or not ULTRADNS_PASSWORD:
    raise ValueError("Missing ULTRADNS_USERNAME or ULTRADNS_PASSWORD environment variables.")

# Step 4: Initialize Slack app and InferenceClient
app = App(token=SLACK_BOT_TOKEN)
inference_client = InferenceClient()

# Step 5: Define the bot commands
# Slash command: /udns-system-status
@app.command("/udns-system-status")
def udns_system_status(ack, respond):
    """
    Handle the /udns-system-status Slack command.

    Args:
        ack: Acknowledge the command.
        respond: Function to send a response to Slack.

    - Fetches the UltraDNS system status JSON.
    - Calls InferenceClient to analyze the system status.
    """
    ack()
    try:
        # Fetch system status using UltraDNSClient
        client = UltraDNSClient(ULTRADNS_USERNAME, ULTRADNS_PASSWORD)
        system_status = client.fetch_system_status()

        # Use InferenceClient to process the system status
        inference_client.status_check(system_status, respond)

    except Exception as e:
        respond(f"Error fetching or analyzing system status: {e}")

# Slash command: /analyze-zone-file
@app.command("/analyze-zone-file")
def analyze_zone_file(ack, respond, command):
    """
    Handle the /analyze-zone-file Slack command.

    Args:
        ack: Acknowledge the command.
        respond: Function to send a response to Slack.
        command: The incoming Slack command data.

    - Parses the zone names from the command input.
    - Uses UltraDNSClient to fetch zone data.
    - Calls InferenceClient to analyze the zone file.
    """
    ack()
    zones = [zone.strip(",") for zone in command["text"].split()]
    try:
        client = UltraDNSClient(ULTRADNS_USERNAME, ULTRADNS_PASSWORD)
    except Exception as e:
        respond(f"Authentication failed: {e}")
        return

    results = []
    for zone_name in zones:
        try:
            zone_data = client.fetch_zone_data(zone_name)
            inference_client.zone_inference(zone_data, respond)
            results.append(f"Zone {zone_name} analyzed successfully.")
        except Exception as e:
            results.append(f"Error analyzing zone {zone_name}: {e}")

    respond("\n".join(results))

# Slash command: /zone-health-check
@app.command("/zone-health-check")
def zone_health_check(ack, respond, command):
    """
    Handle the /zone-health-check Slack command.

    Args:
        ack: Acknowledge the command.
        respond: Function to send a response to Slack.
        command: The incoming Slack command data.

    - Parses the zone names from the command input.
    - Uses UltraDNSClient to fetch health check data.
    - Calls InferenceClient to analyze the health check JSON.
    """
    ack()
    zones = [zone.strip(",") for zone in command["text"].split()]
    try:
        client = UltraDNSClient(ULTRADNS_USERNAME, ULTRADNS_PASSWORD)
    except Exception as e:
        respond(f"Authentication failed: {e}")
        return

    results = []
    for zone_name in zones:
        try:
            health_check = client.fetch_health_check(zone_name)
            inference_client.zone_healthcheck(health_check, respond)
            results.append(f"Zone {zone_name} health check completed.")
        except Exception as e:
            results.append(f"Error analyzing zone {zone_name}: {e}")

    respond("\n".join(results))

# Event listener for bot mentions
@app.event("app_mention")
def handle_mention(event, say):
    """
    Handle @mention messages in Slack.

    Args:
        event: The incoming Slack event data.
        say: Function to send a response to Slack.

    - Extracts and processes the text after the @mention.
    - Calls InferenceClient to handle DNS-related questions.
    """
    text = event.get("text", "").replace(f"<@{event['user']}>", "").strip()
    if not text:
        say("Please provide a question related to DNS.")
        return

    inference_client.dns_helper(text, say)

# Generic message handler
@app.event("message")
def handle_message_events(body, logger):
    """
    Log and handle unprocessed Slack messages.

    Args:
        body: The incoming Slack message data.
        logger: Logger instance to log the message data.
    """
    logger.info(body)

# Step 6: Start the Slack app using the SocketModeHandler
if __name__ == "__main__":
    """
    Initialize the SocketModeHandler to listen for events
    and handle Slack commands and events.
    """
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
