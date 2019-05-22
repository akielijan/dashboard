import base64
import re
import json
import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.development.base_component import Component

frequencies = {}
languages = ['english', 'polish', 'norwegian', 'finnish']
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
    for lang in languages:
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
    for lang in languages:
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
    for lang in languages:
        error = get_error(input_letter_frequency, frequencies[lang]['letters'])
        results.append((lang, error))
    return sorted(results, key=lambda v: v[1])


app = dash.Dash(__name__)


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
            dcc.Textarea(
                id='text-input',
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


def test_detect_lang():
    text = """
    Sylkaisi et loydetty naisilla paissani ja en kaljaasi me. Nyt vei toi vedappas kaljaasi loistoja yhteensa. Seisomaan saa uteliaina ajaisivat tuo pohjineen osa tarpeemme tyrskahti. Suomuakaan tuo kaksisataa ankkurinne kas eli oikeastaan jos. Ommella suoraan poistaa vai lie ilmalla eli aikomus. Muilla puolin kalpea han kas kutsui toi isa. Kysymyksen nykyisista pysahtyvan te kuitenkaan ja on. Tuvan loi jaa voi helga minun tuo. Oma teille matkan isa pitipa nytkin nakyja. 

Et ai eihan meren viron mikas tytto menen ai. Talla sai nyt loi lie minun hokee sehan. On taakseen loytavat rinnalla pyorahti en sinunkin ei se. Leikiksi pystyssa se se loydetty. Te ne usein puoli paiva moisi juuri ei me. Ja koettaen paattaen kuljemme en se hinnalla on kymmenta kaljaasi. Seinamalle palkkioksi ja ne he suurtakaan no. Koetakaan on jalkeensa haaveensa se paljonkos kuvitella. Puutavaraa isa han kahvipannu tee suomuakaan liikkeelle tuommoinen rikastunut. Ne herran pitipa ryssan on summan edessa ei tuohon. 

Tai ryypattiin iso loi luulikohan uteliaasti vietavaksi. Papalla potkaus ja ne sentaan minulta. He no enhan mikas jotta lisaa usvaa mutta. Han tuhansia rukoilen isa rakentaa oli. Yha ero tupa noin tai jos toru. Kuului ryskaa ne et se huulet. Tosissaan tai haaveensa hymahtaen kay voi vai. Palkkioksi toi suurtakaan luo kaljamalla tuo minullekin hiljaisuus. 

Rikastunut he patriarkat nuottikota ei. Muut no puhu se itku. Kerrallaan ansioitaan me on voitaisiin sisimpansa harrykoita te et pannaksesi. Pysahtyvan nuottikota tarkoittaa oikeastaan ai ei ai on. On ai pilkkanaan moottoriin nykyaikana lainaamaan se et. Ai poikimatta tuommoinen sisimpansa ne ai karahtanut moottoriin. Jos kesat jalat tulee tuo toi milla tahan. Elamassani muutettuna ero hartaimman tuo nykyisista pyyhkimaan purjelaiva. Suurtakaan kuitenkaan vatvotusta voitaisiin vakituiset ja et no kokonainen. Tarpeeksi kasvoilla en taallakin olevinasi se tehnytkin puuskahti. 

Kaksisataa luulikohan viinaelake naamallasi en ai. Terve antoi on ei hanhi kadet olisi huvin. Jos vai rakentaa tietysti paivassa ela vanhakin nostivat rahaakin. Maksaa ei heinia ulapan muista voinut ai joutuu. Ne kohta liene on onkin esiin. Osaat vanha missa te se he mista en. 

Satun pthyi jo muuta ai ei kesan. Kaikilla vie poydalle muutakin isa anteeksi miehensa sahvoori ota tee. Tahankin miehensa ja ai et maksavan se kummitus kuolleen. Ruumiin loi ota muutkin merille otappas. Vei iso han ryyppasin kai rahasumma kalpeista. On koetakaan loytamaan osaamatta ne oljytakki kuunnella kuvitella ei. Totisesti oli noutamaan vuoteensa kas tarpeemme millainen ainaisena. Tyttarenne jos kuolleelta kai vieraankin voitaisiin tarkoittaa kaupunkiin. Toisia en ja puista mikaan soutaa. 

Sina lapi on vaan pysy tein paha en. Se koetakaan kaksikaan ja kaantynyt. Ruuhen en toinen ai lausui. Ryyppasin pienoinen punastuen kalpeista on semmoisia me ikaankuin se. Kaupunkiin hartioilla sen ota tuo nelikoihin jai puheenaihe. Sanoo helga ai jo mikas joulu. Se pohjineen no kastettua majakoita ja jalkaansa ukkovaari menemista. Punastuen ai me no tervehtii huonoista teistakin. Hyvastinsa oli seinamalle lie voi tuommoinen. Sai vastannut vahintain nae osaamatta tuo oli. 

Heidan taalla taisin nae jos vei. Ja hinnalla ne varjossa poskille entisina ei kutukala. Nalkainen rannoille he saariston semmoinen ne. Naemme nyt oma taisin valiin. Sen ostaa voi olipa sinun vei nyt astui hahah. Juova jos osaat jai sen eri menet. Ehka vei kuka ukko lie heti sai vaan. Me kurkkuun en sylkaisi jaanytta ne luulkoon. En on sisimpansa toivottiin se minullekin hartaimman. 

Aiotte lapsia jai meille jos paitse juonut eli. On tama no ai enka meni se vesi. Pyyhkia aitinsa en anastaa te tuvasta et menevan. No tuhattakin ja miinavenhe kaljamalla vatvotusta. Tayden sen heitti joutuu sylkea eli nyt kay. Tee kuivempaan kohdallani nae jaa osa sittenkuin tarvitsisi. 

Kayda jokin me laine malja tasta se ei viela. Taallakin paljonkos ei ne mihinkaan uteliaina merirosvo et sammuttaa jo. Ensin pitaa hanet he ne uskon on se. Totisesti he me majakoita istahtaen. Toi uteliaina haaveensa varsinkin sen. Musta tai ota onkin suusi salin. Mitenka ne ymmarra viisiin nousisi he. 


    """
    print(detect_language(text))
    pass


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

    test_detect_lang()


@app.callback(Output('main-div', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)
        ]

    return create_dashboard()


def format_results(result: list):
    ol = html.Ol()
    components = []
    for i in range(min(3, len(result))):
        lang, error = result[i]
        components.append(
            html.Li("{} {}".format(str(lang).capitalize(), float(error)))
        )
    ol.children = components
    return ol


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
