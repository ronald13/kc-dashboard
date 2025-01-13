import os
import pandas as pd
import numpy as np
import dash
from dash import Dash, dcc, html, Input, Output, callback_context,State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
# from prep import create_tornado, simple_bar, stacked_bar, simple_pie, draw_pie, make_spider, text_fig, create_box_bars, create_heatmap
from styling import template, marker_color, marker_color_full, color_list
from solver import Mafia, merge_two_dicts
from prep import create_timeline, get_full_data, winrate_chart, create_cart_distibution, get_role, \
    create_shooting_target, create_box_bars
from loguru import logger
import json



pd.options.mode.chained_assignment = None  # default='warn'

here = os.path.abspath(os.path.dirname(__file__))
prefix = os.environ.get("DASH_PREFIX", "/")

color_schemes = ['rgb(243,243,243)', 'rgb(206,217,216)', 'rgb(152,171,184)', 'rgb(125,148,163)', 'rgb(93,114,125)',
              'rgb(67,84,92)']


# Список игроков
players = [
    {"name": "Колобок", "nickname": "Колобок", "image": "assets/foto/kolobok.jpg"},
    {"name": "Зверюга", "nickname": "Зверюга", "image": "/assets/foto/zweruga.jpg"},
    {"name": "GOJO", "nickname": "GOJO", "image": "assets/foto/Gojo.jpg"},
    {"name": "Ирландец", "nickname": "Ирландец", "image": "assets/foto/Irlandman.jpg"},
    {"name": "Блудница", "nickname": "Блудница", "image": "assets/foto/Bludnica.jpg"},
    {"name": "KED", "nickname": "KED", "image": "assets/foto/Ked.jpg"},
    {"name": "Бывшая", "nickname": "Бывшая", "image": "assets/foto/Byvshaja.jpg"},
    {"name": "Дантист", "nickname": "Дантист", "image": "assets/foto/Dantist.jpg"},
    {"name": "Плесень", "nickname": "Плесень", "image": "assets/foto/Plesen.jpg"},
    {"name": "Ад", "nickname": "Ад", "image": "assets/foto/Ad.jpg"},
]

tournament_data = pd.DataFrame({
    "Date": pd.date_range(start="2023-01-01", end="2023-09-30", freq="7D"),
    "Player": ["Player 1"] * 39
})

# =====================================================================
#                               READ DATA
# =====================================================================

with open('data/tstata_kc.json') as f:
    kc_data=json.load(f)

df_games = get_full_data(kc_data)

points = df_games[['game_id', 'game_date', 'player_name']]
points.drop_duplicates(subset=['game_date', 'player_name'], inplace=True)

top10_players = df_games.groupby('player_name')['total_score'].sum().reset_index().sort_values('total_score', ascending=False).head(10)['player_name'].to_list()


top_players = df_games[df_games['player_name'].isin(top10_players)]
top_players = top_players.groupby(['game_date', 'player_name']).agg(total_score=('total_score', 'sum'),
                                                                        game_count=(
                                                                        'game_id', 'nunique'), ).reset_index()

# FirstShot Data
df_firstshots = pd.json_normalize(
        [game['gamefirstshot'] for game in kc_data if 'gamefirstshot' in game]
    )
df_firstshots.dropna(inplace=True)
df_firstshots.rename(columns={'score': 'score_firstshot'}, inplace=True)

df_firstshots = df_firstshots.merge(df_games[['game_id', 'player_id', 'player_name', 'role_id', 'who_win', 'best_roles', 'maf_in_best']],
                                    on=['game_id', 'player_id'], how='left')





# =====================================================================
#                               GENERATE FIGURES
# =====================================================================

# figures for first screen
fig_timeline_preview = create_timeline(top_players, selected_player=None)



# =====================================================================
#                               STYLES
# =====================================================================

