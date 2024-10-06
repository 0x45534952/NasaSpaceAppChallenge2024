import base64
import io

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
import plotly.express as px
import random
from urllib.parse import parse_qs
import ollama
from constants import ollama_model
import os
JSON_FILE_PATH = os.getenv('DATA_JSON_PATH', 'data/data.json')  # Use environment variable for the JSON file path
import json
import logging

logging.basicConfig(level=logging.INFO)
class Data:
    def __init__(self):
        self.df = pd.read_csv("data/default.csv")
        self.DEFAULT_CSV_PATH = "data/default.csv"

    def update(self, df):
        self.df = df
data = Data()

def chat_container(text, type_):
    return html.Div(text, id="chat-item", className=type_)


def jumbotron():
    return html.Div(
        dbc.Container(
            [
                html.H2("NASA OSD Data visualisation", className="display-4"),
                # dcc.Markdown(
                #     "This application uses [Dash Chart Editor](https://github.com/BSd3v/dash-chart-editor)"
                #     " as an interface to explore a dataset and Llama 3.2 to interact in real-time with "
                #     "a dataset by asking questions about its contents.",
                #     className="lead",
                # ),
                # html.Hr(className="my-2"),
                # html.P(
                #     "Start using the application by interacting with the sample dataset, or upload your own."
                # ),
                # html.P(
                #     [
                #         dbc.Button(
                #             "Learn more",
                #             style={"background-color": "#238BE6"},
                #             href="https://plotly.com/examples/generative-ai-chatgpt/",
                #         ),
                #         dbc.Button(
                #             "Upload your own CSV",
                #             id="modal-demo-button",
                #             style={
                #                 "background-color": "#238BE6",
                #                 "margin-left": "10px",
                #             },
                #         ),
                #     ],
                #     className="lead",
                #     style={"display": "flex"},
                # ),
            ],
            fluid=True,
            className="py-3",
        ),
        className="p-3 bg-light rounded-3",
    )

def upload_modal():
    return html.Div(
        [
            dmc.Modal(
                title="Upload Modal",
                id="upload-modal",
                size="lg",
                zIndex=10000,
                children=[
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(
                            ["Drag and Drop or ", html.A("Select Files")]
                        ),
                        style={
                            "width": "100%",
                            "height": "60px",
                            "lineHeight": "60px",
                            "borderWidth": "1px",
                            "borderStyle": "dashed",
                            "borderRadius": "5px",
                            "textAlign": "center",
                            "margin": "10px",
                            "font-family": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial,"
                            " sans-serif, Apple Color Emoji, Segoe UI Emoji",
                        },
                        # Allow multiple files to be uploaded
                        multiple=False,
                    ),
                    dmc.Space(h=20),
                    html.Div(id="summary"),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Close",
                                color="red",
                                variant="outline",
                                id="modal-close-button",
                            ),
                        ],
                        # position="right",
                    ),
                ],
            ),
        ]
    )


def generate_prompt(df, question):
    # Generate insights
    insights = []

    # Basic DataFrame Information
    insights.append(
        f"The DataFrame contains {len(df)} rows and {len(df.columns)} columns."
    )
    insights.append("Here are the first 5 rows of the DataFrame:\n")
    insights.append(df.head().to_string(index=False))

    # Summary Statistics
    insights.append("\nSummary Statistics:")
    insights.append(df.describe().to_string())

    # Column Information
    insights.append("\nColumn Information:")
    for col in df.columns:
        insights.append(f"- Column '{col}' has {df[col].nunique()} unique values.")

    # Missing Values
    missing_values = df.isnull().sum()
    insights.append("\nMissing Values:")
    for col, count in missing_values.items():
        if count > 0:
            insights.append(f"- Column '{col}' has {count} missing values.")

    # Most Common Values in Categorical Columns
    categorical_columns = df.select_dtypes(include=["object"]).columns
    for col in categorical_columns:
        top_value = df[col].mode().iloc[0]
        insights.append(f"\nMost common value in '{col}' column: {top_value}")

    insights_text = "\n".join(insights)

    # Compliment and Prompt
    prompt = (
        "You are a data analyst and chart design expert helping users build charts and answer "
        "questions about arbitrary datasets. The user's question will be provided. Ensure you "
        "answer the user's question accurately and given the context of the dataset. The user "
        "will use the results of your commentary to work on a chart or to research the data "
        "using Dash Chart Editor, a product built by Plotly. If the user's question doesn't "
        " make sense, feel free to make a witty remark about Plotly and Dash. Your response "
        "should use Markdown markup. Limit your response to only 1-3 sentences. Address the "
        "user directly as they can see your response."
    )

    prompt = f"{prompt}\n\nContext:\n\n{insights_text}\n\nUser's Question: {question}"

    return prompt


