import json
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

''' 
====================
        GRAPH 
====================
'''

# TODO: Pydantic 이용해서 데이터 유효성 검사 로직 추가
class CodeIssue(TypedDict):
    title: str
    summary: str
    issue_type: str
    severity: str
    start_line: int
    end_line: int
    code_snippet: list[str]

# State schema
class CodeReviewState(TypedDict):
    user_code: str
    issues: CodeIssue
    refactored_code: str
    unit_code: str


class CodeReviewGraph:
    def __init__(self):
        builder = StateGraph(CodeReviewState)

        # Add Nodes
        builder.add_node("extract_code_issues", extract_code_issues)

        # Add Edges
        builder.add_edge(START, "extract_code_issues")
        builder.add_edge("extract_code_issues", END)

        # Compile
        self.graph = builder.compile()

    def invoke(self, query):
        initial_state = {'user_code': query}
        output = self.graph.invoke(initial_state) 

        return output

    
''' 
====================
        NODE 
====================
'''

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def extract_code_issues(state: CodeReviewState) -> CodeReviewState:
    template = """
    You are an expert-level Python code reviewer specializing in bugs, security, and performance issues.
    Your task is to analyze the given Python code and identify meaningful issues that could impact correctness, security, or efficiency.
    Focus only on meaningful and important issues (not style or general improvements), but be thorough and list **as many such issues as possible** throughout the entire code.

    ⚠️ Only include issues that matter — such as:
    - 🐞 Bugs: Logic errors, boundary errors, misuse of language features
    - 🔐 Security Issues: e.g., SQL injection, unsafe input usage, deserialization, OS command injection
    - 🚀 Performance problems: e.g., slow loops, algorithmic inefficiencies, large memory usage

    Classify each issue into one of the following severities:
    - CRITICAL: The issue may cause security vulnerabilities (e.g., injection attacks), system crashes, or major functional failures. All bugs and security errors are included in "CRITICAL"
    - WARNING: The code works correctly, but optimizations or improvements (e.g., performance, readability) are recommended.

    Please follow this format in your response:
    Focus only on meaningful and important issues (not style or general improvements), but be thorough and list **as many such issues as possible** throughout the entire code.
    For each issue, return a JSON object with the following fields:

    - "title": a short and concise summary of the issue (e.g., "Contains SQL injection vulnerability")
    - "summary": A concise description (in English) of the issue found (string).
    - "issue_type": One of the following values: Bugs, Security Issue, Performance Problem
    - "severity": One of the following values: CRITICAL, WARNING.
    - "start_line": The start line number of the problematic code block (integer).
    - "end_line": The end line number (inclusive) of the problematic code block (integer).
    - "code_snippet": A list of strings representing each line of the problematic code (i.e., multiline snippet).

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
    output = rag_chain.invoke(state['user_code'])
    issues = json.loads(output[len('```json'): -len('```')].strip())

    # Update states
    return {"issues": issues}

def suggest_code_improvements(state: CodeReviewState) -> CodeReviewState:
    pass

def generate_unit_tests(state: CodeReviewState) -> CodeReviewState:
    pass
        
        


    