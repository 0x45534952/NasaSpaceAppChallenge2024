import pickle
import uuid

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import Dash, Input, Output, State, callback, page_container, _dash_renderer
_dash_renderer._set_react_version("18.2.0")
from flask import request

import utils
from constants import redis_instance

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_scripts=["https://cdn.plot.ly/plotly-latest.min.js"],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="AI Data Insights",
    use_pages=True,
)


server = app.server


def layout():
    return dmc.MantineProvider(
        [
            utils.jumbotron(),
            page_container,
        ],
    )


app.layout = layout()


@callback(
    Output("save-clip", "content"),
    Input("save-clip", "n_clicks"),
    State("current-charts", "children"),
    prevent_initial_call=True,
)
def copy_link_to_view(n, current):
    figure_id = str(uuid.uuid4())
    redis_instance.set(figure_id, pickle.dumps(current))
    return request.host_url[:-1] + app.get_relative_path(f"/view?layout={figure_id}")


if __name__ == "__main__":
    app.run(debug=True)