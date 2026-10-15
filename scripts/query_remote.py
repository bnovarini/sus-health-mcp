"""Small Streamable HTTP client. No login or API key required."""
import argparse, asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def run(url, tool, arguments):
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if tool == 'list':
                result = await session.list_tools()
            else:
                result = await session.call_tool(tool, arguments)
            print(result.model_dump_json(indent=2))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tool', nargs='?', default='dataset_info')
    parser.add_argument('--arguments', default='{}')
    parser.add_argument('--url', default='https://sus-health-mcp.fly.dev/mcp')
    args = parser.parse_args()
    asyncio.run(run(args.url, args.tool, json.loads(args.arguments)))

if __name__ == '__main__':
    main()
