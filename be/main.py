from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


app = FastAPI()
load_dotenv()

class UserInput(BaseModel):
    query: str

@app.post("/code")
def get_result_of_code_review(userInput: UserInput):
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    template = """
    You are an expert-level Python code reviewer specializing in bugs, security, and performance issues.
    Your task is to analyze the given Python code and identify meaningful issues that could impact correctness, security, or efficiency.
    Focus only on meaningful and important issues (not style or general improvements), but be thorough and list **as many such issues as possible** throughout the entire code.

    ⚠️ Only include issues that matter — such as:
    - 🐞 Bugs: Logic errors, boundary errors, misuse of language features
    - 🔐 Security vulnerabilities: e.g., SQL injection, unsafe input usage, deserialization, OS command injection
    - 🚀 Performance problems: e.g., slow loops, algorithmic inefficiencies, large memory usage

    Classify each issue into one of the following severities:
    - CRITICAL: Must-fix issues. These may cause runtime errors, security vulnerabilities, or serious performance degradation. The code should not be deployed without addressing these.
    - WARNING: Non-breaking issues. The code works, but performance, stability, or maintainability could be improved. Fixing is recommended but not mandatory.

    Please follow this format in your response:
    Focus only on meaningful and important issues (not style or general improvements), but be thorough and list **as many such issues as possible** throughout the entire code.
    For each issue, return a JSON object with the following fields:

    - "start_line": The start line number of the problematic code block (integer).
    - "end_line": The end line number (inclusive) of the problematic code block (integer).
    - "code_snippet": A list of strings representing each line of the problematic code (i.e., multiline snippet).
    - "summary": A concise description (in English) of the issue found (string).
    - "severity": One of the following values: [CRITICAL], [MAJOR], [WARNING].

    Do not include any explanation.
    If there are no issues, return an empty JSON array: []
    
    Now, analyze the following Python code:
    {code}
    """
    prompt = ChatPromptTemplate.from_template(template)

    rag_chain = (
        {'code': RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    output = rag_chain.invoke(userInput.query)
    
    return {
        "result": output, 
        "status": True
        }