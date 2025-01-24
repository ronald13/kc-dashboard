import os
import pandas as pd
import dash
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from prep import create_timeline, get_full_data, winrate_chart, create_cart_distibution, get_role, \
    create_shooting_target, create_circular_layout, create_winrate_distibution, number_win_series
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

df_games, df_firstshots = get_full_data(kc_data)

points = df_games[['game_id', 'game_date', 'player_name']]
points.drop_duplicates(subset=['game_date', 'player_name'], inplace=True)

top10_players = df_games.groupby('player_name')['total_score'].sum().reset_index().sort_values('total_score', ascending=False).head(10)['player_name'].to_list()
top_players = df_games[df_games['player_name'].isin(top10_players)]
top_players = top_players.groupby(['game_date', 'player_name']).agg(total_score=('total_score', 'sum'),
                                                                        game_count=(
                                                                        'game_id', 'nunique'), ).reset_index()

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
                                              'margin': '0 0 0 0', 'text-transform': 'uppercase'}),

        html.P('#кc2024 #брест #сезон3 #топ10',
               style={'width': '350px', 'font-size': '14px',
                      'margin-top':'-5px', 'font-weight':'bold', 'color':'#757575'},
               className='header__text'),
    ],  className='app__header'),

    html.Div([
            # Header с изображениями игроков
            html.Div('Кликни на изображение чтобы получить дополнительную аналитику', style={'textAlign': 'center', 'color':'#bfc0c3'}),
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
                    html.Div(player["nickname"], style={"textAlign": "left", "marginTop": "8px"})

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
                            dbc.Row([
                               dbc.Col([
                                   html.Div('Винрейт', className="tile__title"),
                                   html.Div(id="total_winrate", className="tile__value"),
                               ],md=8),
                               dbc.Col([
                                    html.Div(id="winrate_distibution", className=""),
                               ], style={'margin-top':5})
                            ]),

                            html.Div(id="winrate_chart")
                        #
                        ], style={'marginBottom':10}, className="app__tile"),
                        html.Div([
                            html.Div('Дополнительные факты:', className="tile__title"),
                            html.Div(' - Шериф умирал в первую ночь 33 раза из 205', className="tile__title"),
                        ], style={'marginBottom':10}, className="app__tile"),


                    ], width=4
                    ),
                    dbc.Col([
                        html.Div(id="player-content", className="text-center my-4", style={"fontSize": "24px"}),
                        html.Div([
                                dcc.Checklist(
                                    id='metric-selector',
                                    options=[
                                        {'label': 'WinRate', 'value': 'win_rate'},
                                        {'label': 'Отстрелы', 'value': 'shots'}
                                    ],
                                    value=[],
                                    inline=True,
                                    style={'color': '#000', 'text-align': 'left', 'margin-bottom':10},
                                    className='checklist',
                                ),
                                dcc.Checklist(
                                    id='role-selector',
                                    options=[
                                        {'label': 'Мирный', 'value': 1},
                                        {'label': 'Мафия', 'value': 2},
                                        {'label': 'Шериф', 'value': 4},
                                        {'label': 'Дон', 'value': 3}
                                    ],
                                    value=[],
                                    inline=True,
                                    style={'color': '#000', 'text-align': 'left'},
                                    className='role-checklist',
                                ),

                                dcc.Graph(id='circular-layout', config={'displayModeBar': False}),

                            ], style={'width': '100%', 'textAlign': 'center'}),

                    ], style={},  width=4, className="app__tile"),
            #
                    dbc.Col([
                        html.Div(id='killed_row'),

                        html.Div([
                            html.Div('Убит в первую ночь', className="tile__title"),
                            html.Div(id="total_firstshot", className="tile__value"),
                            html.Div([
                                dcc.Graph(id="shooting_target", config={'displayModeBar': False}),
                            ], style={'textAlign': 'center', 'width':'100%'}),

                        ], className="app__tile"),
                    ], width=4),
            #
                ], style={'display':'flex', 'gap':0},  className="")


    ], className='app__content'),

    # FOOTER INFO
    html.Div([
        html.Div([
                html.Div([
                    html.Img(src='assets/img/logo.png', style={'width': '80px'}),
                    html.P('2024 ШIFFER Inc©. Информация носит ознакомительный характер.', style={'font-size':'15px', 'margin':'0 10px'}),
                ], style={'margin-top': '10px', 'display': 'flex', 'flex-direction': 'row', 'align-items': 'center', 'font-size': '15px' }, className='footer'),
                html.Div([
                    html.P('Data Source:'),
                    html.A("ShifferData", href='https://app.shiffer.info/#/turnirlist?type=15', target="_blank",
                           className='link')
                ], style={'text-align': 'center'}),

                html.Div([
                    html.P('Created by: '),
                    html.P('Luterino', style={'fontWeight': 'bold'}),

                ], style={'text-align': 'center'} )
            ], className='vrectangle')
    ], className='app__footer'),

], style={'display': 'flex'}, className='app__wrapper _container')



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
    Output("winrate_distibution", "children"),

    Output("total_firstshot", "children"),
    Output("shooting_target", "figure"),
    # Output("firstshots_distribution", "figure"),
    # Output("most_killed", "children"),
    # Output("less_killed", "children"),
    Output("killed_row", "children"),

    Input('player-content', 'children')
)
def update_players_dashboard(selected_player):

    if selected_player:
        selected_df = df_games[df_games['player_name'].isin([selected_player])]
        shots_list = df_firstshots[df_firstshots['player_name'] == selected_player]['maf_in_best'].to_list()


    else:
        selected_df = df_games
        shots_list = df_firstshots['maf_in_best'].to_list()

    winrate_df = selected_df['score'].value_counts(normalize=True).reset_index()
    winrate_value = (winrate_df[winrate_df['score'] == 1]['proportion'].values[0] * 100).round(0).astype(int)

    fig_winrate = winrate_chart(winrate_value)
    winrate_by_cart = (selected_df.groupby('role_id')['win_condition'].value_counts(normalize=True) * 100).round(2).reset_index()
    winrate_by_cart=winrate_by_cart.loc[winrate_by_cart['win_condition'] == 1].merge(get_role(), on='role_id', how='left')


    drawn_cards = (selected_df['role_id'].value_counts(normalize=True) * 100).round(0).astype(int).reset_index().rename(columns={'proportion': 'count'})
    drawn_cards = drawn_cards.merge(get_role(), on='role_id', how='left')
    cart_distibution = create_cart_distibution(drawn_cards)

    winrate_distibution = create_winrate_distibution(winrate_by_cart)


    firstshots_miss_value = df_games.shape[0] / 10 - df_firstshots.dropna(subset=['player_id', 'player_name']).shape[0]


    fig_target = create_shooting_target(shots_list)

    most_killed = df_firstshots.groupby('player_name')['game_id'].count().reset_index().sort_values('game_id', ascending=False).head(1)['player_name'].values[0]
    less_killed = df_firstshots[df_firstshots['player_name'].isin(top10_players)].groupby('player_name')['game_id'].count().reset_index().sort_values('game_id', ascending=True).head(1)['player_name'].values[0]

    win_series = number_win_series(selected_df)

    killed_row_general = dbc.Row([
        dbc.Col([
            html.Div('Самый стреляемый', className="tile__title", style={'white-space': 'nowrap'}),
            html.Div(most_killed, className="tile__value", style={'font-size': 24, 'margin-top': 10}),
        ], className="app__tile"),
        dbc.Col([
            html.Div('Самый нестреляемый', className="tile__title", style={'white-space': 'nowrap'}),
            html.Div(less_killed, className="tile__value", style={'font-size': 24, 'margin-top': 10}),
        ], className="app__tile"),
        dbc.Col([
            html.Div('Промахов', className="tile__title"),
            html.Div(firstshots_miss_value, className="tile__value"),
        ], className="app__tile"),
    ], style={'gap': 10, 'margin': "0 0 10px 0"}),

    killed_row_player = dbc.Row([
        dbc.Col([
            html.Div('Выиграно серий', className="tile__title", style={'white-space': 'nowrap'}),
            html.Div(win_series['count'].values[0], className="tile__value", style={'font-size': 24, 'margin-top': 10}),
        ], className="app__tile"),
    ], style={'gap': 10, 'margin': "0 0 10px 0"})

    return ( html.Div(selected_df['game_id'].nunique()),
             html.Div(f"{winrate_value}%"),
             fig_winrate,
             cart_distibution,
             winrate_distibution if selected_player else html.Div(),
             # html.Div(firstshots_miss_value),
             html.Div(df_firstshots[df_firstshots['player_name'] == selected_player].shape[0]),
             fig_target,
             # firstshots_distribution,
             # html.Div(most_killed),
             killed_row_player if selected_player else killed_row_general,
            )

