#!/usr/bin/env python3
"""
Local development server for the RepoGenesis Leaderboard.

Serves the leaderboard static files over HTTP so that fetch() requests
work correctly (browsers block fetch on file:// protocol).

Usage:
    python serve.py             # default port 8000
    python serve.py --port 3000 # custom port
"""

import argparse
import http.server
import os
import socketserver
import webbrowser


DEFAULT_PORT = 4090


def main():
    """Start the local HTTP server for the leaderboard."""
    parser = argparse.ArgumentParser(
        description="Serve the RepoGenesis Leaderboard locally"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to serve on (default: {DEFAULT_PORT})",
    )
    args = parser.parse_args()

    # Change to the leaderboard directory so files are served from here
    leaderboard_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(leaderboard_dir)

    handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", args.port), handler) as httpd:
        url = f"http://localhost:{args.port}"
        print(f"Serving RepoGenesis Leaderboard at {url}")
        print("Press Ctrl+C to stop.")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
