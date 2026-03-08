import uvicorn
import argparse

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Run Todo API server")
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    # settings = get_settings()
    
    # print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"🚀 Starting")
    print(f"📚 Documentation available at http://{args.host}:{args.port}/api/docs/")

    uvicorn.run(
        "app.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )