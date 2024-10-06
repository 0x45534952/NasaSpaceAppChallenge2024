import dash_bootstrap_components as dbc
from dash import dcc, html, register_page, Input, Output, callback, State
import urllib.parse
import json

# Load json data from data folder (data.json)
experiments = json.load(open("data/data.json"))

# Register the page
register_page(__name__, path="/")

# Prepare dropdown options from experiments data
experiment_options = [{"label": exp, "value": experiments[exp]["value"]} for exp in experiments]

# Define the layout with production-ready design for web and mobile
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                # Header with clean typography and responsive font size
                html.H1("Nasa Space App Challenge 2024", 
                        className="text-center mb-3", 
                        style={"font-weight": "bold", 
                               "font-size": "calc(1.5rem + 1vw)",  # Responsive font size
                               "color": "#2c3e50"}),

                # Subheader with responsive font and subtle color
                html.P("A Minimalist App for Scientists", 
                       className="text-center mb-4", 
                       style={"font-size": "calc(0.75rem + 0.5vw)",  # Responsive font size
                              "color": "#7f8c8d"}),

                # Dropdown for selecting experiments, responsive width
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Select an Experiment", 
                                  html_for='experiment-dropdown', 
                                  style={"font-weight": "bold", 
                                         "color": "#34495e"}),
                        dcc.Dropdown(
                            id='experiment-dropdown',
                            options=experiment_options,
                            placeholder="Choose an experiment",
                            style={"border": "1px solid #bdc3c7", 
                                   "border-radius": "5px", 
                                   "font-size": "16px"}  # Ensure legibility
                        )
                    ], xs=12, sm=10, md=8, lg=6, xl=6, className="mx-auto")  # Responsive centering
                ], className="mb-4"),

                # Button for navigation, centered and responsive size
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Go to Summary", 
                                   id='summary-btn', 
                                   style={"background-color": "#0B3D91",  # Custom color
                                          "border-color": "#0B3D91",    # Ensure border matches
                                          "color": "#fff",              # White text
                                          "width": "100%", 
                                          "font-size": "18px", 
                                          "padding": "10px"})
                    ], xs=12, sm=8, md=6, lg=4, xl=4, className="mx-auto")  # Center the button
                ], className="mb-4"),

                # Hidden div to trigger page navigation
                dcc.Location(id='url', refresh=True)
            ], width=12)
        ])
    ], fluid=True, style={"max-width": "100%", "padding": "30px 15px"})  # Responsive padding for mobile
])

# Callback for button click and navigation
@callback(
    Output('url', 'href'),
    Input('summary-btn', 'n_clicks'),
    State('experiment-dropdown', 'value')
)
def navigate_to_summary(n_clicks, experiment_name):
    if n_clicks > 0 and experiment_name:  # Ensure the button is clicked and experiment is selected
        # Create the URL for redirection, encoding the experiment name as a query parameter
        return f"/summary?id={urllib.parse.quote(experiment_name)}"
    return None
