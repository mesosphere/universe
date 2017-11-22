#!/usr/bin/env python3

import gen_universe
import json
import logging
import os
import re

from enum import Enum
from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.error import URLError, HTTPError
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen


# Binds to all available interfaces
HOST_NAME = ''
# Gets the port number from $PORT0 environment variable
PORT_NUMBER = int(os.environ['PORT_UNIVERSECONVERTER'])
MAX_REPO_SIZE = int(os.environ.get('MAX_REPO_SIZE', '20'))

# Constants
MAX_TIMEOUT = 60
MAX_BYTES = MAX_REPO_SIZE * 1024 * 1024

header_user_agent = 'User-Agent'
header_accept = 'Accept'
header_content_type = 'Content-Type'
header_content_length = 'Content-Length'
param_charset = 'charset'
default_charset = 'utf-8'

json_key_packages = 'packages'
param_url = 'url'
url_path = '/transform'


def run_server(server_class=HTTPServer):
    """Runs a builtin python server using the given server_class.

    :param server_class: server
    :type server_class: HTTPServer
    :return: None
    """
    server_address = (HOST_NAME, PORT_NUMBER)
    httpd = server_class(server_address, Handler)
    logger.warning('Server Starts on port - %s', PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        logger.warning('Server Stops on port - %s', PORT_NUMBER)


class Handler(BaseHTTPRequestHandler):
    def do_GET(s):
        """
        Respond to the GET request. The expected format of this request is:
                http://<host>:<port>/transform?url=<url> with `User-Agent`
                and `Accept` headers
        """
        errors = _validate_request(s)
        if errors:
            s.send_error(HTTPStatus.BAD_REQUEST, explain=errors)
            return

        query = dict(parse_qsl(urlparse(s.path).query))
        if param_url not in query:
            s.send_error(HTTPStatus.BAD_REQUEST,
                         explain=ErrorResponse.PARAM_NOT_PRESENT.to_msg(param_url))
            return

        logging.debug(">>>>>>>>>")

        user_agent = s.headers.get(header_user_agent)
        accept = s.headers.get(header_accept)
        decoded_url = query.get(param_url)

        try:
            json_response = handle(decoded_url, user_agent, accept)
        except Exception as e:
            s.send_error(HTTPStatus.BAD_REQUEST, explain=str(e))
            return

        s.send_response(HTTPStatus.OK)
        content_header = gen_universe.format_universe_repo_content_type(
            _get_repo_version(accept))
        s.send_header(header_content_type, content_header)
        s.send_header(header_content_length, len(json_response))
        s.end_headers()
        s.wfile.write(json_response.encode())


def handle(decoded_url, user_agent, accept):
    """Returns the requested json data. May raise an error instead, if it fails.

    :param decoded_url: The url to be fetched from
    :type decoded_url: str
    :param user_agent: User-Agent header value
    :type user_agent: str
    :param accept: Accept header value
    :return Requested json data
    :rtype str (a valid json object)
    """
    logger.debug('Url : %s\n\tUser-Agent : %s\n\tAccept : %s',
                 decoded_url, user_agent, accept)
    repo_version = _get_repo_version(accept)
    dcos_version = _get_dcos_version(user_agent)
    logger.debug('Version %s\nDC/OS %s', repo_version, dcos_version)

    req = Request(decoded_url)
    req.add_header(header_user_agent, user_agent)
    req.add_header(header_accept, accept)
    try:
        with urlopen(req, timeout=MAX_TIMEOUT) as res:
            charset = res.info().get_param(param_charset) or default_charset

            if header_content_length not in res.headers:
                raise ValueError(ErrorResponse.ENDPOINT_HEADER_MISS.to_msg())

            if int(res.headers.get(header_content_length)) > MAX_BYTES:
                raise ValueError(ErrorResponse.MAX_SIZE.to_msg())

            raw_data = res.read()
        packages = json.loads(raw_data.decode(charset)).get(json_key_packages)
    except (HTTPError, URLError) as error:
        logger.info("Request protocol error %s", decoded_url)
        logger.exception(error)
        raise error

    return render_json(packages, dcos_version, repo_version)


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
    packages_dict = {json_key_packages: processed_packages}
    errors = gen_universe.validate_repo_with_schema(
        packages_dict,
        repo_version
    )
    if len(errors) != 0:
        logger.error(errors)
        raise ValueError(ErrorResponse.VALIDATION_ERROR.to_msg(errors))
    return json.dumps(packages_dict)


def _validate_request(s):
    """

    :param s: The in built base http request handler
    :type s: BaseHTTPRequestHandler
    :return Error message (if any)
    :rtype String or None
    """
    if not urlparse(s.path).path == url_path:
        return ErrorResponse.INVALID_PATH.to_msg(s.path)

    if header_user_agent not in s.headers:
        return ErrorResponse.HEADER_NOT_PRESENT.to_msg(header_user_agent)

    if header_accept not in s.headers:
        return ErrorResponse.HEADER_NOT_PRESENT.to_msg(header_accept)


def _get_repo_version(accept_header):
    """Returns the version of the universe repo parsed.

    :param accept_header: String
    :return repo version as a string or raises Error
    :rtype str or raises an Error
    """
    result = re.findall(r'\bversion=v\d', accept_header)
    if result is None or len(result) is 0:
        raise ValueError(ErrorResponse.UNABLE_PARSE.to_msg(accept_header))
    result.sort(reverse=True)
    return str(result[0].split('=')[1])


def _get_dcos_version(user_agent_header):
    """Parses the version of dcos from the specified header.

    :param user_agent_header: String
    :return dcos version as a string or raises an Error
    :rtype str or raises an Error
    """
    result = re.search(r'\bdcos/\b\d\.\d{1,2}', user_agent_header)
    if result is None:
        raise ValueError(ErrorResponse.UNABLE_PARSE.to_msg(user_agent_header))
    return str(result.group().split('/')[1])


class ErrorResponse(Enum):
    INVALID_PATH = 'URL Path {} is invalid. Expected path /transform'
    HEADER_NOT_PRESENT = 'Header {} is missing'
    PARAM_NOT_PRESENT = 'Request parameter {} is missing'
    UNABLE_PARSE = 'Unable to parse header {}'
    VALIDATION_ERROR = 'Validation errors during processing {}'
    MAX_SIZE = 'Endpoint response exceeds maximum content size'
    ENDPOINT_HEADER_MISS = 'Endpoint doesn\'t return Content-Length header'

    def to_msg(self, *args):
        return self.value.format(args)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "INFO"),
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    run_server()
