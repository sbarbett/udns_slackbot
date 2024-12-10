import json
import os
from openai import OpenAI


class AssistantClient:
    """
    A client for interacting with specific OpenAI assistants defined in a configuration file.

    This client abstracts the process of interacting with OpenAI assistants, including:
    - Loading assistant IDs from a configuration file.
    - Creating threads for conversation context.
    - Adding messages to threads.
    - Running the assistant to process input and return responses.

    The class supports multiple assistants by specifying the assistant name when instantiated.

    Attributes:
        config_file (str): Path to the configuration file containing assistant IDs.
        api_key (str): API key for OpenAI.
        client (OpenAI): Instance of the OpenAI client.
        assistant_id (str): ID of the specified assistant.
    """

    def __init__(self, assistant_name, config_file="/data/config.json", api_key=None):
        """
        Initialize the AssistantClient with a specific assistant.

        Args:
            assistant_name (str): The name of the assistant to use (e.g., "zone_analyzer").
            config_file (str, optional): Path to the configuration file. Defaults to "/data/config.json".
            api_key (str, optional): API key for OpenAI. Defaults to None.
        """
        self.config_file = config_file
        self.api_key = api_key or os.getenv("OPENAI_KEY")
        if not self.api_key:
            raise EnvironmentError("OPENAI_KEY environment variable is not set and no API key was provided.")
        self.client = OpenAI(api_key=self.api_key)
        self.assistant_id = self._load_assistant_id(assistant_name)

    def _load_assistant_id(self, assistant_name):
        """
        Load the assistant ID from the config file.

        Args:
            assistant_name (str): The name of the assistant (e.g., "zone_analyzer").

        Returns:
            str: The assistant ID.

        Raises:
            FileNotFoundError: If the config file does not exist.
            ValueError: If the config file is invalid or the assistant ID is missing.
            RuntimeError: For any other errors while loading the configuration.
        """
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
            key = f"{assistant_name}_id"
            assistant_id = config.get(key)
            if not assistant_id or not assistant_id.startswith("asst_"):
                raise ValueError(f"Invalid or missing '{key}' in {self.config_file}.")
            return assistant_id
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {self.config_file} not found.")
        except json.JSONDecodeError:
            raise ValueError(f"Configuration file {self.config_file} is not valid JSON.")
        except Exception as e:
            raise RuntimeError(f"An error occurred while loading the configuration: {e}")

    def _create_thread(self):
        """
        Create a new thread.

        Returns:
            str: The thread ID.

        Raises:
            RuntimeError: If the thread creation fails.
        """
        try:
            thread = self.client.beta.threads.create()
            return thread.id
        except Exception as e:
            raise RuntimeError(f"Failed to create a thread: {e}")

    def _add_message_to_thread(self, thread_id, content):
        """
        Add a message to the thread.

        Args:
            thread_id (str): The thread ID.
            content (str): The content to add to the thread.

        Raises:
            RuntimeError: If adding the message fails.
        """
        try:
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to add a message to the thread: {e}")

    def run_assistant(self, content):
        """
        Run the assistant by creating a thread and adding a message.

        Args:
            content (str): The content to analyze or process.

        Returns:
            list: A list of messages from the assistant.

        Raises:
            RuntimeError: If the assistant run fails.
        """
        thread_id = self._create_thread()
        self._add_message_to_thread(thread_id, content)

        try:
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                instructions="Address the user as user."
            )
            if run.status == "completed":
                return self.client.beta.threads.messages.list(thread_id=thread_id)
            else:
                raise RuntimeError(f"Run not completed. Status: {run.status}")
        except Exception as e:
            raise RuntimeError(f"Error during assistant run: {e}")