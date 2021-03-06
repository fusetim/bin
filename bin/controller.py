import bottle as bt
from pathlib import Path
from bin import root, config
from bin.models import Snippet
from bin.utils import parse_language, parse_extension


@bt.route('/', method='GET')
def get_new_form():
    return bt.template('newform.html')


@bt.route('/assets/<filepath:path>')
def assets(filepath):
    return bt.static_file(filepath, root=root.joinpath('assets'))


@bt.route('/new', method='POST')
def post_new():
    content_length = bt.request.get_header('Content-Length')
    if content_length is None:
        raise bt.HTTPError(411, "Content-Length required")
    if int(content_length) > config.SNIPPET_MAX_SIZE:
        raise bt.HTTPError(413, f"Payload too large, we accept maximum {config.SNIPPET_MAX_SIZE} bytes")

    code = None
    if bt.request.files:
        part = next(bt.request.files.values())
        ext = parse_extension(Path(part.filename).suffix[1:])
        code = part.file.read(config.SNIPPET_MAX_SIZE)
    elif bt.request.forms:
        ext = parse_extension(bt.request.forms.get('lang'))
        code = bt.request.forms.get('code', '').encode('latin-1')
    if not code:
        raise bt.HTTPError(417, "Missing code")

    snippet = Snippet.create(code.decode('utf-8'))
    bt.redirect(f'/{snippet.id}.{ext}')


@bt.route('/<snippet_id>', method='GET')
@bt.route('/<snippet_id>.<ext>', method='GET')
def get_html(snippet_id, ext=None):
    try:
        snippet = Snippet.get_by_id(snippet_id)
    except KeyError:
        raise bt.HTTPError(404, "Snippet not found")
    language = parse_language(ext)
    return bt.template('highlight', code=snippet.code, language=language)


@bt.route('/raw/<snippet_id>', method='GET')
@bt.route('/raw/<snippet_id>.<ext>', method='GET')
def get_raw(snippet_id, ext=None):
    try:
        snippet = Snippet.get_by_id(snippet_id)
    except KeyError:
        raise bt.HTTPError(404, "Snippet not found")
    return snippet.code
