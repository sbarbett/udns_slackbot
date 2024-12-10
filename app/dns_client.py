import json
import time
from ultra_rest_client.connection import RestApiConnection


class UltraDNSClient:
    """
    A client for interacting with the UltraDNS API to retrieve DNS zones and health checks.

    This client provides functionality for:
    - Authenticating with the UltraDNS API.
    - Fetching zone data.
    - Performing health checks on zones.
    - Handling task-based operations (e.g., zone exports and health checks) with polling.

    The class abstracts API interactions and ensures error handling for common operations.

    Attributes:
        client (RestApiConnection): Authenticated connection to the UltraDNS API.
    """

    def __init__(self, username, password):
        """
        Initialize the UltraDNSClient.

        Args:
            username (str): The UltraDNS username for authentication.
            password (str): The UltraDNS password for authentication.

        Raises:
            RuntimeError: If authentication with UltraDNS fails.
        """
        self.client = RestApiConnection()
        try:
            self.client.auth(username, password)
        except Exception as e:
            raise RuntimeError(f"Failed to authenticate with UltraDNS: {e}")

    def fetch_zone_data(self, zone_name):
        """
        Fetch zone data for a specific zone.

        Args:
            zone_name (str): The name of the zone to fetch.

        Returns:
            str: The raw zone data.

        Raises:
            ValueError: If the zone does not exist.
        """
        self._validate_zone_exists(zone_name)
        task_id = self._initiate_zone_export([zone_name])
        self._poll_task_status(task_id)
        return self._download_exported_data(task_id)

    def fetch_health_check(self, zone_name):
        """
        Fetch health check for a specific zone.

        Args:
            zone_name (str): The name of the zone to check.

        Returns:
            str: The health check result in JSON format.

        Raises:
            ValueError: If the zone does not exist.
        """
        self._validate_zone_exists(zone_name)
        location = self._initiate_health_check(zone_name)
        return self._download_health_check(location)

    def _validate_zone_exists(self, zone_name):
        """
        Validate if the zone exists in UltraDNS.

        Args:
            zone_name (str): The name of the zone to validate.

        Raises:
            ValueError: If the zone does not exist or the response format is unexpected.
        """
        response = self.client.get(f"/v3/zones/{zone_name}")
        if isinstance(response, list):
            # Check if it's an error message
            error = response[0]
            if isinstance(error, dict) and "errorMessage" in error:
                raise ValueError(f"Zone validation failed: {error['errorMessage']}")
        elif not isinstance(response, dict):
            raise ValueError(f"Unexpected response format while validating zone {zone_name}: {response}")

    def _initiate_zone_export(self, zone_names):
        """
        Initiate a zone export task.

        Args:
            zone_names (list): A list of zone names to export.

        Returns:
            str: The task ID for the initiated export.

        Raises:
            RuntimeError: If the task initiation fails.
        """
        payload = {"zoneNames": zone_names}
        response = self.client.post("/v3/zones/export", json.dumps(payload))
        return response["task_id"]

    def _poll_task_status(self, task_id):
        """
        Poll the status of a task until it completes.

        Args:
            task_id (str): The ID of the task to monitor.

        Raises:
            Exception: If the task fails or encounters an error.
        """
        while True:
            response = self.client.get(f"/tasks/{task_id}")
            if response["code"] == "COMPLETE":
                break
            if response["code"] == "ERROR":
                raise Exception(f"Error processing task {task_id}: {response}")
            time.sleep(10)

    def _download_exported_data(self, task_id):
        """
        Download the exported data for a completed task.

        Args:
            task_id (str): The ID of the completed task.

        Returns:
            str: The exported data in raw format.
        """
        return self.client.get(f"/tasks/{task_id}/result")

    def _initiate_health_check(self, zone_name):
        """
        Initiate a health check task.

        Args:
            zone_name (str): The name of the zone to check.

        Returns:
            str: The location of the health check task.

        Raises:
            RuntimeError: If the task initiation fails.
        """
        response = self.client.post(f"/v1/zones/{zone_name}/healthchecks", json.dumps({}))
        return response["location"]

    def _download_health_check(self, location):
        """
        Wait for a health check to complete and download its results.

        Args:
            location (str): The location of the health check task.

        Returns:
            str: The health check results in JSON format.

        Raises:
            Exception: If the health check fails or encounters an error.
        """
        while True:
            response = self.client.get(location)
            if response["state"] == "COMPLETED":
                return json.dumps(response)
            if response["state"] == "FAILED":
                raise Exception(f"Error processing health check: {response}")
            time.sleep(10)