@callback(
    Output("chart-editor", "dataSources", True),
    Output("summary", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def update_output(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    data.update(df)

    preview = html.Div(
        [
            html.H5(filename),
            dag.AgGrid(
                rowData=df.to_dict("records"),
                columnDefs=[{"field": i} for i in df.columns],
                defaultColDef={"sortable": True, "resizable": True, "editable": True},
            ),
        ]
    )


    return df.to_dict("list"), preview


@callback(
    Output("upload-modal", "opened"),
    Input("modal-demo-button", "n_clicks"),
    Input("modal-close-button", "n_clicks"),
    State("upload-modal", "opened"),
    prevent_initial_call=True,
)
def modal_demo(nc1, nc2, opened):
    return not opened

@callback(Output("chat-submit", "disabled"), Input("question", "value"))

def disable_submit(question):
    return not bool(question)

def most_interesting_plot(df):
    # Generate insights
    insights = []

    # Basic DataFrame Information
    insights.append(
        f"The DataFrame contains {len(df)} rows and {len(df.columns)} columns."
    )
    insights.append("Here are the first 5 rows of the DataFrame:\n")
    insights.append(df.head().to_string(index=False))

    # Summary Statistics
    insights.append("\nSummary Statistics:")
    insights.append(df.describe().to_string())

    # Column Information
    insights.append("\nColumn Information:")
    for col in df.columns:
        insights.append(f"- Column '{col}' has {df[col].nunique()} unique values.")

    # Missing Values
    missing_values = df.isnull().sum()
    insights.append("\nMissing Values:")
    for col, count in missing_values.items():
        if count > 0:
            insights.append(f"- Column '{col}' has {count} missing values.")

    # Most Common Values in Categorical Columns
    categorical_columns = df.select_dtypes(include=["object"]).columns
    for col in categorical_columns:
        top_value = df[col].mode().iloc[0]
        insights.append(f"\nMost common value in '{col}' column: {top_value}")

    insights_text = "\n".join(insights)

    # Compliment and Prompt
    prompt = (
        "You are a data analyst and chart design expert helping users build charts and answer "
        "questions about arbitrary datasets. You are using Dash Chart Editor, a product built "
        "by Plotly. Your task is to create the best possible plot using the provided insights "
        "and the actual data from the dataset. Ensure that the plot is meaningful and accurately "
        "represents the data. Be sure to include the data and labels. "
        "Your response should ONLY include the Dash layout of the plot, "
        "not in a variable. Do not put it in a code block nor Markdown. Only answer "
        "'html.Div(id='generated-plot', [...])'. Keep it simple and concise."
        "Here is an example of a Dash layout:\n\n"
        """
        html.Div(id='generated-plot', children=[
            dcc.Graph(
                figure={
                    'data': [
                        {'x': df['column1'], 'y': df['column2'], 'type': 'bar',
                        'name': 'Example Bar Plot'},
                        {'x': df['column3'], 'y': df['column4'], 'type': 'line',
                        'name': 'Example Line Plot'}
                    ],
                    'layout': {
                        'title': {'text': 'Example Plot Title'},
                        'xaxis': {'title': {'text': 'X Axis Title'}, 'type': 'category'},
                        'yaxis': {'title': {'text': 'Y Axis Title'}, 'type': 'linear'},
                        'legend': {'orientation': 'h'}
                    }
                }
            )
        ])
        """
    )

    prompt = f"{prompt}\n\nContext:\n\n{insights_text}"

    response = ollama.chat(
        model=ollama_model, messages=[{"role": "user", "content": prompt}]
    )

    code = response["message"]["content"]

    # print(code)

    part1 = """dmc.MantineProvider(
    [
        html.P(
            [
                dbc.Button(
                    "Upload your own CSV",
                    id="modal-demo-button",
                    style={
                        "background-color": "#238BE6",
                        "margin-left": "10px",
                    },
                ),
            ],
            className="lead",
            style={"display": "flex"},
        ),
        dmc.Paper(
            ["""
    part2 = """,
                html.Div(
                    [
                        dcc.Location(id="url", refresh=False),
                        html.P("Ask about the dataset...", className="lead"),
                        dmc.Textarea(
                            placeholder=random.choice(
                                [
                                    '"Are there any outliers in this dataset?"',
                                    '"What trends do you see in this dataset?"',
                                    '"Anything stand out about this dataset?"',
                                    '"Do you recommend specific charts given this dataset?"',
                                    '"What columns should I investigate further?"',
                                ]
                            ),
                            autosize=True,
                            minRows=2,
                            id="question",
                        ),
                        dmc.Group(
                            [
                                dmc.Button(
                                    "Submit",
                                    id="chat-submit",
                                    disabled=True,
                                ),
                            ],
                            # position="right",
                        ),
                        html.Div(
                        [
                            loading_overlay,
                            html.Div(
                                id="chat-output",
                            ),
                        ],
                        ),
                    ],
                    id="chat-container",
                ),
            ],
            shadow="xs",
            id="flex",
        ),
        utils.upload_modal(),
        html.Div(id="current-charts"),
    ],
    id="padded",
)"""


    
    default_code = """html.Div(
                    [
                        dce.DashChartEditor(
                            id="chart-editor",
                            dataSources=df.to_dict("list"),
                        ),
                        dmc.Affix(
                            dmc.Button("Save this chart", id="add-to-layout"),
                            position={"bottom": 20, "left": 20},
                        ),
                    ],
                )"""
    
    return code, default_code, part1, part2


###         create_body_weight_chart(merged_df_665),
###        create_rrna_contamination_chart_665(merged_rna_df_665),
###        create_habitat_chart(merged_df_665),


df_665 = pd.read_csv("data/OSD-665_metadata_OSD-665-ISA/OSD-665-assays.csv")
samples_665 = pd.read_csv("data/OSD-665_metadata_OSD-665-ISA/OSD-665-samples.csv")

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


df_665['Parameter Value: rRNA Contamination'] = str(df_665['Parameter Value: rRNA Contamination']).replace('percent', '').strip()

# Convert the remaining numeric part to float
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