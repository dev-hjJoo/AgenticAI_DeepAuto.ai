import json
from dotenv import load_dotenv
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import subprocess
import tempfile
import os

''' 
====================
        GRAPH 
====================
'''

# TODO: Pydantic 이용해서 데이터 유효성 검사 로직 추가
class CodeIssue(TypedDict):
    title: str
    description: str
    issue_type: str
    severity: str
    start_line: int
    end_line: int
    code_snippet: list[str]

# State schema
class CodeReviewState(TypedDict):
    user_code: str
    refactoring_code: str
    issues: CodeIssue
    refactoring_issues: CodeIssue
    pylint_score: str
    refactoring_pylint_score: str
    unit_code: str


class CodeReviewGraph:
    def __init__(self):
        builder = StateGraph(CodeReviewState)

        # Add Nodes
        builder.add_node("extract_code_issues", extract_code_issues)
        builder.add_node("suggest_code_improvements", suggest_code_improvements)
        builder.add_node("generate_unit_tests", generate_unit_tests)

        # Add Edges
        builder.add_edge(START, "extract_code_issues")
        builder.add_conditional_edges(
            "extract_code_issues",
            self._decide_next_step,
            {
                "suggest_code_improvements": "suggest_code_improvements",
                "generate_unit_tests": "generate_unit_tests"
            }
        )
        builder.add_edge("suggest_code_improvements", "extract_code_issues")
        builder.add_edge("generate_unit_tests", END)

        # Compile
        self.graph = builder.compile()

        # Save Graph Image
        image_bytes = self.graph.get_graph().draw_mermaid_png()
        with open("docs/graph_output.png", "wb") as f:
            f.write(image_bytes)
    
    def _decide_next_step(self, state: CodeReviewState) -> Literal["suggest_code_improvements", "generate_unit_tests"]:
        if not state.get('refactoring_code', False):
            return "suggest_code_improvements"  
        else:
            return "generate_unit_tests"

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

    - "pylint_score": Extract and include the overall pylint_score if it exists in the static analysis report.
        - Your code has been rated at `pytlint_score`/10
    - "title": a short and concise summary of the issue (e.g., "Contains SQL injection vulnerability")
    - "description": A concise description (in English) of the issue found (string).
    - "issue_type": One of the following values: Bugs, Security Issue, Performance Problem
    - "severity": One of the following values: CRITICAL, WARNING.
        - For Pylint issues: Use "WARNING" if the code type starts with `C` or `I`. Otherwise, use "CRITICAL".
        - For Bandit issues: Always use "CRITICAL".
    - "start_line": The start line number of the problematic code block (integer).
    - "end_line": The end line number (inclusive) of the problematic code block (integer).
    - "code_snippet": A list of strings representing each line of the problematic code (i.e., multiline snippet).
        - You must ensure the snippet content and line numbers exactly match the original code** — validate both the content and the position against the provided source code.

    Your output must follow this format (strict JSON only, no markdown or explanation):
    If there are no issues, return an empty JSON array: []
    
    Here is the code to analyze:

    {code}

    And here is the static analysis result:

    {static_analysis}

    ---
    Return your result as a JSON array containing all detected issues.
    ```json
    {{
    "pylint_score": float or null,
    "issues": [
        {{
        "title": string,              // Short summary, e.g., "Possible SQL injection"
        "description": string,        // Description of the issue (in English)
        "issue_type": "Bugs" | "Security Issue" | "Performance Problem",
        "severity": "CRITICAL" | "WARNING",  // See rules below
        "start_line": integer,        // Line number where issue starts
        "end_line": integer,          // Line number where issue ends (inclusive)
        "code_snippet": [...]         // List of code lines, must match the original source exactly
        }},
        ...
    ]
    }}
    """
    prompt = ChatPromptTemplate.from_template(template)

    rag_chain = (
        RunnablePassthrough()
        | prompt
        | llm
        | StrOutputParser()
    )
    if not state.get('issues', False):
        static_analysis = _analyze_code(state['user_code'])
        
        output = rag_chain.invoke({"code": state['user_code'], 'static_analysis': static_analysis})

        # 결과 후처리
        result = _remove_markdown_code_tag(output)
        result = json.loads(result)

        # Update states
        return {"issues": result['issues'], "pylint_score": result['pylint_score']}

    if state.get('refactoring_code', False) and not state.get('refactoring_issues', False):
        static_analysis = _analyze_code(state['refactoring_code'])

        output = rag_chain.invoke({"code": state['refactoring_code'], 'static_analysis': static_analysis})
        
        # 결과 후처리
        result = _remove_markdown_code_tag(output)
        result = json.loads(result)

        # Update states
        return {"refactoring_issues": result['issues'], "refactoring_pylint_score": result['pylint_score']}

    

def suggest_code_improvements(state: CodeReviewState) -> CodeReviewState:
    template = """
    You are given a Python code snippet under the field user_code, and a list of detected issues under the field issues.
    Each issue includes:
    - "title": a short and concise summary of the issue (e.g., "Contains SQL injection vulnerability")
    - "description": A concise description (in English) of the issue found (string).
    - "issue_type": One of the following values: Bugs, Security Issue, Performance Problem
    - "severity": One of the following values: CRITICAL, WARNING.
    - "start_line": The start line number of the problematic code block (integer).
    - "end_line": The end line number (inclusive) of the problematic code block (integer).
    - "code_snippet": A list of strings representing each line of the problematic code (i.e., multiline snippet).

    Your task is to:

    Generate a fixed version of the code that eliminates all issues listed.
    Preserve the overall logic and structure of the code as much as possible.
    For every modified line, append a Python comment containing the corresponding issue title (e.g., # Fixed: Potential index out of range error).

    Do not include any explanation or extra output—only return the full corrected Python code with inline comments.

    [user_code]
    {user_code}

    [issues]
    {issues}
    """

    prompt = ChatPromptTemplate.from_template(template)

    rag_chain = (
        RunnablePassthrough()
        | prompt
        | llm
        | StrOutputParser()
    )
    output = rag_chain.invoke({"user_code": state['user_code'], 'issues': state['issues']})
    result = _remove_markdown_code_tag(output)

    return {'refactoring_code': result}

def generate_unit_tests(state: CodeReviewState) -> CodeReviewState:
    template = '''
    You are given a Python code snippet under the field code. Your task is to:

    1. Generate unittest-style test cases for the given code using Python's built-in unittest module.
    2. Ensure all methods and branches in the given code are tested thoroughly.
    3. Include both positive and negative test cases that demonstrate expected and failing behaviors.
    4. The test code should:
    - Import the target class or functions if needed.
    - Use the unittest.TestCase class structure.
    - Include meaningful test method names and assertions.
    5. Do not include any explanation—output only the full Python test code.

    Example Output:
    class UserAuthentication:
        def __init__(self, username, password):
            self.username = username
            self.password = password
        
        def validate_credentials(self):
            if len(self.password) < 8:
                return False
            if not any(c.isupper() for c in self.password):
                return False
            return True
        
        def generate_token(self):
            if self.validate_credentials():
                return f"token_{{self.username}}_{{len(self.password)}}"
            return None
    
    Input:
    {code}
    '''

    prompt = ChatPromptTemplate.from_template(template)

    rag_chain = (
        RunnablePassthrough()
        | prompt
        | llm
        | StrOutputParser()
    )
    output = rag_chain.invoke({"code": state['refactoring_code']})
    result = _remove_markdown_code_tag(output)

    return {'unit_code': result}
        
        

''' 
====================
      FUNCTION
====================
'''

def _analyze_code(code: str) -> dict:
    ''' _analyze_code
        주어진 Python 코드 문자열을 임시 파일에 저장한 후, Pylint, Flake8, Bandit, MyPy를 실행하여 결과 반환
        I: 문자열 형식의 파이썬 코드 (String)
        O: 정적 도구(pylint, flake8, bandit, mypy) 별 분석 결과가 담긴 딕셔너리 (DICT<도구명(String): 분석 결과(String)>)
    '''
    """"""
    results = {}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w') as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        # Pylint
        pylint_out = subprocess.run(
            ["pylint", tmp_path, "--disable=all", "--enable=E,W,C,R"], # E: Error, W: Warning, C: Convention, R: Refactor
            capture_output=True,
            text=True
        )
        results["pylint"] = pylint_out.stdout

        # Flake8
        flake8_out = subprocess.run(
            ["flake8", tmp_path],
            capture_output=True,
            text=True
        )
        results["flake8"] = flake8_out.stdout

        # Bandit
        bandit_out = subprocess.run(
            ["bandit", "-r", tmp_path, "-q", "-n", "5"],
            capture_output=True,
            text=True
        )
        results["bandit"] = bandit_out.stdout

        # MyPy
        mypy_out = subprocess.run(
            ["mypy", tmp_path],
            capture_output=True,
            text=True
        )
        results["mypy"] = mypy_out.stdout

    finally:
        os.remove(tmp_path)

    # 문자열 형태로 변환
    str_results = ''
    for tool, output in results.items():
        str_results = str_results + f"\n== {tool.upper()} REPORT ==" + '\n' + output.strip() + '\n'

    return str_results

def _remove_markdown_code_tag(code: str):
    output = code.strip()
    if output.startswith("```json"):
        output = output[len('```json'):]
    if output.startswith("```python"):
        output = output[len('```python'):]
    if output.endswith("```"):
        output = output[:-len('```')]
    
    return output.strip()