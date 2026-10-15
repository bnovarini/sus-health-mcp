"""Run the fixed, read-only serving implementation."""
from .staged_server import mcp, main as http_main
import os, sys

def main():
    if '--http' in sys.argv:
        http_main()
    else:
        mcp.run()

if __name__ == '__main__':
    main()
