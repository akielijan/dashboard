import base64
import re
import json
import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

frequencies = {}
languages = ['polish']
active_languages = ['polish']
widget_height = "300px"


def import_lang(filename) -> dict:
    with open(filename + '.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def get_difference(lang_chars: list, other_chars: list) -> list:
    chars = set(lang_chars)
    for others in other_chars:
        if others == lang_chars:
            continue
        chars = chars.difference(set(others))
    chars = list(chars)
    chars.sort()
    return chars


def get_intersection(d: list) -> list:
    result = set()
    for i in range(len(d)):
        if i == 0:
            result = set(d[0])
        else:
            result = result.intersection(set(d[i]))

    result = list(result)
    result.sort()
    return result


def get_formatted_and_filtered_values(x_values, freq_dict):
    filtered_values = []
    for val in x_values:
        filtered_values.append(freq_dict[val])
    return [v * 100 for v in filtered_values]


def get_layout(title):
    return go.Layout(
        title=go.layout.Title(
            text=title + ' frequency',
            xref='paper',
        )
    )


def init():
    for lang in languages:
        frequency = import_lang(lang)
        add_language_frequency(frequency, lang)


def add_language_frequency(frequency, lang):
    frequencies[lang] = frequency
    all_letters.append(list(frequency['letters'].keys()))
    all_digrams.append(list(frequency['digrams'].keys()))
    all_trigrams.append(list(frequency['trigrams'].keys()))


def basic_plots_data_init():
    letters_plot_data.clear()
    digrams_plot_data.clear()
    trigrams_plot_data.clear()
    for lang in active_languages:
        frequency = frequencies[lang]
        x_letters = get_intersection(all_letters)
        letters_plot_data.append(go.Scatter(
            x=x_letters,
            y=get_formatted_and_filtered_values(x_letters, frequency['letters']),
            mode='lines',
            name=lang
        )
        )
        x_digrams = get_intersection(all_digrams)
        digrams_plot_data.append(go.Scatter(
            x=x_digrams,
            y=get_formatted_and_filtered_values(x_digrams, frequency['digrams']),
            mode='lines',
            name=lang
        )
        )
        x_trigrams = get_intersection(all_trigrams)
        trigrams_plot_data.append(go.Scatter(
            x=x_trigrams,
            y=get_formatted_and_filtered_values(x_trigrams, frequency['trigrams']),
            mode='lines',
            name=lang
        )
        )


def distinct_plot_data_init():
    distinct_letters_plot_data.clear()
    for lang in active_languages:
        frequency = frequencies[lang]
        distinct_letters = get_difference(list(frequency['letters'].keys()), all_letters)

        distinct_letters_plot_data.append(go.Scatter(
            x=distinct_letters,
            y=get_formatted_and_filtered_values(distinct_letters, frequency['letters']),
            mode='markers',
            name=lang,
            marker=dict(
                size=10,
            )
        )
        )


def process_text(text: str) -> str:
    processed = text.lower()
    pattern = re.compile(r"[^a-zA-ZÀ-ž ]")
    processed = re.sub(pattern, "", processed)
    return processed


def get_letter_frequency(text: str) -> dict:
    freq = {}
    length = 0
    for letter in text:
        if letter.isspace():
            continue

        length += 1

        if letter not in freq:
            freq[letter] = 1
        else:
            freq[letter] += 1

    for key in freq:
        freq[key] /= length
    return freq


def get_digram_frequency(text: str) -> dict:
    freq = {}
    length = 0
    for i in range(len(text)-1):
        if text[i].isspace() or text[i+1].isspace():
            continue

        length += 1

        digram = text[i] + text[i+1]
        if digram not in freq:
            freq[digram] = 1
        else:
            freq[digram] += 1

    for key in freq:
        freq[key] /= length
    return freq


def get_trigram_frequency(text: str) -> dict:
    freq = {}
    length = 0
    for i in range(len(text) - 2):
        if text[i].isspace() or text[i + 1].isspace() or text[i + 2].isspace():
            continue

        length += 1
        trigram = text[i] + text[i + 1] + text[i + 2]
        if trigram not in freq:
            freq[trigram] = 1
        else:
            freq[trigram] += 1

    for key in freq:
        freq[key] /= length
    return freq


def get_error(input_freq: dict, lang_freq: dict) -> float:
    result = 0.0
    for key in input_freq:
        occurrences_in_text = input_freq[key]
        occurrences_in_lang = 0.0
        if key in lang_freq:
            occurrences_in_lang = lang_freq[key]

        result += pow(occurrences_in_lang - occurrences_in_text, 2)
    return result


def detect_language(text: str, level=1) -> list:
    text = process_text(text)
    results = []
    for lang in active_languages:
        error = 0
        if level >= 1:
            input_letter_frequency = get_letter_frequency(text)
            error += get_error(input_letter_frequency, frequencies[lang]['letters'])
        if level >= 2:
            input_digram_frequency = get_digram_frequency(text)
            error += get_error(input_digram_frequency, frequencies[lang]['digrams'])
        if level >= 3:
            input_trigram_frequency = get_trigram_frequency(text)
            error += get_error(input_trigram_frequency, frequencies[lang]['trigrams'])
        results.append((lang, error))
    return sorted(results, key=lambda v: v[1])


app = dash.Dash(__name__)


def get_available_languages():
    data = []
    for language in list(frequencies.keys()):
        data.append({"label": language, "value": language})
    return data


def digrams_contour_diagram_init(lang='polish'):
    z = []
    if lang is None or len(lang) == 0:
        if len(active_languages) > 0:
            fr = frequencies[active_languages[0]]
        else:  # dummy data
            fr = {"letters": {}, "digrams": {}, "trigrams": {}}
    else:
        fr = frequencies[lang]
    alphabet = list(fr['letters'].keys())
    alphabet.sort()
    for second_letter in alphabet:
        row = []
        for first_letter in alphabet:
            dg = first_letter + second_letter
            if dg not in fr['digrams']:
                row.append(0)
            else:
                row.append(fr['digrams'][dg])
        z.append(list(row))

    data = [
        go.Contour(
            x=alphabet,
            y=alphabet,
            z=z,
            colorscale='Jet'
        )
    ]

    return data


def update_graphs_data():
    basic_plots_data_init()
    distinct_plot_data_init()


def create_dashboard():
    update_graphs_data()
    digram_contour = digrams_contour_diagram_init(None)
    return [
        html.Div(children=[
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'upload file',
                    html.A('')
                ]),
                accept=".json",
                # Allow multiple files to be uploaded
                multiple=True
            ),
            html.Div(
                id='tools',
                children=[
                    dcc.Dropdown(
                        id='tools-languages',
                        options=get_available_languages(),
                        value=active_languages,
                        multi=True,
                        placeholder="select languages"
                    ),
                ]
            ),
            html.Div(
                id='textarea-wrapper',
                children=[
                    dcc.Textarea(
                        id='text-input',
                        placeholder="enter text to predict"
                    )
                ]
            ),
            html.Div(
                id='detection-result'
            )
        ],
            className="widget right"
        ),
        dcc.Graph(
            id='letters-graph',
            figure={
                'data': letters_plot_data,
                'layout': get_layout('common letters')
            },
            className="widget left non-transparent"
        ),
        dcc.Graph(
            id='digrams-graph',
            figure={
                'data': digrams_plot_data,
                'layout': get_layout('digrams')
            },
            className="widget left non-transparent"
        ),
        dcc.Graph(
            id='distinct-graph',
            figure={
                'data': distinct_letters_plot_data,
                'layout': get_layout('distinct letters')
            },
            className="widget right non-transparent"
        )
    ]