default_style = {
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
                dbc.Col([
                    html.Div([
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

                    ],
                        id=f"player-box-{i}",
                        style={
                            "display": "flex",
                            "justifyContent": "center",
                            "alignItems": "center",
                            "flexDirection": "column",
                            "width": "100px",
                            "height": "120px",
                            "borderRadius": "50%",
                            "overflow": "hidden",
                            "backgroundColor": "#f8f9fa",
                            "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
                        }
                    ),
                    html.Div(player["nickname"], style={"textAlign": "center", "marginTop": "8px"})

                ], width=1

                ) for i, player in enumerate(players)
            ],
            className="justify-content-center"
        ),

            # Текст, который изменяется при клике


            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="tournament-timeline",  config={'displayModeBar': False})
                ], width=10)
            ], style={'justify-content': 'center', 'margin-bottom':30}),


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
                        #
                        ], className="app__tile"),


                    ], width=4
                    ),
                    dbc.Col([
                        html.Div(id="player-content", className="text-center my-4", style={"fontSize": "24px"}),
                    ], style={},  width=4, className="app__tile"),
            #
                    dbc.Col([
                        html.Div([
                            html.Div('Количество промахов в первую ночь', className="tile__title"),
                            html.Div(id="firstshots_miss", className="tile__value"),
            #                 html.Div('Распределение отстрелов по боксам', className="tile__title"),
            #                 dcc.Graph(id="firstshots_distribution", config={'displayModeBar': False}, style={'height':150, 'maxWidth':'100%'}),
                        ], style={'marginBottom': 10}, className="app__tile"),
                        html.Div([
                            html.Div('Убит в первую ночь', className="tile__title"),
                            html.Div(id="total_firstshot", className="tile__value"),
            #                 dcc.Graph(id="shooting_target", config={'displayModeBar': False}),
                        ], className="app__tile"),
                    ], width=4),
            #
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



# Callback для изменения текста и подсветки выбранного игрока
outputs = [
    Output("player-content", "children"),
    Output("tournament-timeline", "figure")
    # Output("role-pie-chart", "figure")
] + [Output(f"player-box-{i}", "style") for i in range(len(players))]

@app.callback(
    # [Output("total_games", "children"),
    # Output("total_winrate", "children")]+
    outputs,
    [Input(f"player-{i}", "n_clicks") for i in range(len(players))],
    [State("player-content", "children")]
)
def update_dashboard(*args):
    ctx = dash.callback_context

    selected_style = default_style.copy()
    selected_style["border"] = "4px solid #f24236"

    if not ctx.triggered:
        return [None, fig_timeline_preview, *([default_style] * len(players)), ]
    else:
        clicked_id = ctx.triggered[0]["prop_id"].split(".")[0]
        player_index = int(clicked_id.split("-")[-1])
        selected_player = players[player_index]['name']



        # Сброс при повторном нажатии
        current_selection = args[-1]

        if current_selection == selected_player:
            return [None, fig_timeline_preview, *([default_style] * len(players))]

        selected_games = df_games[df_games['player_name'].isin([selected_player])]

        fig_timeline = create_timeline(top_players, selected_player=selected_player)




        styles = [selected_style if i == player_index else default_style for i in range(len(players))]
        return [selected_player, fig_timeline, *styles]

