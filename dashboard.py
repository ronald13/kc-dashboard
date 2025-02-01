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

nickname_mapping = {
    "Колобок": "kolobok",
    "Зверюга": "zweruga",
    "GOJO": "Gojo",
    "Ирландец": "Irlandman",
    "Блудница": "Bludnica",
    "KED": "Ked",
    "Бывшая": "Byvshaja",
    "Дантист": "Dantist",
    "Плесень": "Plesen",
    "Лупа": "lupa",
    "Ад": "Ad"
}
# Список игроков
# players = [
#     {"name": "Колобок", "nickname": "Колобок", "image": "assets/foto/kolobok.jpg"},
#     {"name": "Зверюга", "nickname": "Зверюга", "image": "/assets/foto/zweruga.jpg"},
#     {"name": "GOJO", "nickname": "GOJO", "image": "assets/foto/Gojo.jpg"},
#     {"name": "Ирландец", "nickname": "Ирландец", "image": "assets/foto/Irlandman.jpg"},
#     {"name": "Блудница", "nickname": "Блудница", "image": "assets/foto/Bludnica.jpg"},
#     {"name": "KED", "nickname": "KED", "image": "assets/foto/Ked.jpg"},
#     {"name": "Бывшая", "nickname": "Бывшая", "image": "assets/foto/Byvshaja.jpg"},
#     {"name": "Дантист", "nickname": "Дантист", "image": "assets/foto/Dantist.jpg"},
#     {"name": "Плесень", "nickname": "Плесень", "image": "assets/foto/Plesen.jpg"},
#     {"name": "Лупа", "nickname": "Лупа", "image": "assets/foto/lupa.jpg"},
# ]

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

df_sum = df_games.groupby(['series_id', 'player_id'], as_index=False)['total_score'].sum()

# 2. Присваиваем место в серии (ранг) только уникальным игрокам
df_sum['place_in_series'] = df_sum.groupby('series_id')['total_score'].rank(ascending=False, method='min').astype(int)

# 3. Объединяем обратно с исходным df по 'series_id' и 'player_id'
df1 = df_games.merge(df_sum[['series_id', 'player_id', 'place_in_series']], on=['series_id', 'player_id'], how='left')

top_players = top_players.merge(df1[['game_date', 'series_id', 'player_name', 'place_in_series']], on=['game_date', 'player_name'], how='left').drop_duplicates()



