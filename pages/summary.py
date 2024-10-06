import dash_bootstrap_components as dbc
from dash import dcc, html, register_page, Input, Output, callback
from urllib.parse import parse_qs
from prompts import NASAExperimentSummary  # Import your class
import json
import os
import logging
import plotly.express as px
import pandas as pd
import re

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Register the page with a specified path
register_page(__name__, path='/summary')

# File path configuration (for scalability)
JSON_FILE_PATH = os.getenv('DATA_JSON_PATH', 'data/data.json')  # Use environment variable for the JSON file path

### Helper Functions ###

def load_experiment_data():
    """Loads experiment data from a JSON file with error handling."""
    try:
        with open(JSON_FILE_PATH) as json_file:
            data = json.load(json_file)
            logging.info(f"Successfully loaded data from {JSON_FILE_PATH}")
            return data
    except FileNotFoundError:
        logging.error(f"File not found: {JSON_FILE_PATH}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON file: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading data: {e}")
        return None

def find_experiment_by_id(experiment_id, data):
    """Finds the experiment in the JSON file using the provided ID."""
    for key, experiment in data.items():
        if experiment.get('value') == experiment_id:
            logging.info(f"Experiment {experiment_id} found in the data.")
            return experiment
    logging.error(f"Experiment ID {experiment_id} not found in the JSON data.")
    return None

def create_protocol_accordion(protocols):
    """Helper function to create an accordion layout for protocols."""
    if not protocols:
        return html.P("No protocols available", style={'font-size': '16px'})
    
    return dbc.Accordion(
        children=[
            dbc.AccordionItem(
                title=protocol.get('name', 'No Name'),  # Fallback for missing protocol name
                children=html.P(protocol.get('description', 'No Description')),
            ) for protocol in protocols
        ],
        start_collapsed=True,
        flush=True
    )

def display_error_message(title, message):
    """Helper function to display an error message section."""
    return dbc.Container([
        dbc.Row(dbc.Col(html.H2(title, className="mb-4"), width=12)),
        dbc.Row(dbc.Col(html.P(message), width=12))
    ], fluid=True)

def fetch_experiment_data(experiment_id, fallback_data):
    """Fetch the experiment summary data using NASAExperimentSummary class or fallback JSON."""
    try:
        experiment_summary = NASAExperimentSummary(experiment_id)
        summary_json = experiment_summary.prompt()
        if summary_json is not None:
            logging.info(f"Successfully fetched data for experiment ID: {experiment_id}")
            return summary_json
    except Exception as e:
        logging.error(f"Error fetching experiment summary: {e}")
    
    logging.info(f"Using fallback data for experiment ID: {experiment_id}")
    return fallback_data

### Layout ###

# Define a consistent, minimalistic style for sections
SECTION_STYLE = {
    'padding': '40px 20px',
    'margin': '0 auto',
    'max-width': '1200px',
    'line-height': '1.8'
}

HEADER_STYLE = {
    'padding': '60px 20px 20px 20px',
    'text-align': 'center',
    'background-color': '#F7F7F7',
    'color': '#0B3D91'  # Primary color for header
}

CONTENT_STYLE = {
    'background-color': '#FFFFFF',
    'border-radius': '10px',
    'box-shadow': '0 4px 6px rgba(0,0,0,0.1)',
    'padding': '30px',
    'margin-bottom': '40px',
    'justify-content': 'center',
    'display': 'flex',
    'flex-direction': 'column',
}

# Loader spinner to display while fetching data
loader_spinner = dbc.Spinner(color="primary", size="lg")

