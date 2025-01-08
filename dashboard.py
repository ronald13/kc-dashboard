import os
import pandas as pd
import numpy as np
import dash
from dash import Dash, dcc, html, Input, Output, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
# from prep import create_tornado, simple_bar, stacked_bar, simple_pie, draw_pie, make_spider, text_fig, create_box_bars, create_heatmap
from styling import template, marker_color, marker_color_full, color_list
from solver import Mafia, merge_two_dicts
from prep import create_timeline, get_full_data, winrate_chart, create_cart_distibution, get_role
from loguru import logger
import json



pd.options.mode.chained_assignment = None  # default='warn'

here = os.path.abspath(os.path.dirname(__file__))
prefix = os.environ.get("DASH_PREFIX", "/")

color_schemes = ['rgb(243,243,243)', 'rgb(206,217,216)', 'rgb(152,171,184)', 'rgb(125,148,163)', 'rgb(93,114,125)',
              'rgb(67,84,92)']


# Список игроков
players = [
    {"name": "Колобок", "image": "assets/foto/kolobok.jpg"},
    {"name": "Зверюга", "image": "/assets/foto/zweruga.jpg"},
    {"name": "GOJO", "image": "assets/foto/Gojo.jpg"},
    {"name": "Ирландец", "image": "assets/foto/Irlandman.jpg"},
    {"name": "Блудница", "image": "assets/foto/Bludnica.jpg"},
    {"name": "KED", "image": "assets/foto/Ked.jpg"},
    {"name": "Бывшая", "image": "assets/foto/Byvshaja.jpg"},
    {"name": "Дантист", "image": "assets/foto/Dantist.jpg"},
    {"name": "Плесень", "image": "assets/foto/Plesen.jpg"},
    {"name": "Ад", "image": "assets/foto/Ad.jpg"},
]

with open('data/tstata_kc.json') as f:
    kc_data=json.load(f)

df_games = get_full_data(kc_data)

points = df_games[['game_id', 'game_date', 'player_name']]
points.drop_duplicates(subset=['game_date', 'player_name'], inplace=True)

top10_players = df_games.groupby('player_name')['total_score'].sum().reset_index().sort_values('total_score', ascending=False).head(10)['player_name'].to_list()
# print(top10_players)

top_players = points[points['player_name'].isin(top10_players)]


# Данные о картах
card_data = pd.DataFrame({
    "Role": ["Peaceful", "Mafia", "Sheriff", "Don"],
    "Count": [50, 30, 10, 10]
})

app = Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
    url_base_pathname=prefix,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    assets_folder=os.path.join(here, "assets")

)

app.title = "Капитанский стол | Dashboard"
server = app.server




app.layout = html.Div([


    # HEADER INFO
    html.Div([
        html.H1('Капитанский стол 3.0', style={'line-height': '1.1', 'letter-spacing': '-0.81px', 'color': '#f24236',
                                              'font-family': 'Roboto', 'font-size': '42px', 'font-weight': 'bold',
                                              'margin': '0 0 10px 0', 'text-transform': 'uppercase'}),

        html.P('#кc2024 #брест #сезон3 #топ10',
               style={'width': '350px', 'font-size': '14px',
                      'margin-bottom':0, 'font-weight':'bold', 'color':'#757575'},
               className='header__text'),
    ],  className='app__header'),

    html.Div([
            # Header с изображениями игроков
            html.Div('Кликни на изображение чтобы получить дополнительную аналитику', style={'textAlign': 'center'}),
            dbc.Row(
                [
                dbc.Col(
                    html.Div(
                        html.Img(
                            src=player["image"],
                            id=f"player-{i}",
                            style={
                                "cursor": "pointer",
                                "border": "2px solid transparent",
                                "borderRadius": "50%",
                                "width": "80px",
                                "height": "80px",
                                "objectFit": "cover"
                            }
                        ),
                        style={
                            "display": "flex",
                            "justifyContent": "center",
                            "alignItems": "center",
                            "width": "100px",
                            "height": "100px",
                            "borderRadius": "50%",
                            "overflow": "hidden",
                            "backgroundColor": "#f8f9fa",
                            "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
                        }
                    ),
                width=1
            ) for i, player in enumerate(players)
                ],
                className="justify-content-center"
            ),

            # Текст, который изменяется при клике
            html.Div(id="player-content", className="text-center my-4", style={"fontSize": "24px"}),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="tournament-timeline",  config={'displayModeBar': False})
                ], width=12)
            ]),

            dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div('Cыграно игр', className="tile__title"),
                            html.Div(id="total_games", className="tile__value"),
                            html.Div(id="cart_distibution", className="")
                        ], style={'marginBottom':10}, className="app__tile"),
                        html.Div([
                            html.Div('Винрейт', className="tile__title"),
                            html.Div(id="total_winrate", className="tile__value"),
                            html.Div(id="winrate_chart")

                        ], className="app__tile"),


                    ], width=4
                    ),
                    dbc.Col([
                        dcc.Graph(id="role-pie-chart", config={'displayModeBar': False})
                    ], style={},  width=4, className="app__tile"),

                    dbc.Col([
                        html.Div([
                            html.Div('Призовые места', className="tile__title"),
                            # html.Div(id="carts_info", className="tile__value"),
                            # html.Div(id="cart_distibution", className="")
                        ], style={'marginBottom': 10}, className="app__tile"),
                        html.Div([
                            html.Div('Отстрелы', className="tile__title"),
                            html.Div(id="total_firstshot", className="tile__value"),
                        ], className="app__tile"),
                    ], width=4),

                ], style={'dislay':'flex', 'gap':0},  className="")


    ], className='app__content'),

    # FOOTER INFO
    html.Div([
        html.Div([
                html.Div([
                    html.Img(src='assets/img/logo_white.png', style={'width': '80px'}),
                    html.P('©', style={'font-size':'15px', 'color': '#fff', 'margin':'0 10px'}),
                    html.A("Перейти на сайт", href='https://statistics.shiffer.by/#/Turnir/41', target="_blank", className='link'),
                ], style={'margin-top': '10px', 'display': 'flex', 'flex-direction': 'row', 'align-items': 'center', 'font-size': '15px', 'text-decoration': 'underline' }, className='footer')
            ], className='vrectangle')
    ], className='app__footer'),

], style={'display': 'flex'}, className='app__wrapper')