# @app.callback(
#     [
#         Output("total_games", "children"),
#         Output("total_winrate", "children"),
#         Output("firstshots_miss", "children"),
#         Output("total_firstshot", "children"),
#         Output("winrate_chart", "children"),
#         Output("cart_distibution", "children"),
#         Output("shooting_target", "figure"),
#         Output("firstshots_distribution", "figure"),
#
#     ],
#     [Input(f"player-{i}", "n_clicks") for i in range(len(players))]
# )
# def update_tile_info(*args):
#     ctx = dash.callback_context
#     fig_winrate = winrate_chart(70)
#
#     # Shooting Chart  + Data
#     shots = [0, 1, 2, 3, 1, 2, 0, 3, 2, 1]
#     shots_list = df_firstshots['maf_in_best'].to_list()
#     fig_target = create_shooting_target(shots_list)
#
#
#     # Shooting Miss
#     firstshots_miss_value = df_games.shape[0] /10 - df_firstshots.shape[0]
#     print(firstshots_miss_value)
#     firstshot_by_box = df_firstshots.groupby('boxNumber')['id'].count().reset_index().rename(columns={'id': 'count'})
#     firstshots_distribution =  create_box_bars(firstshot_by_box['count'] , param="#295883")
#
#
#     # Преобразуем строку в DataFrame и конвертируем count в int
#     df = pd.read_csv('drawn_сards.csv', index_col=0)
#     df['count'] = df['count'].astype(int)
#
#     cart_distibution = create_cart_distibution(df)
#     if not ctx.triggered:
#         return (html.Div(df_games.shape[0]/10),
#                 html.Div('60%'),
#                 html.Div(firstshots_miss_value),
#                 html.Div(df_firstshots.shape[0]), # убито в первую ночь
#                 fig_winrate,
#                 cart_distibution,
#                 fig_target,
#                 firstshots_distribution)
#     else:
#         clicked_id = ctx.triggered[0]["prop_id"].split(".")[0]
#         player_index = int(clicked_id.split("-")[-1])
#         selected_player = players[player_index]['name']
#         # print('selected_player', selected_player)
#
#     selected_games = df_games[df_games['player_name'].isin([selected_player])]
#     drawn_сards = selected_games['role_id'].value_counts().reset_index().merge(get_role(), on='role_id', how='left', )
#     cart_distibution = create_cart_distibution(drawn_сards)
#
#     winrate = selected_games['score'].value_counts(normalize=True).reset_index()
#
#     winrate_value = (winrate[winrate['score'] == 1]['proportion'].values[0] * 100).astype(int)
#     fig_winrate = winrate_chart(winrate_value)
#     # fig_target = create_shooting_target(shots)
#
#     shots_list = df_firstshots[df_firstshots['player_name'] == selected_player]['maf_in_best'].to_list()
#     fig_target = create_shooting_target(shots_list)
#
#
#     return  (html.Div(selected_games.shape[0]),
#             html.Div(f"{winrate_value}%"),
#              html.Div(firstshots_miss_value),
#              html.Div(df_firstshots[df_firstshots['player_name'] == selected_player].shape[0]),  # убит в первую ночь
#              fig_winrate, cart_distibution, fig_target,
#              go.Figure())



@app.callback(
    Output("total_games", "children"),
    Output("total_winrate", "children"),
    Output("winrate_chart", "children"),
    Output("cart_distibution", "children"),
    Output("firstshots_miss", "children"),
    Output("total_firstshot", "children"),

    Input('player-content', 'children')
)
def update_players_dashboard(selected_player):

    if selected_player:
        selected_df = df_games[df_games['player_name'].isin([selected_player])]

    else:
        selected_df = df_games



    winrate_df = selected_df['score'].value_counts(normalize=True).reset_index()
    winrate_value = (winrate_df[winrate_df['score'] == 1]['proportion'].values[0] * 100).astype(int)
    fig_winrate = winrate_chart(winrate_value)


    drawn_cards = (selected_df['role_id'].value_counts(normalize=True) * 100).round(0).astype(int).reset_index().rename(columns={'proportion': 'count'})
    drawn_cards = drawn_cards.merge(get_role(), on='role_id', how='left')
    cart_distibution = create_cart_distibution(drawn_cards)


    firstshots_miss_value = df_games.shape[0] / 10 - df_firstshots.shape[0]



    return ( html.Div(selected_df['game_id'].nunique()),
             html.Div(f"{winrate_value}%"),
             fig_winrate,
             cart_distibution,
             html.Div(firstshots_miss_value),
             html.Div(df_firstshots[df_firstshots['player_name'] == selected_player].shape[0])
            )









    # don't run when imported, only when standalone
if __name__ == '__main__':
    port = os.getenv("DASH_PORT", 8054)
    app.run_server(debug=True, port=port, host="0.0.0.0")