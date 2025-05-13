import dash
from dash import dcc, html, Dash, Input, Output, State
import pandas as pd
import plotly.graph_objs as go

# Завантаження даних
file_path = 'D:/DA-main/vhi/df_all.csv'  # Вказуємо шлях до файлу з даними
df = pd.read_csv(file_path)

# Створення додатку Dash
app = Dash(__name__)
app.title = "Аналіз VCI, TCI, VHI"

# Список областей (унікальний набір)
oblast_list = sorted(df['oblast'].unique())

# Опис інтерфейсу
app.layout = html.Div([
    html.Div([
        # Dropdown для вибору VCI, TCI, VHI
        html.Label("Обрати часовий ряд:"),
        dcc.Dropdown(
            id='time-series-dropdown',
            options=[
                {'label': 'VCI', 'value': 'VCI'},
                {'label': 'TCI', 'value': 'TCI'},
                {'label': 'VHI', 'value': 'VHI'}
            ],
            value='VHI',  # Початкове значення
            clearable=False
        ),

        # Dropdown для вибору області
        html.Label("Обрати область:"),
        dcc.Dropdown(
            id='region-dropdown',
            options=[{'label': f"Область {oblast}", 'value': oblast} for oblast in oblast_list],
            value=oblast_list[0],  # Початкова область
            clearable=False
        ),

        # Слайдер для вибору діапазону тижнів
        html.Label("Вибрати діапазон тижнів:"),
        dcc.RangeSlider(
            id='week-slider',
            min=df['Week'].min(),
            max=df['Week'].max(),
            step=1,
            value=[df['Week'].min(), df['Week'].max()],
            marks={i: f"{i}" for i in range(df['Week'].min(), df['Week'].max() + 1, 10)}
        ),

        # Слайдер для вибору діапазону років
        html.Label("Вибрати діапазон років:"),
        dcc.RangeSlider(
            id='year-slider',
            min=df['Year'].min(),
            max=df['Year'].max(),
            step=1,
            value=[df['Year'].min(), df['Year'].max()],
            marks={i: f"{i}" for i in range(df['Year'].min(), df['Year'].max() + 1, 5)}
        ),

        # Кнопка для скидання фільтрів
        html.Button("Скинути фільтри", id="reset-button", n_clicks=0),

        # Чекбокси для сортування
        html.Label("Сортування:"),
        dcc.Checklist(
            id='sort-checklist',
            options=[
                {'label': 'За зростанням', 'value': 'asc'},
                {'label': 'За спаданням', 'value': 'desc'}
            ],
            value=[],  # Без вибору спочатку
            inline=True
        ),

    ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),

    html.Div([
        # Вкладки для таблиці та графіків
        dcc.Tabs(id='tabs', value='table-tab', children=[
            dcc.Tab(label='Таблиця', value='table-tab'),
            dcc.Tab(label='Графік часових рядів', value='time-series-tab'),
            dcc.Tab(label='Порівняльний графік', value='comparison-plot-tab'),
        ]),

        html.Div(id='tabs-content')
    ], style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'})
])


# Callback для обробки скидання та оновлення фільтрів
@app.callback(
    [Output('time-series-dropdown', 'value'),
     Output('region-dropdown', 'value'),
     Output('week-slider', 'value'),
     Output('year-slider', 'value'),
     Output('sort-checklist', 'value')],
    Input('reset-button', 'n_clicks'),
    prevent_initial_call='initial_duplicate'
)
def reset_filters(n_clicks):
    return 'VHI', oblast_list[0], [df['Week'].min(), df['Week'].max()], [df['Year'].min(), df['Year'].max()], []


# Callback для оновлення контенту вкладок
@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs', 'value'),
     Input('time-series-dropdown', 'value'),
     Input('region-dropdown', 'value'),
     Input('week-slider', 'value'),
     Input('year-slider', 'value'),
     Input('sort-checklist', 'value')]
)
def update_content(selected_tab, selected_series, selected_region, week_range, year_range, sort_order):
    filtered_df = df[
        (df['oblast'] == selected_region) &
        (df['Week'] >= week_range[0]) & (df['Week'] <= week_range[1]) &
        (df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])
    ]

    # Сортування якщо визначено
    if 'asc' in sort_order and 'desc' in sort_order:
        return html.Div("Помилка: Не можна одночасно обрати сортування за зростанням та спаданням.")
    elif 'asc' in sort_order:
        filtered_df = filtered_df.sort_values(by=selected_series, ascending=True)
    elif 'desc' in sort_order:
        filtered_df = filtered_df.sort_values(by=selected_series, ascending=False)

    if selected_tab == 'table-tab':
        return html.Div([
            html.H4("Таблиця відфільтрованих даних"),
            html.Div(dcc.Graph(
                figure={
                    'data': [go.Table(
                        header=dict(values=list(filtered_df.columns),
                                    fill_color='paleturquoise',
                                    align='left'),
                        cells=dict(values=[filtered_df[col] for col in filtered_df.columns],
                                   fill_color='lavender',
                                   align='left')
                    )]
                }
            ))
        ])
    elif selected_tab == 'time-series-tab':
        return html.Div([
            html.H4("Часовий ряд"),
            dcc.Graph(
                figure=go.Figure(
                    data=[
                        go.Scatter(
                            x=filtered_df['Year'] + (filtered_df['Week'] / 52),  # Рік + тиждень у дробовій частині
                            y=filtered_df[selected_series],
                            mode='lines',
                            name=f"{selected_series} для області {selected_region}"
                        )
                    ],
                    layout=go.Layout(
                        title=f"Часовий ряд {selected_series}",
                        xaxis=dict(title='Рік'),
                        yaxis=dict(title=selected_series)
                    )
                )
            )
        ])
    elif selected_tab == 'comparison-plot-tab':
        comparison_df = df[
            (df['Week'] >= week_range[0]) & (df['Week'] <= week_range[1]) &
            (df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])
        ]
        return html.Div([
            html.H4("Порівняльний графік"),
            dcc.Graph(
                figure=go.Figure(
                    data=[
                        go.Box(
                            y=comparison_df[comparison_df['oblast'] == region][selected_series],
                            name=f"Область {region}"
                        ) for region in comparison_df['oblast'].unique()
                    ],
                    layout=go.Layout(
                        title=f"Порівняльний графік {selected_series}",
                        xaxis=dict(title='Область'),
                        yaxis=dict(title=selected_series)
                    )
                )
            )
        ])


# Запуск застосунку
if __name__ == '__main__':
    app.run_server(debug=True)
