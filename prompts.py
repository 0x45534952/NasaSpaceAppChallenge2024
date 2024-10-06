import requests
import textwrap
import ollama
import json
import re
import logging
from constants import ollama_model

# Constants for error messages and JSON structure
DEFAULT_DESCRIPTION = "No description available."
DEFAULT_PROTOCOL = {"name": "Unnamed Protocol", "description": "No description provided."}
EXPERIMENT_URL_BASE = "https://osdr.nasa.gov/geode-py/ws/repo/studies/"
JSON_FILE_PATH = 'data/data.json' 
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NASAExperimentSummary:
    def __init__(self, experiment_name):
        self.url = EXPERIMENT_URL_BASE + experiment_name
        self.description = DEFAULT_DESCRIPTION
        self.protocols = []
        self.json_file_path = "data/data.json"

    def fetch_data(self):
        """Fetches experiment data from NASA API."""
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.description = data.get("description", DEFAULT_DESCRIPTION)
            self.protocols = data.get("protocols", [])
            logging.info("Data fetched successfully.")
        except requests.exceptions.Timeout:
            logging.error("The request timed out.")
            raise
        except requests.exceptions.ConnectionError:
            logging.error("Failed to establish a connection.")
            raise
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
            raise
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error occurred: {req_err}")
            raise
        except Exception as err:
            logging.exception("An unexpected error occurred.")
            raise

    def map_protocols(self):
        """Maps the protocols to a structured format."""
        if not self.protocols:
            return [DEFAULT_PROTOCOL]

        return [
            {
                "name": protocol.get("name", DEFAULT_PROTOCOL["name"]),
                "description": protocol.get("description", DEFAULT_PROTOCOL["description"])
            }
            for protocol in self.protocols
        ]

    def prompt_summary(self, summary_output):
        """Generates a summary using the Ollama API."""
        try:
            completion = ollama.chat(
                model=ollama_model,
                messages=[{"role": "user", "content": summary_output}],
            )
            return completion["message"]["content"]
        except Exception as e:
            logging.error(f"Error while calling Ollama API: {e}")
            return None

    def prompt(self):
        """Main method to execute the fetching and summarizing process."""
        try:
            self.fetch_data()
            
            if self.description == DEFAULT_DESCRIPTION:
                return None
            
            summary_output = self.generate_summary()
            final_json_string = self.prompt_summary(summary_output)

            # Format final_json to be a valid JSON string
            final_json = self.clean_and_parse_json(final_json_string)
            return final_json

        except Exception as e:
            logging.error("Error while fetching and summarizing data", exc_info=True)  # Log stack trace
            return None

    def clean_and_parse_json(self, json_string):
        """Cleans and parses the JSON string."""
        json_string = self._fix_quotes(json_string)
        json_string = self._trim_json_string(json_string)
        json_string = self._remove_unmatched_braces(json_string)

        try:
            json_object = json.loads(json_string)
            return json_object
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error: {e}")
            logging.error(f"Invalid JSON string: {json_string}")
            return None

    def _fix_quotes(self, json_string):
        """Fix common quote issues."""
        json_string = re.sub(r'(\w)"(\w)', r"\1'\2", json_string)
        json_string = re.sub(r'"(\w+)"\s(\w)', r"'\1' \2", json_string)
        return json_string

    def _trim_json_string(self, json_string):
        """Trims everything before the first '{' and after the last '}'."""
        return json_string[json_string.find('{'):json_string.rfind('}') + 1]

    def _remove_unmatched_braces(self, json_string):
        """Identifies and removes unmatched closing braces."""
        balance = 0
        unmatched_indexes = []

        for index, char in enumerate(json_string):
            if char == '{':
                balance += 1
            elif char == '}':
                balance -= 1
                if balance < 0:
                    unmatched_indexes.append(index)
                    balance = 0

        for index in reversed(unmatched_indexes):
            json_string = json_string[:index] + json_string[index + 1:]

        return json_string

    def format_protocols(self):
        """Formats protocols into a readable string."""
        mapped_protocols = self.map_protocols()
        return "\n".join(
            f"{index + 1}st Protocol:\nName: {protocol['name']}\nDescription: {protocol['description']}\n"
            for index, protocol in enumerate(mapped_protocols)
        )
    def generate_summary(self):
        if self.description == "No description available.":
            return "No description available."
        experiment_overview = textwrap.dedent(f"""
        Objective:

        Your task is to create a compelling and informative summary of a NASA experiment, aimed at engaging new and mid-level scientists. The summary should include the following aspects:

        1. Experiment Overview: Start with a brief introduction, clearly explaining the experiment's focus and context. Ensure it’s accessible to those with a basic understanding of science but not necessarily advanced knowledge.

        2. Goals: Outline the key objectives of the experiment in a clear and straightforward manner. Make it easy for readers to grasp the experiment’s purpose and desired outcomes.

        3. Significance: Explain why this experiment is important, focusing on its potential impact on scientific knowledge or practical applications. Highlight how it could advance fields such as space exploration, human health, technology, or other relevant areas.

        4. Protocol: Summarize the main steps of the experimental protocol in a simple, understandable way. Avoid excessive detail but ensure key procedures are covered. Define any complex terms or concepts in layman's terms to aid comprehension, ensuring new scientists can easily follow along.

        Context for Summary:

        This summary will appear on a webpage designed to showcase NASA’s experimentation data, so it should be engaging and clear. The tone should stimulate curiosity and be easy to understand, without sacrificing important information.

        Output:
        Make sure it always respects this JSON structure, and the output should be the JSON and the JSON only in a valid format:
        {{
            "experiment_name": ...,
            "experiment_overview": ...,
            "goals" : [
                ...,
                ...,
            ],
            "significance": ...,
            "protocol": [
                {{"name": ..., "description": ... }},
                ...,
            ]
        }}

        Here's the description of the experiment:

        {self.description}
        """)

        protocols_summary = self.format_protocols()
        summary = experiment_overview #+ "\n" + protocols_summary
        return summary
    
    @staticmethod
    def update_json(experiment_id, updated_data):
        """Updates the JSON file with new data for the given experiment ID."""
        allowed_fields = {"experiment_name", "experiment_overview", "goals", "significance", "protocol"}

        try:
            # Load existing JSON data
            with open(JSON_FILE_PATH, "r") as json_file:
                json_obj = json.load(json_file)

            experiment_key = f"Experiment {experiment_id}"

            # Update only allowed fields present in the updated_data
            if experiment_key in json_obj:
                for key, value in updated_data.items():
                    if key in allowed_fields:
                        json_obj[experiment_key][key] = value
                        logging.info(f"Updated '{key}' for {experiment_key}.")
                    else:
                        logging.warning(f"Skipping update for unallowed field: {key}")
            else:
                logging.error(f"Experiment '{experiment_id}' not found in the JSON.")
                return

            # Write the updated JSON object back to the file
            with open(JSON_FILE_PATH, "w") as json_file:
                json.dump(json_obj, json_file, indent=4)
            logging.info(f"Successfully updated {experiment_key} in {JSON_FILE_PATH}.")
        except FileNotFoundError:
            logging.error(f"File not found: {JSON_FILE_PATH}")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")