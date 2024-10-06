import random

import dash_chart_editor as dce
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import ollama
import pandas as pd
from dash import Input, Output, State, callback, dcc, html, no_update, register_page
from urllib.parse import parse_qs
import utils
import json
import logging
import os

logging.basicConfig(level=logging.INFO)
from constants import ollama_model

JSON_FILE_PATH = os.getenv('DATA_JSON_PATH', 'data/data.json')  # Use environment variable for the JSON file path

utils.data.update(pd.read_csv("/home/theo/NASA/NasaSpaceAppChallenge2024/data/OSD-665_metadata_OSD-665-ISA/OSD-665-assays.csv"))

df = utils.data.df

register_page(__name__, path="/ai")

loading_overlay = dmc.LoadingOverlay(
    id="loading-overlay",
    visible=False,
    overlayProps={"radius": "sm", "blur": 2},
    zIndex=10,
)

code, default_code, part1, part2 = utils.most_interesting_plot(df)

try:
    exec("layout = " + part1 + code + part2)
except Exception as e:
    exec("layout = " + part1 + default_code + part2) 

@callback(
    Output("chat-output", "children", True),
    Output("question", "value", True),
    Output("loading-overlay", "visible", True),
    Input("chat-submit", "n_clicks"),
    State("question", "value"),
    State("chat-output", "children"),
    prevent_initial_call=True,
    )
def chat_window(n_clicks, question, cur):
    if not question:
        return no_update, no_update, False

    data = utils.data.df.to_dict("list")
    print(data)

    df = pd.DataFrame(data)
    prompt = utils.generate_prompt(df, question)

    try:
        completion = ollama.chat(
            model=ollama_model, messages=[{"role": "user", "content": prompt}]
        )
        answer = completion["message"]["content"]
    except Exception as e:
        answer = f"Error: {str(e)}"

    question_markdown = dcc.Markdown(question, className="chat-item question")
    answer_markdown = dcc.Markdown(answer, className="chat-item answer")

    new_content = [question_markdown, answer_markdown]


    return (new_content + cur if cur else new_content), "", False


@callback(
    Output("chart-editor", "saveState", True),
    Input("add-to-layout", "n_clicks"),
    prevent_initial_call=True,
)
def save_figure_to_chart_editor(n):
    if n:
        return True


@callback(
    Output("current-charts", "children", True),
    Input("chart-editor", "figure"),
    State("chart-editor", "dataSources"),
    State("current-charts", "children"),
    prevent_initial_call=True,
)
def save_figure(figure, data, cur):
    # cleaning data output for unnecessary columns
    figure = dce.cleanDataFromFigure(
        figure,
    )
    df = pd.DataFrame(data)
    # create Figure object from dash-chart-editor figure
    figure = dce.chartToPython(figure, df)

    # Validate there's something to save
    if figure.data:
        item = [dmc.Paper([dcc.Graph(figure=figure)])]

        header = [
            html.Div(
                [
                    html.H2("Saved figures"),
                    dcc.Clipboard(
                        id="save-clip",
                        title="Copy link",
                        style={"margin-left": "10px"},
                    ),
                ],
                style={"display": "flex"},
            )
        ]
        return cur + item if cur else header + item

    return no_update

@callback(
    Output("csv-path", "children", True),
    Input("url", "search"),
    prevent_initial_call=True,
)
def update_csv_file(search):
    params = parse_qs(search.lstrip("?"))
    experiment_id = params.get("experiment_id", [None])[0]
    try:
        with open(JSON_FILE_PATH) as json_file:
            data = json.load(json_file)
            logging.info(f"Succesfully loaded {JSON_FILE_PATH}")
    except Exception as e:
        logging.error(f"Error loading {JSON_FILE_PATH}: {str(e)}")
        return no_update
    for exp in data:
        if exp.get("value") == experiment_id:
            return exp.get("csv_path")
    return 
