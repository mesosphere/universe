#!/usr/bin/env python3

import json
import logging
import os
import re
from enum import Enum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen

import gen_universe

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
transform_url_path = '/transform'

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get('LOGLEVEL', 'INFO'),
    format='[%(asctime)s|%(threadName)s|%(levelname)s]: %(message)s'
)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle each request in a separate thread"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override the default behavior of writing to stderr with `logging`"""
        logger.info("[%s] %s", self.address_string(), format % args)

    def do_GET(self):
        logger.debug('\n{}\n{}'.format(self.requestline, self.headers).rstrip())
        url_path = urlparse(self.path).path
        try:
            if url_path == transform_url_path:
                self.handle_transform()
            else:
                raise ValueError(ErrorResponse.INVALID_PATH.to_msg(url_path))
        except Exception as e:
            self.send_error(
                HTTPStatus.BAD_REQUEST,
                explain=e.message if hasattr(e, 'message') else str(e)
            )

    def handle_transform(self):
        """
        Respond to the GET request. The expected format of this request is:
                http://<host>:<port>/transform?url=<url> with `User-Agent`
                and `Accept` headers
        """
        errors = _validate_request(self)
        if errors:
            self.send_error(HTTPStatus.BAD_REQUEST, explain=errors)
            return

        query = dict(parse_qsl(urlparse(self.path).query))
        if param_url not in query:
            self.send_error(
                HTTPStatus.BAD_REQUEST,
                explain=ErrorResponse.PARAM_NOT_PRESENT.to_msg(param_url)
            )
            return

        user_agent = self.headers.get(header_user_agent)
        accept = self.headers.get(header_accept)
        decoded_url = query.get(param_url)

        try:
            json_response = handle(decoded_url, user_agent, accept)
        except HTTPError as e:
            logger.info(
                'Upstream error :\nURL: [%s]\nReason: [%s %s]\nBody:\n[%s]',
                decoded_url,
                e.code,
                e.reason,
                e.read(),
                exc_info=True
            )
            self.send_error(HTTPStatus.BAD_GATEWAY, explain=str(e))
            return
        except URLError as e:
            logger.info(
                'Route error :\nURL: [%s]\nReason: [%s]',
                decoded_url,
                e.reason,
                exc_info=True
            )
            self.send_error(HTTPStatus.BAD_GATEWAY, explain=str(e))
            return

        self.send_response(HTTPStatus.OK)
        content_header = gen_universe.format_universe_repo_content_type(
            _get_repo_version(accept))
        self.send_header(header_content_type, content_header)
        self.send_header(header_content_length, len(json_response))
        self.end_headers()
        self.wfile.write(json_response.encode())


def run_server():
    """Runs a builtin python server using the given server_class.

    :return: None
    """
    server_address = (HOST_NAME, PORT_NUMBER)
    httpd = ThreadedHTTPServer(server_address, Handler)
    logger.warning('Server Starts on port - %s', PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        logger.warning('Server Stops on port - %s', PORT_NUMBER)


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
    req = Request(decoded_url)
    req.add_header(header_user_agent, user_agent)
    req.add_header(header_accept, accept)
    logger.debug('\n{}\n{}\n{}'.format(
        '<--- Upstream Request --->',
        req.full_url,
        _format_dict(req.headers)
    ))
    with urlopen(req, timeout=MAX_TIMEOUT) as res:
        charset = res.info().get_param(param_charset) or default_charset

        if header_content_length not in res.headers:
            raise ValueError(ErrorResponse.ENDPOINT_HEADER_MISS.to_msg())

        if int(res.headers.get(header_content_length)) > MAX_BYTES:
            raise ValueError(ErrorResponse.MAX_SIZE.to_msg())
        resp_content = res.read().decode(charset)
        logger.debug('\n{}\n{} {}\n{}\n{}'.format(
            '<--- Upstream Response --->',
            res.getcode(),
            res.reason,
            _format_dict(res.headers),
            resp_content if res.getcode() // 200 != 1 else ''
        ))
        repo_version = _get_repo_version(accept)
        dcos_version = _get_dcos_version(user_agent)
        logger.debug('Version [%s] DC/OS [%s]', repo_version, dcos_version)
        try:
            json_body = json.loads(resp_content)
        except ValueError as e:
            logger.exception(e)
            raise ValueError(ErrorResponse.INVALID_JSON_FROM_UPSTREAM.to_msg(decoded_url))
        assert json_key_packages in json_body, 'Expected key [{}] is not present in response'.format(json_key_packages)
        return render_json(
            json_body[json_key_packages],
            dcos_version,
            repo_version
        )


def render_json(packages, dcos_version, repo_version):
    """Returns the json

    :param packages: packages list
    :type packages: list
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
        raise ValueError(ErrorResponse.UNABLE_PARSE.to_msg(
            header_accept, accept_header
        ))
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
        raise ValueError(ErrorResponse.UNABLE_PARSE.to_msg(
            header_user_agent, user_agent_header
        ))
    return str(result.group().split('/')[1])


def _format_dict(d):
    """Takes a dictionary and returns it in a pretty formatted string
    :param d: dict
    :return pretty formatted dictionary
    :rtype str
    """
    return '\n'.join('{}: {}'.format(k, v) for k, v in d.items())


class ErrorResponse(Enum):
    INVALID_PATH = 'URL Path {} is invalid. Expected path /transform'
    HEADER_NOT_PRESENT = 'Header {} is missing'
    PARAM_NOT_PRESENT = 'Request parameter {} is missing'
    UNABLE_PARSE = 'Unable to parse header {}:{}'
    VALIDATION_ERROR = 'Validation errors during processing {}'
    MAX_SIZE = 'Endpoint response exceeds maximum content size'
    ENDPOINT_HEADER_MISS = 'Endpoint doesn\'t return Content-Length header'
    INVALID_JSON_FROM_UPSTREAM = 'Upstream [{}] did not return a json body'

    def to_msg(self, *args):
        return self.value.format(args)


if __name__ == '__main__':
    run_server()
