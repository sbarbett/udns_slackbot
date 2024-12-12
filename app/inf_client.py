from asst_client import AssistantClient
from slackstyler import SlackStyler


class InferenceClient:
    """
    The InferenceClient class provides methods to interact with various assistants
    for analyzing DNS zone files, conducting health checks, and answering DNS-related queries.
    """

    def __init__(self):
        """
        Initialize the InferenceClient.

        No arguments are required for initialization. The client will dynamically
        instantiate AssistantClient instances for specific assistant interactions.
        """
        pass

    def status_check(self, status, say):
        """
        Perform a system status check analysis using the OpenAI Assistant.

        Args:
            status (str): The JSON response from the UltraDNS system status page.
            say (function): The Slack say function to send messages to a Slack channel.

        Raises:
            Exception: If any error occurs during the assistant interaction.
        """
        try:
            asst_client = AssistantClient("system_status")
            prompt = f"""
            Analyze the following UltraDNS system status JSON response. Provide a summary of the current state of the system in a conversational format. Focus on:
            - Whether all services are operational or if any are down/degraded.
            - Highlighting any affected services with their names and the most recent update timestamps.
            - Summarizing upcoming maintenance, including affected services, scheduled times, and potential impacts.
            - If there are active incidents, briefly describe them and the affected services.

            If all services are operational with no issues or maintenance, state "All systems are operational, and no upcoming maintenance is scheduled."

            JSON System Status:
            {status}
            """
            raw_messages = asst_client.run_assistant(prompt)
            self._process_response(raw_messages, say)
        except Exception as e:
            say(f"Error during assistant run: {e}")

    def zone_inference(self, zone_file, say):
        """
        Perform DNS zone file analysis using the OpenAI Assistant.

        Args:
            zone_file (str): The content of the DNS zone file to analyze.
            say (function): The Slack say function to send messages to a Slack channel.

        Raises:
            Exception: If any error occurs during the assistant interaction.
        """
        try:
            asst_client = AssistantClient("zone_analyzer")
            prompt = f"""
            Analyze the following DNS zone file for compliance with DNS standards and best practices. Only make suggestions if there are clear issues or meaningful opportunities for optimization. If everything is in order, state "No issues detected." Do NOT provide any suggestions regarding the SOA record unless explicitly requested. Tags should focus on DNS-specific themes.

            Return your response in this format:
            Suggestions:
            - Suggestion 1
            - Suggestion 2

            Tags (JSON):
            {{
              "tags": ["meaningful-tag1", "meaningful-tag2"]
            }}

            Zone file:
            {zone_file}
            """
            raw_messages = asst_client.run_assistant(prompt)
            self._process_response(raw_messages, say)
        except Exception as e:
            say(f"Error during assistant run: {e}")

    def zone_healthcheck(self, healthcheck, say):
        """
        Perform a zone health check analysis using the OpenAI Assistant.

        Args:
            healthcheck (str): The JSON response from a health check to analyze.
            say (function): The Slack say function to send messages to a Slack channel.

        Raises:
            Exception: If any error occurs during the assistant interaction.
        """
        try:
            asst_client = AssistantClient("zone_healthcheck")
            prompt = f"""
            Analyze the following DNS health check JSON response. Summarize the overall status of each category, highlight critical issues or warnings, and provide actionable recommendations for improvement. Include the description and relevant messages from the JSON to provide context for your recommendations. If everything is in order, state "No issues detected."

            Do not restate successful checks unless they add critical context. Focus on items with a status of "ERROR", "WARNING", or "BEST_PRACTICE".

            Your response format should be a general summary of the issues identified in the health check. Provide it in a conversational, human-readable format and not a list.

            Health check JSON:
            {healthcheck}
            """
            raw_messages = asst_client.run_assistant(prompt)
            self._process_response(raw_messages, say)
        except Exception as e:
            say(f"Error during assistant run: {e}")

    def dns_helper(self, question, say):
        """
        Answer general DNS questions using the OpenAI Assistant.

        Args:
            question (str): The DNS-related question to answer.
            say (function): The Slack say function to send messages to a Slack channel.

        Raises:
            Exception: If any error occurs during the assistant interaction.
        """
        try:
            asst_client = AssistantClient("dns_helper")
            prompt = f"""
            Answer the following question about the Domain Name System (DNS). Provide a clear and accurate response based on relevant RFCs and DNS best practices. If the question is unrelated to DNS, respond with: "I'm sorry, but I am an assistant specifically designed for answering DNS questions. I can't help with that."

            Question:
            {question}
            """
            raw_messages = asst_client.run_assistant(prompt)
            self._process_response(raw_messages, say)
        except Exception as e:
            say(f"Error during assistant run: {e}")

    @staticmethod
    def _process_response(raw_messages, say):
        """
        Parse and style the response from the assistant.

        Args:
            raw_messages (list): A list of raw message objects returned by the assistant.
            say (function): The Slack say function to send messages to a Slack channel.

        Raises:
            Exception: If the response is empty or cannot be processed.
        """
        response_text = ""
        for message in raw_messages:
            if message.role == "assistant":
                for part in message.content:
                    if part.type == "text" and hasattr(part, "text") and hasattr(part.text, "value"):
                        response_text += part.text.value

        if response_text:
            styler = SlackStyler()
            say(styler.convert(response_text))
        else:
            say("The assistant's response was empty.")
