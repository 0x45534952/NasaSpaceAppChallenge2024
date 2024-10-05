import dash_bootstrap_components as dbc
from dash import dcc, html, register_page, Input, Output, callback
from urllib.parse import parse_qs
from prompts import NASAExperimentSummary  # Import your class

# Register the page with a specified path
register_page(__name__, path='/summary')

# Define color scheme for the dark minimalist theme
COLORS = {
    'dark_blue': '#002D62',
    'darker_grey': '#333333',
    'light_grey': '#E0E0E0',
    'off_white': '#F7F7F7'
}

# Define styles for different sections
SECTION_STYLE = {
    'padding': '40px 15px',
    'color': COLORS['dark_blue'],
    'max-width': '1200px',
    'margin': '0 auto',
    'line-height': '1.6'
}

HEADER_STYLE = {
    **SECTION_STYLE,
    'background-color': COLORS['off_white'],
    'padding-top': '60px',
    'padding-bottom': '20px',
}

# CSS for the full-screen loader
LOADER_STYLE = {
    'position': 'fixed',
    'top': '0',
    'left': '0',
    'width': '100%',
    'height': '100%',
    'display': 'flex',
    'justify-content': 'center',
    'align-items': 'center',
    'background-color': 'rgba(255, 255, 255, 0.8)',  # Semi-transparent white background
    'z-index': '9999'  # Ensure the loader is on top of everything
}

# Helper function to create a section layout
def create_section(title, content, bg_color, font_size='18px'):
    return dbc.Container([
        dbc.Row(dbc.Col(html.H2(title, className="display-5 mb-4", style={'color': COLORS['darker_grey']}), width=12)),
        dbc.Row(dbc.Col(content, width=12))
    ], fluid=True, style={'background-color': bg_color, 'padding-top': '30px'})

# Helper function to create an accordion for protocols
def create_protocol_accordion(protocols):
    return dbc.Accordion(
        children=[
            dbc.AccordionItem(
                title=protocol['name'],  # Ensure that you're using 'name' as the title
                children=html.P(protocol['description'], style={'font-size': '16px', 'color': COLORS['darker_grey']}),  # Use 'description' for the content
                style={'background-color': COLORS['light_grey'], 'border': f'1px solid {COLORS["dark_blue"]}', 'border-radius': '5px'}
            ) for protocol in protocols
        ],
        start_collapsed=True,
        flush=True,
        style={'border-radius': '10px'}
    )

# Loader spinner to display while fetching data
loader_spinner = dbc.Spinner(color="primary", size="lg")

# Layout with full-width immersive sections and loader
layout = html.Div([
    dcc.Location(id='url', refresh=False),

    # Full-screen loader while waiting for content
    html.Div(
        id='loader',
        children=loader_spinner,
        style=LOADER_STYLE  # Apply the full-screen style to the loader
    ),

    # Header section with experiment name, initially empty
    html.Div(id='experiment-name', style=HEADER_STYLE, hidden=True),  # Hidden by default

    # Placeholder for dynamically loaded content based on the URL
    html.Div(id='summary-content', hidden=True)  # Hidden by default
])

# Callback to update content dynamically based on query parameter
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
    experiment_id = params.get('id', [None])[0]  # Extract the 'id' parameter

    # If no experiment ID is provided, return an error message
    if not experiment_id:
        return (display_error_message("Experiment Not Found", "The experiment ID provided does not match any known experiments. Please check the URL and try again."),
                None, LOADER_STYLE, True, True)

    # Fetch summary using NASAExperimentSummary class
    experiment_summary = NASAExperimentSummary(experiment_id)
    summary_json = experiment_summary.prompt()

    # If fetching fails or summary_json is empty, display an error
    if summary_json is None:
        return (display_error_message("Experiment Not Found", "The experiment ID provided does not match any known experiments. Please check the URL and try again."),
                None, LOADER_STYLE, True, True)
    if not summary_json:
        return (display_error_message("Error Fetching Data", "There was an issue retrieving data for this experiment. Please try again later."),
                None, LOADER_STYLE, True, True)
    
    # Extract the experiment name for the header
    experiment_name = summary_json.get("experiment_name", "Experiment Overview")

    # Build the sections using helper functions
    content = html.Div([
        create_section("🧪 Experiment Overview", 
                       html.P(summary_json["experiment_overview"], style={'font-size': '18px', 'color': COLORS['darker_grey']}), 
                       COLORS['light_grey']),

        create_section("🎯 Mission Goals", 
                       html.Ul([html.Li(goal, style={'font-size': '18px', 'color': COLORS['darker_grey']}) for goal in summary_json['goals']]), 
                       COLORS['off_white']),

        create_section("🌍 Significance", 
                       html.P(summary_json['significance'], style={'font-size': '18px', 'color': COLORS['darker_grey']}), 
                       COLORS['light_grey']),

        create_section("📝 Protocol", 
                       create_protocol_accordion(summary_json['protocol']), 
                       COLORS['off_white'])
    ])

    # Hide loader and show the content and experiment name
    return content, html.H1(experiment_name, style={'text-align': 'center', 'color': COLORS['dark_blue']}), {'display': 'none'}, False, False

# Helper function to display error messages
def display_error_message(title, message):
    return create_section(title, html.P(message, style={'font-size': '18px', 'color': COLORS['darker_grey']}), COLORS['light_grey'])