if __name__ == '__main__':
    all_letters = []
    all_digrams = []
    all_trigrams = []
    init()

    letters_plot_data = []
    digrams_plot_data = []
    trigrams_plot_data = []
    distinct_letters_plot_data = []

    app.layout = html.Div(
        id="main-div",
        children=create_dashboard()
    )


@app.callback(Output('tools-languages', 'options'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def add_external_language(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)
        ]

    return get_available_languages()


def update_active_languages(languages_to_activate):
    if languages_to_activate is not None and sorted(languages_to_activate) != sorted(active_languages):
        active_languages.clear()
        for language_to_activate in languages_to_activate:
            active_languages.append(language_to_activate)


@app.callback(Output('letters-graph', 'figure'),
              [Input('tools-languages', 'value')])
def update_letters_graph(languages_to_activate):
    update_active_languages(languages_to_activate)
    update_graphs_data()
    return {
        'data': letters_plot_data,
        'layout': get_layout('common letters')
    }


@app.callback(Output('distinct-graph', 'figure'),
              [Input('tools-languages', 'value')])
def update_letters_graph(languages_to_activate):
    update_active_languages(languages_to_activate)
    update_graphs_data()
    return {
        'data': distinct_letters_plot_data,
        'layout': get_layout('distinct letters')
    }

@app.callback(Output('digrams-graph', 'figure'),
              [Input('tools-languages', 'value')])
def update_letters_graph(languages_to_activate):
    update_active_languages(languages_to_activate)
    update_graphs_data()
    return {
        'data': digrams_plot_data,
        'layout': get_layout('digrams')
    }


def format_results(result: list):
    if result is not None and len(result) > 0:
        lang, error = result[0]
        # html.Li("{0} {1:.2f}".format(str(lang).capitalize(), float(error)))
        return [lang]

    return ["prediction result"]


# def format_results(result: list):
#     ol = html.Ol()
#     components = []
#     for i in range(min(3, len(result))):
#         lang, error = result[i]
#         components.append(
#             html.Li("{0} {1:.2f}".format(str(lang).capitalize(), 1-float(error)))
#         )
#     ol.children = components
#     return ol


@app.callback(Output('detection-result', 'children'),
              [Input('text-input', 'value')])
def do_language_detection(contents):
    result = []
    if contents is None or len(contents) == 0:
        pass
        # clear
    else:
        result = detect_language(contents, 3)
        print(result[0])

    return format_results(result)


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    if 'json' in filename:
        # Assume that the user uploaded a JSON file
        language = filename.split('.')[0]
        if language in languages:
            # todo: alert for user or sth
            print("Can't add existing language")
            return
        languages.append(language)
        frequency = json.loads(decoded.decode('utf-8'))
        add_language_frequency(frequency, language)


if __name__ == '__main__':
    app.run_server(debug=True)