layout = html.Div([
    dcc.Location(id='url', refresh=False),

    # Full-screen loader while waiting for content
    html.Div(id='loader', children=loader_spinner, style={'position': 'fixed', 'top': '0', 'left': '0', 'width': '100%', 'height': '100%', 'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'background-color': 'rgba(255, 255, 255, 0.8)', 'z-index': '9999'}),

    # Header section with experiment name, initially empty
    html.Div(id='experiment-name', hidden=True, style=HEADER_STYLE),  # Hidden by default

    # Placeholder for dynamically loaded content based on the URL
    html.Div(id='summary-content', hidden=True, style=SECTION_STYLE)  # Hidden by default
])

### Callback ###

@callback(
    [Output('summary-content', 'children'),
     Output('experiment-name', 'children'),
     Output('loader', 'style'),  # Hide loader after content is loaded
     Output('summary-content', 'hidden'),  # Show content when ready
     Output('experiment-name', 'hidden')],  # Show experiment name when ready
    Input('url', 'search')
)

def update_summary_content(search):
    # Parse the query parameters from the URL
    params = parse_qs(search.lstrip('?'))  
    experiment_id = params.get('id', [None])[0]
    charts_content = None

    if not experiment_id:
        logging.error("No experiment ID provided in URL.")
        return (display_error_message("Experiment Not Found", "No experiment ID was provided in the URL."), None, {'display': 'flex'}, True, True)

    # If specific experiment ID 'OSD-665', generate and return charts
    if experiment_id == 'OSD-665':
        logging.info("Displaying summary for experiment OSD-665")
        
        body_weight_chart = create_body_weight_chart(merged_df_665)
        rrna_contamination_chart = create_rrna_contamination_chart_665(merged_rna_df_665)
        habitat_chart = create_habitat_chart(merged_df_665)
        violin_chart = create_violin(merged_df_665)
        
        charts_content = html.Div([
            html.H2("Violin Plot of Body Weight"),
            violin_chart,
            html.H2("Body Weight Chart"),
            body_weight_chart,
            html.H2("rRNA Contamination Chart"),
            rrna_contamination_chart,
            html.H2("Habitat Chart"),
            habitat_chart,
        ], style=CONTENT_STYLE)
    
    if experiment_id == 'OSD-379':
        logging.info("Displaying summary for experiment OSD-379")

        avg_qa_chart = create_avg_qa_score_chart(df_379, samples_379)
        rrna_contamination_chart = create_rrna_contamination_chart(df_rrna_filtered, samples_379)
        qa_score_by_age = create_qa_score_by_age_chart(df_379, samples_379)
        
        charts_content = html.Div([
            html.H2("Average QA Score Chart"),
            avg_qa_chart,
            html.H2("rRNA Contamination Chart"),
            rrna_contamination_chart,
            html.H2("Read Depth Chart"),
            qa_score_by_age,
        ], style=CONTENT_STYLE)



    # Load experiment data from JSON if experiment ID is not 'OSD-665'
    experiment_data = load_experiment_data()
    if not experiment_data:
        return (display_error_message("Data Loading Error", "Failed to load experiment data. Please try again later."), None, {'display': 'flex'}, True, True)

    # Find the experiment by ID in the JSON file
    experiment = find_experiment_by_id(experiment_id, experiment_data)
    if not experiment:
        return (display_error_message("Experiment Not Found", f"Experiment with ID {experiment_id} was not found."), None, {'display': 'flex'}, True, True)

    if experiment.get('experiment_name') == "N/A":
        summary_json = fetch_experiment_data(experiment_id, experiment)
        logging.info(f"Updating JSON data for experiment ID: {experiment_id}")
        NASAExperimentSummary.update_json(experiment_id, summary_json)
    else:
        summary_json = experiment

    logging.info(f"Displaying summary for experiment ID: {experiment_id}")
    
    # Build the page content dynamically
    experiment_name = summary_json.get("experiment_name", "Experiment Overview")
    content = html.Div([

        html.Div([
            dbc.Row(dbc.Col(html.H2("🧪 Experiment Overview", className="mb-4", style={'color': '#0B3D91'}), width=12)),
            dbc.Row(dbc.Col(html.P(summary_json.get("experiment_overview", "No Overview Provided")), width=12))
        ], style=CONTENT_STYLE),

        html.Div([
            dbc.Row(dbc.Col(html.H2("🎯 Mission Goals", className="mb-4", style={'color': '#0B3D91'}), width=12)),
            dbc.Row(dbc.Col(html.Ul([html.Li(goal) for goal in summary_json.get('goals', [])]), width=12))
        ], style=CONTENT_STYLE),

        html.Div([
            dbc.Row(dbc.Col(html.H2("🌟 Significance", className="mb-4", style={'color': '#0B3D91'}), width=12)),
            dbc.Row(dbc.Col(html.P(summary_json.get('significance', "No Significance Provided")), width=12))
        ], style=CONTENT_STYLE),

        html.Div([
            dbc.Row(dbc.Col(html.H2("📝 Protocol", className="mb-4", style={'color': '#0B3D91'}), width=12)),
            dbc.Row(dbc.Col(create_protocol_accordion(summary_json.get('protocol', [])), width=12))
        ], style=CONTENT_STYLE),

        charts_content,

        html.Div([
            dbc.Row(dbc.Col(html.H2("Further Analysis", className="mb-4", style={'color': '#0B3D91'}), width=12)),
            dbc.Row(dbc.Col(html.P("Explore the comprehensive analysis derived from the experiment data. "
                                    "This includes graphical representations, interpretations, and "
                                    "potential implications of the findings.", style={'font-size': '16px'}), width=12)),
            dbc.Row(dbc.Col(dbc.Button("View Full Analysis", color="primary", href=f'/ai?id={experiment_id}', style={
                "background-color": '#0B3D91',  # Match header color
                "border": "none",
                "margin": "10px auto",
                "display": "block",
                "padding": "10px 20px",
                "border-radius": "5px",
            }), width={"size": 6, "offset": 3})),  # Center button
        ], style=CONTENT_STYLE)
    ])

    return content, html.H1(experiment_name), {'display': 'none'}, False, False


###-###-### GRAPHS PLOTTING ###-###-###

### Imports ###
df_665 = pd.read_csv("data/OSD-665_metadata_OSD-665-ISA/OSD-665-assays.csv")
samples_665 = pd.read_csv("data/OSD-665_metadata_OSD-665-ISA/OSD-665-samples.csv")
df_379 = pd.read_csv("data/OSD-379_metadata_OSD-379-ISA/OSD-379-assays.csv")
samples_379 = pd.read_csv("data/OSD-379_metadata_OSD-379-ISA/OSD-379-samples.csv")
###---------###

merged_df_665 = pd.merge(df_665, samples_665, on='Sample Name')
merged_df_665['Parameter Value: Body Weight upon Euthanasia'] = pd.to_numeric(
    merged_df_665['Parameter Value: Body Weight upon Euthanasia'].str.replace('gram', '').str.strip(),
    errors='coerce'
)

# Create a boxplot for 'Body Weight upon Euthanasia' by 'Spaceflight' condition
def create_body_weight_chart(merged_df):
    fig = px.box(
        merged_df,
        x='Factor Value: Spaceflight',
        y='Parameter Value: Body Weight upon Euthanasia',
        color='Factor Value: Spaceflight',  # Color by spaceflight condition
        title='Body Weight upon Euthanasia across Spaceflight Conditions',
        labels={
            'Parameter Value: Body Weight upon Euthanasia': 'Body Weight (grams)',
            'Factor Value: Spaceflight': 'Spaceflight Condition'
        },
    )
    return dcc.Graph(figure=fig)


df_665['Parameter Value: rRNA Contamination'] = df_665['Parameter Value: rRNA Contamination'].astype(str)
df_665['Parameter Value: rRNA Contamination'] = df_665['Parameter Value: rRNA Contamination'].str.replace('percent', '', regex=False).str.strip()
df_665['Parameter Value: rRNA Contamination'] = pd.to_numeric(df_665['Parameter Value: rRNA Contamination'], errors='coerce')

# Filter out any invalid or zero values
df_rrna_665 = df_665[df_665['Parameter Value: rRNA Contamination'] > 0]
merged_rna_df_665 = pd.merge(df_rrna_665, samples_665, on='Sample Name')

def create_rrna_contamination_chart_665(merged_df):
    
    fig = px.scatter(
        merged_df,
        x='Factor Value: Spaceflight',
        y='Parameter Value: rRNA Contamination',
        title='rRNA Contamination Levels across Samples',
        labels={
            'Factor Value: Spaceflight': 'Spaceflight Condition',
            'Parameter Value: rRNA Contamination': 'rRNA Contamination (%)',
        },
        size='Parameter Value: rRNA Contamination',
        color='Parameter Value: rRNA Contamination'
    )
    
    return dcc.Graph(figure=fig)

# Create a histogram for 'Habitat' by 'Spaceflight' condition
def create_habitat_chart(merged_df):
    fig = px.histogram(
        merged_df,
        x='Parameter Value: habitat',
        color='Factor Value: Spaceflight',
        title='Habitat Distribution by Spaceflight Condition',
        labels={
            'Parameter Value: habitat': 'Habitat',
            'Factor Value: Spaceflight': 'Spaceflight Condition'
        },
    )
    return dcc.Graph(figure=fig)

def create_violin(merged_df):

    fig = px.violin(
        merged_df,
        x='Factor Value: Spaceflight',
        y='Parameter Value: Body Weight upon Euthanasia',
        color='Factor Value: Spaceflight',
        box=True,
        points="all",
        title='Body Weight Distribution by Spaceflight Condition'
    )

    return dcc.Graph(figure=fig)



###-###-### OSD-379 ###-###-###
def extract_numeric_value(value):
    match = re.search(r'\d+(\.\d+)?', str(value))  # Regex to find the first number in the string
    return float(match.group()) if match else None

def create_avg_qa_score_chart(df_assays, df_samples):
    merged_df = pd.merge(df_assays, df_samples, on='Sample Name')
    
    # Clean the 'Parameter Value: QA Score' column by extracting numeric values
    merged_df['Parameter Value: QA Score'] = merged_df['Parameter Value: QA Score'].apply(extract_numeric_value)
    
    # Group by age and calculate average QA score
    avg_qa_df = merged_df.groupby('Factor Value: Age').agg(
        avg_qa=('Parameter Value: QA Score', 'mean')
    ).reset_index()
    
    fig = px.bar(
        avg_qa_df,
        x='Factor Value: Age',
        y='avg_qa',
        color='Factor Value: Age',  # Color by age groups
        title='Average RNA Integrity (QA Score) by Age Group',
        labels={
            'avg_qa': 'Average RNA Integrity Number',
            'Factor Value: Age': 'Age Group'
        },
    )
    return dcc.Graph(figure=fig)

df_379['Parameter Value: rRNA Contamination'] = df_379['Parameter Value: rRNA Contamination'].astype(str)
df_379['Parameter Value: rRNA Contamination'] = df_379['Parameter Value: rRNA Contamination'].str.replace('percent', '', regex=False).str.strip()
df_379['Parameter Value: rRNA Contamination'] = pd.to_numeric(df_379['Parameter Value: rRNA Contamination'], errors='coerce')

df_rrna_filtered = df_379[df_379['Parameter Value: rRNA Contamination'] > 0]

def create_rrna_contamination_chart(df_assays, df_samples):

    merged_df = pd.merge(df_assays, df_samples, on='Sample Name')
    
    fig = px.scatter(
        merged_df,
        x='Factor Value: Age',
        y='Parameter Value: rRNA Contamination',
        title='rRNA Contamination Levels across Samples',
        labels={
            'Factor Value: Age': 'Age of Samples',
            'Parameter Value: rRNA Contamination': 'rRNA Contamination (%)',
        },
        size='Parameter Value: rRNA Contamination',
        color='Parameter Value: rRNA Contamination'
    )
    
    return dcc.Graph(figure=fig)

def create_qa_score_by_age_chart(df_assays, df_samples):
    # Fusionner les deux dataframes sur le nom de l'échantillon
    merged_df = pd.merge(df_assays, df_samples, on='Sample Name')

    # Créer un boxplot pour comparer les scores QA par groupe d'âge
    fig = px.box(
        merged_df,
        x='Factor Value: Age',
        y='Parameter Value: QA Score',
        title='Comparing QA Scores by Age Group',
        labels={
            'Factor Value: Age': 'Age Group',
            'Parameter Value: QA Score': 'QA Score',
        },
    )
    return dcc.Graph(figure=fig)

