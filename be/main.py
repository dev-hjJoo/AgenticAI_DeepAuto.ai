from fastapi import FastAPI

app = FastAPI()

@app.get("/connect")
def connect():
    print('='*30)
    print('HELLO FastAPI')
    print('='*30)
    
    return {
        "msg": "Hello FastAPI", 
        "status": True
        }