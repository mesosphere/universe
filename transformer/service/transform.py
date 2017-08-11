#!/usr/bin/env python3

import gen_universe
import json
import logging
import re

from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen


# TODO move somewhere or read from env variables
HOST_NAME = '0.0.0.0'
PORT_NUMBER = 7373

header_user_agent = 'User-Agent'
header_accept = 'Accept'
param_url = 'url'
url_path = '/transform'
default_charset = 'utf-8'
header_content_type = 'Content-Type'


def run_server(server_class=HTTPServer):
    """Runs a builtin python server using the given server_class.

    :param server_class: server
    :type server_class: HTTPServer
    :return: None
    """
    server_address = (HOST_NAME, PORT_NUMBER)
    httpd = server_class(server_address, Handler)
    logger.warning('Server Starts - %s:%s', HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        logger.warning('Server Stops - %s:%s', HOST_NAME, PORT_NUMBER)


class Handler(BaseHTTPRequestHandler):
    def do_GET(s):
        """
        Respond to the GET request. The expected format of this request is:
                http://<host>:<port>/transform?url=<url> along with `User-Agent`
                and `Accept` headers
        """
        if not urlparse(s.path).path == url_path:
            s.send_error(HTTPStatus.BAD_REQUEST, ErrorResponse.INVALID_PATH)
            return

        if not (header_user_agent in s.headers and header_accept in s.headers):
            s.send_error(HTTPStatus.BAD_REQUEST, ErrorResponse.INVALID_HEADERS)
            return

        query = dict(parse_qsl(urlparse(s.path).query))
        if param_url not in query:
            s.send_error(HTTPStatus.BAD_REQUEST, ErrorResponse.INVALID_PARAM)
            return

        user_agent = s.headers.get(header_user_agent)
        accept = s.headers.get(header_accept)
        decoded_url = query.get(param_url)

        try:
            json_response = handle(decoded_url, user_agent, accept)
            s.send_response(HTTPStatus.OK)
            content_header = gen_universe.format_universe_repo_content_type(
                _get_repo_version(accept))
            s.send_header(header_content_type, content_header)
            s.end_headers()
            s.wfile.write(json_response.encode())
        except Exception as e:
            s.send_error(HTTPStatus.BAD_REQUEST, str(e))


def handle(decoded_url, user_agent, accept):
    """Results in either an error or the requested json data

    :param decoded_url: The url to be fetched from
    :type decoded_url: str
    :param user_agent: User-Agent header value
    :type user_agent: str
    :param accept: Accept header value
    :return Requested json data
    :rtype str (a valid json object)
    """
    repo_version = _get_repo_version(accept)
    dcos_version = _get_dcos_version(user_agent)
    logger.debug('Url %s\nAgent %s\nAccept %s\nVersion %s\nDC/OS %s',
                 decoded_url, user_agent, accept, repo_version, dcos_version)

    req = Request(decoded_url)
    req.add_header(header_user_agent, user_agent)
    req.add_header(header_accept, accept)
    res = urlopen(req)
    charset = res.info().get_param('charset') or default_charset
    packages = json.loads(res.read().decode(charset)).get('packages')
    return render_json(packages,
                       dcos_version,
                       repo_version)


def render_json(packages, dcos_version, repo_version):
    """Returns the json

    :param packages: package dictionary
    :type packages: dict
    :param dcos_version: version of dcos
    :type dcos_version: str
    :param repo_version: version of universe repo
    :type repo_version: str
    :return filtered json data based on parameters
    :rtype str
    """
    processed_packages = gen_universe.filter_and_downgrade_packages_by_version(
        packages,
        dcos_version
    )
    updated_json_data = json.dumps({'packages': processed_packages})
    errors = gen_universe.validate_repo_with_schema(
        json.loads(updated_json_data),
        repo_version
    )
    if len(errors) != 0:
        logger.error(errors)
        raise ValueError(ErrorResponse.VALIDATION_ERROR)
    return updated_json_data


def _get_repo_version(accept_header):
    """Returns the version of the universe repo parsed.
    # TODO May be support versions of two digits ?
    :param accept_header: String
    :return repo version as str or Error
    :rtype str
    """
    result = re.findall(r'\bversion=v\d', accept_header)
    if result is None or len(result) is 0:
        raise ValueError(ErrorResponse.UNABLE_PARSE)
    result.sort(reverse=True)
    return result[0].split('=')[1]


def _get_dcos_version(user_agent_header):
    """Parses the version of dcos from the specified header.

    :param user_agent_header: String
    :return dcos version as str or Error
    :rtype str
    """
    result = re.search(r'\bdcos\/\b\d\.\d{1,2}', user_agent_header)
    if result is None:
        raise ValueError(ErrorResponse.UNABLE_PARSE)
    return result.group().split('/')[1]


class ErrorResponse:
    INVALID_PATH = 'URL Path is invalid'
    INVALID_HEADERS = 'Headers are invalid'
    INVALID_PARAM = 'Request parameters are invalid'
    UNABLE_PARSE = 'Unable to parse headers'
    VALIDATION_ERROR = 'Repo version and validation error mismatch'


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(message)s')
    run_server()
