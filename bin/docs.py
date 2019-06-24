#! /usr/bin/python
"""
Automatically generates a nice, formatted version of swagger.json into the docs folder
"""

import json


def generate_example_data(key: str, values: dict, depth: int):
    if 'readOnly' in values:
        if values['readOnly']:
            return 'N/A'

    if 'format' in values:
        if values['format'] == 'uuid':
            return '"b3589eeb-0f87-4e99-b942-aa9534911a10"'

    if '$ref' in values:
        return get_definition(values['$ref'], depth + 1)

    if key == 'id':
        return '"b3589eeb-0f87-4e99-b942-aa9534911a10"'
    if key == 'name':
        return '"Lemonworld"'
    if key == 'first_name':
        return '"John"'
    if key == 'last_name':
        return '"Smith"'
    if key == 'email':
        return '"john.smith@mail.com"'
    if key == 'address_line_1':
        return '"22 Holly Mount"'
    if key == 'address_line_2':
        return '""'
    if key == 'city':
        return '"NW3 6SG"'
    if key == 'postcode':
        return '"London"'
    if key == 'region':
        return '"Greater London"'
    if key == 'country':
        return '"United Kingdom"'

    return '"' + key + '"'


def convert_responses_to_html(value):
    html = ''
    for request, value in value.items():
        description = value.get('description')
        if not description:
            description = 'A description hasn\'t been provided for this yet'
        html += f"""
            <p>{request}</p>
            <p class="description">{description}</p>
        """
    return html


def convert_parameters_to_html(parameters):
    if not parameters:
        return ''

    for item in parameters:
        schema = item['schema']['$ref']
        return create_code_block(get_definition(schema))


def create_code_block(code, header='Example'):
    code_block_html = """
        <div class="code">
        <p class='code-header'>Example</p>
        """

    code_block_html += code

    code_block_html += """
        </div>
        """

    return code_block_html


def get_definition(def_name, depth=1):
    definition = definitions[def_name[def_name.rindex('/') + 1:]]

    definitions_html = '{<br>'
    i = 0

    for key, potato in definition['properties'].copy().items():
        if 'readOnly' in potato:
            if potato['readOnly']:
                del (definition['properties'][key])

    for key, potato in definition['properties'].items():
        i = i + 1
        comma = ','
        if i == len(definition['properties'].items()):
            comma = ''

        definitions_html += ('&nbsp;' * 4 * depth) + '<span class="highlight highlight-' + str(depth) + '">"' + key + '"</span>: ' + generate_example_data(key, potato, depth) + comma + '<br> '

    return definitions_html + ('&nbsp;' * 4 * (depth - 1)) + '}'


def convert_request_to_html(value):
    html = ''
    for request, value in value.items():
        if request == 'parameters':
            continue
        # try:
        #    description = value.get('description', 'A description hasn\'t been provided for this yet')
        #    if not description:
        #        description = 'A description hasn\'t been provided for this yet'

        # responses = convert_responses_to_html(value.get('responses'))
        # except:
        #    print('oh no')
        parameters = convert_parameters_to_html(value.get('parameters'))

        html += f"""
            <div class="request">
                <h4>{request}</h4>
                <p class="description">{description}</p>
                {parameters}
            </div>
        """
    return html


with open('../docs/swagger.json') as json_file:
    data = json.load(json_file)

    # Initial Info
    info = data['info']
    page_title = info['title'] + ' Documentation'
    description = info['description']
    terms_of_service = info['termsOfService']
    version = info['version']

    # Paths
    paths = data['paths']
    paths_html = ''

    definitions = data['definitions']

    for path, value in paths.items():
        paths_html += f"""
            <div class="path">
                <h3>{path}</h3>
                {
        convert_request_to_html(value)
        }
            </div>
            """

style = """
<style media="screen">
    :root {
        --background-color: rgb(255, 255, 255);
        --foreground-color: rgb(20, 20, 20);
        --accent-color: #0b0c0c;
        --code-background-color: rgb(240, 240, 240);
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: rgb(20, 20, 30);
            --foreground-color: rgb(250, 250, 255);
            --accent-color: #0b0c0c;
            --code-background-color: rgb(40, 40, 50);
        }
    }
    body {
        background-color: var(--background-color);
    }
    .code {
        font-family: Menlo, monospaced;
        background: var(--code-background-color);
        font-weight: normal;
        padding: 20px;
        font-size 0.8rem;
    }
    .code-header {
        font-size: 0.6rem;
        letter-spacing: 0.4px;
        margin-bottom: 20px;
        text-transform: uppercase;
        font-weight: 700;
        opacity: 0.4;
    }
    .highlight {
        color: rgb(10, 132, 255);
        font-family: Menlo, monospaced;
        font-size 0.8rem;
        font-weight: normal;
    }
    .highlight-2 {
        color: rgb(255, 55, 95);
    }
    .highlight-4 {
        color: rgb(191, 90, 242);
    }
    .highlight-3 {
        color: rgb(255, 204, 0);
    }
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
        -webkit-tap-highlight-color: transparent;
        -ms-overflow-style: -ms-autohiding-scrollbar;
        -webkit-overflow-scrolling: touch;
        -webkit-appearance: none;
        -webkit-font-smoothing: antialiased;
        color: var(--foreground-color);
        margin-bottom: 20px;
        font-size: 19px;
        line-height: 1.2;
        font-weight: 600;
    }
    h1 {
        font-weight: 800;
        font-size: 2rem;
        max-width: 400px;
    }
    h2 {
        font-weight: 700;
        font-size: 1.5rem;
    }
    h3 {
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 30px;
    }
    h4 {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .description {
        opacity: .7;
        margin-bottom: 30px;
    }
    a {
        color: #005ea5;
    }
    .request {
    
    }
    header {
        width: 100vw;
        height: 55px;
        background-color: #0b0c0c;
        margin: 0;
    }
    .container {
        max-width: 900px;
        margin: auto;
        padding: 50px 0;
    }
    .path {
        margin-bottom: 60px;
    }
    #filter-box {
        display: block;
        width: 100%;
        margin: 40px 0;
        outline: 0;
        border: 0;
        padding: 0;
        font-size: 1.2rem;
        background-color: transparent;
        text-indent: 0px;
    }
    ::placeholder {
        color: var(--foreground-color);
        opacity: .5;
    }
    input[type="search"] {
        -webkit-appearance: textfield;
    }
    input[type="search"]::-webkit-search-decoration {
        -webkit-appearance: none;
    }
</style>
"""

html = f"""
<html>
    <head>
        <title>{page_title}</title>
    </head>
    {style}
    <body>
        <div class="container">
            <h1>{page_title}</h1>
            <p class='description'>{description}</p>
            <!--<a href="{terms_of_service}" style="display: block;">Terms of service</a>
            <p>{version}</p>-->

            <!--<input type="search" name="search" class="govuk-input" name="filter-box" id="filter-box" placeholder="Filter..." autofocus autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">-->

            <br>
            <br>

            {paths_html}
        </div>
    </body>
</html>
"""

# Save file
file = open("../docs/index2.html", "w")
file.write(html)
file.close()
