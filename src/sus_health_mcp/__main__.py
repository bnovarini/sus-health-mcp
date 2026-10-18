import sys,json
from .server import mcp,dataset_info,http_app

def main():
 if '--check' in sys.argv:print(json.dumps(dataset_info(),indent=2));return
 if '--http' in sys.argv:
  import uvicorn
  uvicorn.run(http_app(),host='0.0.0.0',port=8080)
 else:mcp.run()
if __name__=='__main__':main()
