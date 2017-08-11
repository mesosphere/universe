#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen
import json
import re
import time
import gen_universe

# TODO move somewhere / read from somewhere
HOST_NAME = '0.0.0.0'
PORT_NUMBER = 7373

header_user_agent = 'User-Agent'
header_accept = 'Accept'
param_url = 'url'
url_path = '/transform'
default_charset = 'utf-8'
header_content_type = 'Content-Type'

def main():
    run_server()


def run_server(server_class=HTTPServer):
    server_address = (HOST_NAME, PORT_NUMBER)
    httpd = server_class(server_address, Handler)
    print(time.asctime(),
          'Server Starts - {}:{}'.format(HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        print(time.asctime(),
              'Server Stops - {}:{}'.format(HOST_NAME, PORT_NUMBER))


class Handler(BaseHTTPRequestHandler):
    def do_GET(s):
        """
        Respond to the GET request. The expected format of this request is:
                http://<host>:<port>/transform?url=<url>
        """
        if urlparse(s.path).path != url_path:
            s.send_error(404, ErrorResponse.INVALID_PATH)
            return

        if not (header_user_agent in s.headers and header_accept in s.headers):
            s.send_error(400, ErrorResponse.INVALID_HEADERS)
            return

        query = dict(parse_qsl(urlparse(s.path).query))

        if param_url not in query:
            s.send_error(400, ErrorResponse.INVALID_PARAMETER)
            return

        user_agent = s.headers.get(header_user_agent)
        accept = s.headers.get(header_accept)
        decoded_url = query.get(param_url)
        try:
            json_response = handle(decoded_url, user_agent, accept)
            s.send_response(200)
            content_header = gen_universe.format_universe_repo_content_type(
                get_repo_version(accept))
            s.send_header(header_content_type, content_header)
            s.end_headers()
            s.wfile.write(json_response.encode())
        except Exception as e:
            s.send_error(400, str(e))


def handle(decoded_url, user_agent, accept):
    repo_version = get_repo_version(accept)
    dcos_version = get_dcos_version(user_agent)
    print('Url {} \nAgent {} \nAccept {} \nVersion {} \nDCOS {}'.format(
        decoded_url, user_agent, accept, repo_version, dcos_version))

    req = Request(decoded_url)
    req.add_header(header_user_agent, user_agent)
    req.add_header(header_accept, accept)
    res = urlopen(req)
    charset = res.info().get_param('charset') or default_charset

    json_data = json.loads(res.read().decode(charset))
    packages = json_data.get('packages')
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
        raise ValueError(ErrorResponse.VALIDATION_ERROR)
    return updated_json_data


def get_repo_version(accept_header):
    # TODO May be support versions of two digits ?
    result = re.findall(r'\bversion=v\d', accept_header)
    if result is None or len(result) is 0:
        raise ValueError(ErrorResponse.UNABLE_PARSE)
    result.sort(reverse=True)
    return result[0].split('=')[1]


def get_dcos_version(user_agent_header):
    result = re.search(r'\bdcos\/\b\d\.\d{1,2}', user_agent_header)
    if result is None:
        raise ValueError(ErrorResponse.UNABLE_PARSE)
    return result.group().split('/')[1]


class ErrorResponse:
    INVALID_PATH = 'URL Path is invalid'
    INVALID_HEADERS = 'Headers are invalid'
    INVALID_PARAMETER = 'Request parameters are invalid'
    UNABLE_PARSE = 'Unable to parse headers'
    VALIDATION_ERROR = 'Repo version and validation error mismatch'


if __name__ == '__main__':
    main()