# Callback для изменения текста
@app.callback(
    [
        Output("player-content", "children"),
        Output("tournament-timeline", "figure"),
        Output("role-pie-chart", "figure")
    ],
    [Input(f"player-{i}", "n_clicks") for i in range(len(players))]
)
def update_dashboard(*args):
    # read data
    df = df_games

    top_players = df[df['player_name'].isin(top10_players)]
    top_players = top_players.groupby(['game_date', 'player_name']).agg(total_score=('total_score', 'sum'),
                                                                game_count=('game_id', 'nunique'), ).reset_index()

    ctx = dash.callback_context


    if not ctx.triggered:
        selected_player = "None"
        fig_timeline = create_timeline(top_players, selected_player=None)
    else:
        clicked_id = ctx.triggered[0]["prop_id"].split(".")[0]
        player_index = int(clicked_id.split("-")[-1])
        selected_player = players[player_index]['name']

        # top_players = top_players[top_players['player_name'].isin([selected_player])]

        fig_timeline = create_timeline(top_players, selected_player=selected_player)


    # Круговая диаграмма ролей
    fig_pie = px.pie(
        card_data,
        values="Count",
        names="Role",
        title="",
        template="plotly_white",
        hole=0.5,

    )
    fig_pie.update_layout(
        width=200
    )

    return f"You selected: {selected_player}", fig_timeline, fig_pie


@app.callback(
    [
        Output("total_games", "children"),
        Output("total_winrate", "children"),

        Output("total_firstshot", "children"),
        Output("winrate_chart", "children"),
        Output("cart_distibution", "children"),

    ],
    [Input(f"player-{i}", "n_clicks") for i in range(len(players))]
)
def update_tile_info(*args):
    ctx = dash.callback_context
    fig_winrate = winrate_chart(70)
    data = '''role_id,count,role_name,color
    1,55,Мирный,#f24236
    2,20,Мафия,#295883
    4,13,Шериф,#cbe5f3
    3,7,Дон,#efbf00'''

    # Преобразуем строку в DataFrame и конвертируем count в int
    df = pd.read_csv('drawn_сards.csv', index_col=0)
    df['count'] = df['count'].astype(int)  # Преобразуем

    cart_distibution = create_cart_distibution(df)
    if not ctx.triggered:
        return (html.Div(df_games.shape[0]/10),
                html.Div('60%'), html.Div('1'),  fig_winrate, cart_distibution)
    else:
        clicked_id = ctx.triggered[0]["prop_id"].split(".")[0]
        player_index = int(clicked_id.split("-")[-1])
        selected_player = players[player_index]['name']
        # print('selected_player', selected_player)

    selected_games = df_games[df_games['player_name'].isin([selected_player])]
    drawn_сards = selected_games['role_id'].value_counts().reset_index().merge(get_role(), on='role_id', how='left')
    cart_distibution = create_cart_distibution(drawn_сards)

    winrate = selected_games['score'].value_counts(normalize=True).reset_index()

    winrate_value = (winrate[winrate['score'] == 1]['proportion'].values[0] * 100).astype(int)
    fig_winrate = winrate_chart(winrate_value)


    return  (html.Div(selected_games.shape[0]),
            html.Div(f"{winrate_value}%"), html.Div('1'),  fig_winrate, cart_distibution)



# don't run when imported, only when standalone
if __name__ == '__main__':
    port = os.getenv("DASH_PORT", 8053)
    app.run_server(debug=True, port=port, host="0.0.0.0")