@app.callback(
    Output('circular-layout', 'figure'),
    Input('metric-selector', 'value'),
    Input('role-selector', 'value'),
    Input('player-content', 'children')

)
def update_figure(selected_metrics, selected_role, selected_player):

    def update_role_values(value):
        all_values = [1, 2, 3, 4]
        if not value:  # Если ничего не выбрано
            return all_values
        elif set(value) == set(all_values):  # Если выбраны все опции
            return all_values
        return value
    selected_roles = update_role_values(selected_role)
    if selected_player:
        df_active = df_games[df_games['player_name'].isin([selected_player]) & (df_games['role_id'].isin(selected_roles))]
        df_firstshots_active = df_firstshots[df_firstshots['player_name'].isin([selected_player]) & (df_firstshots['role_id'].isin(selected_roles))]
    else:
        df_active = df_games[df_games['role_id'].isin(selected_roles)]
        df_firstshots_active = df_firstshots[df_firstshots['role_id'].isin(selected_roles)]

    # create the DataFrame with only boxNumber columns to avoid missing boxes
    result_df = pd.DataFrame({'boxNumber':range(1,11)})

    # if selected_role

    total_winrate_by_box = df_active.groupby('boxNumber').agg(
        total_games=('who_win', 'count'),
        total_wins=('win_condition', 'sum')
    ).reset_index()

    total_winrate_by_box['win_rate'] = (
                (total_winrate_by_box['total_wins'] / total_winrate_by_box['total_games']) * 100).round(1)


    total_shots_by_box = df_firstshots_active.groupby('boxNumber')['game_id'].size().reset_index(name='shots')
    result_df = result_df.merge(total_winrate_by_box, on='boxNumber', how='left').merge(total_shots_by_box, on='boxNumber', how='left').fillna(0)

    total_circular = total_winrate_by_box.merge(total_shots_by_box, how='left', on='boxNumber')
    total_circular.rename(columns={'game_id': 'shots', 'total_winrate':'win_rate'}, inplace=True)
    result_df['win_rate_num'] = result_df['win_rate']




    return create_circular_layout(result_df, selected_metrics)





    # don't run when imported, only when standalone
if __name__ == '__main__':
    port = os.getenv("DASH_PORT", 8054)
    app.run_server(debug=True, port=port, host="0.0.0.0")