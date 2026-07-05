from fastapi import FastAPI


app = FastAPI(title="Enterprise Knowledge Base Agent")


@app.get("/health")
def health_check():
    return {"status": "ok"}