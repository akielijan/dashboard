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
    pattern = re.compile(r"[^a-zA-ZÀ-ž]")
    processed = re.sub(pattern, "", processed)
    return processed


def get_letter_frequency(text: str) -> dict:
    freq = {}
    for letter in text:
        if letter not in freq:
            freq[letter] = 1
        else:
            freq[letter] += 1

    text_length = len(text)
    for key in freq:
        freq[key] /= text_length
    return freq


def get_error(input_freq: dict, lang_freq: dict) -> float:
    result = 0.0
    for character in input_freq:
        occurrences_in_text = input_freq[character]
        occurrences_in_lang = 0.0
        if character in lang_freq:
            occurrences_in_lang = lang_freq[character]

        result += pow(occurrences_in_lang - occurrences_in_text, 2)
    return result


def detect_language(text: str) -> list:
    text = process_text(text)
    input_letter_frequency = get_letter_frequency(text)
    results = []
    for lang in active_languages:
        error = get_error(input_letter_frequency, frequencies[lang]['letters'])
        results.append((lang, error))
    return sorted(results, key=lambda v: v[1])


app = dash.Dash(__name__)


def get_available_languages():
    data = []
    for language in list(frequencies.keys()):
        data.append({"label": language, "value": language})
    return data


def create_dashboard():
    basic_plots_data_init()
    distinct_plot_data_init()
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
            id='super-graph',
            figure={
                'data': digrams_plot_data,
                'layout': get_layout('digrams')
            },
            className="widget right non-transparent"
        ),
        dcc.Graph(
            id='distinct-graph',
            figure={
                'data': distinct_letters_plot_data,
                'layout': get_layout('distinct letters')
            },
            className="widget left non-transparent"
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


@app.callback(Output('main-div', 'children'),
              [Input('upload-data', 'contents'),
               Input('tools-languages', 'value')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def add_external_language(list_of_contents, languages_data, list_of_names, list_of_dates):
    if list_of_contents is not None:
        [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)
        ]
    else:
        if languages_data is not None:
            active_languages.clear()
            for lang in languages_data:
                active_languages.append(lang)

    return create_dashboard()


def format_results(result: list):
    if result is not None and len(result) > 0:
        lang, error = result[0]
        # html.Li("{0} {1:.2f}".format(str(lang).capitalize(), float(error)))
        return [lang]

    return ["prediction result"]


@app.callback(Output('detection-result', 'children'),
              [Input('text-input', 'value')])
def do_language_detection(contents):
    result = []
    if contents is None or len(contents) == 0:
        pass
        # clear
    else:
        result = detect_language(contents)
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