# generate players list with top10
players = [
    {"name": nick, "nickname": nick, "image": f"assets/foto/{nickname_mapping[nick]}.jpg"}
    for i, nick in enumerate(top10_players)
]

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
                                              'font-family': 'Roboto', 'text-transform': 'uppercase'}),

        html.P('#кc2024 #брест #сезон3 #топ10',
               style={'width': '350px', 'font-size': '14px',
                      'margin-top':'-5px', 'font-weight':'bold', 'color':'#757575'},
               className='header__text'),
    ],  className='app__header'),


    html.Div([
            # Header с изображениями игроков
            html.Div('Кликни на изображение', style={'textAlign': 'center', 'color':'#bfc0c3'}),

            # Контейнер для списка игроков с горизонтальным скроллом
            html.Div([
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
                        html.Div(player["nickname"], style={"textAlign": "left", "marginTop": "8px", 'fontWeight':500, 'text-transform':'uppercase'}),

                    ], style={'display':'flex', 'flex-direction':'column', 'align-items':'center', 'justify-center':'center'}, width=1

                    ) for i, player in enumerate(players)
                ],
                    className="players_list", style={'flex-wrap': 'nowrap', 'min-width': '1200px', 'padding': '0 15px'}
                ),
            ], style={'overflow-x': 'auto', 'margin': '0 10px'}),


            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div(" i ",
                                id="timeline-info-icon",
                                style={
                                    "fontSize": "16px",
                                    "cursor": "pointer",
                                    "width": "25px",
                                    "height": "25px",
                                    "border-radius": "50%",
                                    "background": "#fff",
                                    "border": "2px solid #6b7280",
                                    "display": "flex",
                                    "color": "#6b7280",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                }
                            ),
                            dbc.Tooltip(
                                [
                                    html.P("График показывает все серии каждого игрока ТОП10", className="mb-2 ", style={'font-weight': 'bold', 'text-align':'left'} ),
                                    html.Div([
                                        html.Div([
                                            html.Div(className="tooltip_rect_color", style={'background':'#f99746'}),
                                            html.P('Выиграл серию')
                                        ], className="tooltip_row"),

                                        html.Div([
                                            html.Div(className="tooltip_rect_color",  style={'background':'#f24236'}),
                                            html.P('Остальные серии выбранного игрока',  style={'text-align':'left'})
                                        ], className="tooltip_row"),
                                        html.Div([
                                            html.Div(className="tooltip_rect_color", style={'background': '#e5e7eb'}),
                                            html.P('Серии других игроков')
                                        ], className="tooltip_row"),

                                    ], className="mb-0 pl-3")
                                ],
                                target="timeline-info-icon",
                                placement="right",
                                delay=1000,
                                className="tooltip-timeline",

                            )
                        ], style={"display": "flex", "alignItems": "center"}),
                        dcc.Graph(id="tournament-timeline",  config={'displayModeBar': False}, style={'min-width': '1200px'})
                    ],style={'display':'flex'}, width=10)
                ], className="timeline_list"),
            ], style={'overflow-x': 'auto',  'margin-bottom':'40px'}),
            html.Div('Скроль вправо', className="only_mobile",
                     style={'textAlign': 'center', 'font-size': '10px', 'color': '#bfc0c3', 'margin-bottom':'15px', 'margin-top': '-25px'}),




            dbc.Row([

                    dbc.Col([
                    # Первая колонка с ИГРЫ, ВИНТРЕЙТ и ФАКТЫ
                        html.Div([
                            html.Div([
                                html.Div('Cыграно игр', className="tile__title"),
                                html.Div(id="total_games", className="tile__value"),
                                html.Div(id="cart_distibution", className="")
                            ], style={}, className="app__tile mb-3"),

                            html.Div([
                                dbc.Row([
                                    dbc.Col([
                                        html.Div('Винрейт', className="tile__title"),
                                        html.Div(id="total_winrate", className="tile__value"),
                                    ], xs=8, className="d-flex flex-column justify-content-center"),
                                    dbc.Col([
                                        html.Div(id="winrate_distibution", className="h-100 d-flex align-items-center"),
                                    ], xs=4, className="ps-0"),
                                ], className="flex-nowrap"),
                                html.Div(id="winrate_chart")
                            ], className="app__tile mb-3"),

                            html.Div([
                                html.Div('Дополнительные факты:', className="tile__title"),
                                html.Div(' - Шериф умирал в первую ночь 33 раза из 205', className="tile__title"),
                            ], className="app__tile mb-3"),

                        ], className="h-100"),
                    ],  xs=12, md=4, className="mb-3"),

                    dbc.Col([
                        html.Div([
                            html.Div(id="player-content", className="text-center my-4 fs-4"),
                            html.Div([
                                dcc.Checklist(
                                    id='metric-selector',
                                    options=[
                                        {'label': 'WinRate', 'value': 'win_rate'},
                                        {'label': 'Отстрелы', 'value': 'shots'}
                                    ],
                                    value=['win_rate'],
                                    inline=True,
                                    style={'color': '#000', 'text-align': 'left'},
                                    className='checklist mb-2',
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
                                    className='role-checklist mb-3',
                                ),

                                dcc.Graph(id='circular-layout', config={'displayModeBar': False}),

                            ], className="text-center w-100"),
                        ], className="app__tile h-100"),
                    ], xs=12, md=4, className="mb-3"),

                    dbc.Col([
                        html.Div([
                            html.Div(id='killed_row'),
                            html.Div([
                                html.Div('Убит в первую ночь', className="tile__title"),
                                html.Div(id="total_firstshot", className="tile__value"),
                                html.Div([
                                    dcc.Graph(id="shooting_target", config={'displayModeBar': False}),
                                ], className="text-center w-100", style={'position': 'absolute', 'top': 20, 'right': 0}),
                            ], className="app__tile", style={'position':'relative', 'height':280}),
                        ], className="h-100"),
                    ], xs=12, md=4),
            #
                ], className="g-3")


    ], className='app__content'),

    # FOOTER INFO
    html.Div([
        html.Div([
                html.Div([
                    html.Img(src='assets/img/logo.png', style={'width': '80px'}),
                    html.P('2024 ШIFFER Inc©. Информация носит ознакомительный характер.', style={'font-size':'15px', 'margin':'0 10px'}),
                ], style={'margin-top': '10px', 'display': 'flex', 'flex-direction': 'row', 'align-items': 'flex-start', 'font-size': '15px' }, className='footer'),
                html.Div([
                    html.P('Data Source:'),
                    html.A("ShifferData", href='https://app.shiffer.info/#/turnirlist?type=15', target="_blank",
                           className='link')
                ], className='data_links',  style={'text-align': 'center'}),

                html.Div([
                    html.P('Created by: '),
                    html.P('Luterino', style={'fontWeight': 'bold'}),

                ], className='data_links', style={'text-align': 'center'} )
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

    number_series_win = 0
    avg_db_value = 0

    if selected_player:
        selected_df = df_games[df_games['player_name'].isin([selected_player])]
        shots_list = df_firstshots[df_firstshots['player_name'] == selected_player]['maf_in_best'].to_list()
        win_series = number_win_series(df_games)
        number_series_win  = win_series[win_series['player_name'] == selected_player]['count'].values[0] if selected_player in win_series['player_name'].to_list() else 0
        avg_db_value = (selected_df['only_dops'].mean() * 10).round(2)

    else:
        selected_df = df_games.copy()
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
            html.Div(firstshots_miss_value, className="tile__value", style={'margin-top': 10}),
        ], className="app__tile"),
    ], style={'gap': 10, 'margin': "0 0 10px 0"}),

    killed_row_player = dbc.Row([
        dbc.Col([
            html.Div('Выиграно серий', className="tile__title", style={'white-space': 'nowrap'}),
            html.Div(number_series_win, className="tile__value", style={'margin-top': 10}),
        ], className="app__tile"),
        dbc.Col([
            html.Div('Средний ДБ', className="tile__title"),
            html.Div(avg_db_value, className="tile__value"),
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
             killed_row_general if not selected_player else killed_row_player
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