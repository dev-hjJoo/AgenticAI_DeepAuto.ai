import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI
from pydantic import BaseModel

from be.agent.codeReview import CodeReviewGraph

app = FastAPI()

class UserInput(BaseModel):
    query: str

@app.post("/code")
def get_result_of_code_review(userInput: UserInput):
    
    graph = CodeReviewGraph()
    output = graph.invoke(userInput.query)
    
    return {
        "result": output, 
        "status": True
        }