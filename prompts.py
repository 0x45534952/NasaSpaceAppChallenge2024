import requests
import textwrap
import ollama
from constants import ollama_model
import json
import re

class NASAExperimentSummary:
    def __init__(self, experiment_name):
        self.url = "https://osdr.nasa.gov/geode-py/ws/repo/studies/" + experiment_name
        self.description = "No description available."
        self.protocols = []

    def fetch_data(self):
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.description = data.get("description", "No description available.")
            self.protocols = data.get("protocols", [])
        except requests.exceptions.Timeout:
            print("Error: The request timed out.")
        except requests.exceptions.ConnectionError:
            print("Error: Failed to establish a connection.")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            self.description = "No description available."
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        except Exception as err:
            print(f"An unexpected error occurred: {err}")

    def map_protocols(self):
        if not self.protocols:
            return [{"name": "Unnamed Protocol", "description": "No description provided."}]

        return [
            {"name": protocol.get("name", "Unnamed Protocol"), "description": protocol.get("description", "No description provided.")}
            for protocol in self.protocols
        ]
    def prompt_summary(self, summary_output):
        try:
            completion = ollama.chat(
                model=ollama_model,
                messages=[{"role": "user", "content": summary_output}],
            )
            return completion["message"]["content"]
        except Exception as e:
            print(f"Error while calling Ollama API: {e}")
            return None
                          
    def prompt(self):
        self.fetch_data()
        summary_output = self.generate_summary()
        final_json_string = self.prompt_summary(summary_output)
        # format final_json to be a valid JSON string
        final_json = self.clean_and_parse_json(final_json_string)
        return final_json

    def clean_and_parse_json(self, json_string):
        # Step 1: Fix common quote issues
        json_string = re.sub(r'(\w)"(\w)', r"\1'\2", json_string)
        
        # Step 2: Fix incorrect quotes inside lists (e.g., in goals)
        json_string = re.sub(r'"(\w+)"\s(\w)', r"'\1' \2", json_string)

        # step 2-3: Delete everything before the first '{' and after the last '}'
        json_string = json_string[json_string.find('{'):json_string.rfind('}') + 1]
        # Step 3: Identify unmatched closing braces
        balance = 0
        unmatched_indexes = []

        for index, char in enumerate(json_string):
            if char == '{':
                balance += 1
            elif char == '}':
                balance -= 1
                if balance < 0:
                    # If we have more closing braces than opening ones, this is unmatched
                    unmatched_indexes.append(index)
                    balance = 0  # Reset balance after noting unmatched brace

        # Remove unmatched closing braces
        for index in reversed(unmatched_indexes):
            json_string = json_string[:index] + json_string[index + 1:]

        # Step 4: Try to parse the JSON
        try:
            # Load the string as JSON
            json_object = json.loads(json_string)
            return json_object
        except json.JSONDecodeError as e:
            print("JSON Decode Error:", e)
            print("Invalid JSON string:", json_string)
            return None

    def format_protocols(self):
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

