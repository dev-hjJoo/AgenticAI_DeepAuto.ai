import sys
import os
import json
import streamlit as st
from api_client import ApiClient


# PAGE LAYOUT
title = "Automated Code Review and Enhancement"
st.set_page_config(page_title=title, layout="wide")
st.title(title)

# Functions
def _changeFileName(file_name: str):
    ''' _changeFileName
    Snake 표기법으로 작성된 텍스트 파일(.txt)의 이름을 사람이 읽기 좋은 형태로 변환해주는 함수
    I: snake 표기법으로 작성된 파일명 (String) -> 예: test_case_1.txt
    O: 첫 글자 대문자 및 띄워쓰기로 작성된 파일명 (String) -> 예: Test Case 1
    '''
    file_name = file_name.removesuffix(".txt")
    file_name = ' '.join([piece.capitalize() for piece in file_name.split('_')])

    return file_name

def _loadTestCase(task_type: str):
    ''' _loadTestCase
        Task 별로 Test Case 파일들의 이름과 내용을 반환해주는 함수
        I: Test Case 문서가 저장된 폴더 경로 (String)
        O: 경로 내 포함된 txt 파일들의 이름과 내용이 담긴 딕셔너리 (DICT<파일명: 본문 내용>)
    '''
    repo_dir = os.getcwd()
    dir = repo_dir+"/fe/data/"+task_type

    examples =dict()
    if os.path.exists(dir):
        txt_files = [fn for fn in os.listdir(dir) if fn.endswith('.txt')]
        if len(txt_files) > 0:
            for file_name in sorted(txt_files):
                file_path = os.path.join(dir, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                    examples[_changeFileName(file_name)] = content
    
    return examples

def _onSubmit(query: str):
    ''' _onSubmit
        사용자 입력이 주어졌을 때 WAS 서버로 POST 요청을 수행
        I: Test Case 문서가 저장된 폴더 경로 (String)
        O: 경로 내 포함된 txt 파일들의 이름과 내용이 담긴 딕셔너리 (DICT<파일명: 본문 내용>)
    '''
    api = ApiClient()
    response = api.post('code', data={"query": query})
    st.session_state['code_review'] = response['result']

# Variables & Logic
examples = _loadTestCase('task1')
examples['자유 작성'] = ''
if not st.session_state.get('code_review', False):
    st.session_state['code_review'] = {}


# UI
input_area, output_area = st.columns(2)

# 1. 사용자 입력 영역
with input_area:
    selected = st.selectbox(
        label="Test Case",
        options=examples.keys(),
        index=len(examples)-1,
    )
    query = st.text_area(
        label='Enter Python code to review...', 
        value=examples[selected] if selected else '',
        height='content'
    )

    _, btn_col = st.columns([4, 1])
    btn_col.button('Submit', 
                   on_click=_onSubmit, 
                   args=(query,),
                   disabled=(not query),
                   type='primary', 
                   use_container_width=True)

# 2. 결과 출력 영역
with output_area.container(border=True):
    st.header('Report')

    # Metrics
    if st.session_state['code_review'].get('issues', False) and st.session_state['code_review'].get('refactoring_issues', False):
        cnt_issues_area, pylint_score_area = st.columns(2)
        
        with cnt_issues_area.container(border=True):
            # 이슈 개수
            st.markdown('🔖 **Number of bugs and issues** included in the code')
            cnt_iss = len(st.session_state['code_review']['issues'])
            cnt_rf_iss = len(st.session_state['code_review']['refactoring_issues'])

            col1, col2 = st.columns(2)
            col1.metric(label='User Code', 
                    value=cnt_iss)
            col2.metric(label='Refactored Code', 
                    value=cnt_rf_iss, 
                    delta=cnt_iss-cnt_rf_iss)
        
        with pylint_score_area.container(border=True):
            # pylint 점수
            st.markdown('🔖 **PyLint Score**')
            pylint_score = st.session_state['code_review']['pylint_score']
            rf_pylint_score = st.session_state['code_review']['refactoring_pylint_score']

            col1, col2 = st.columns(2)
            col1.metric(label='User Code', 
                    value=pylint_score)
            col2.metric(label='Refactored Code', 
                    value=rf_pylint_score, 
                    delta=rf_pylint_score-pylint_score)
        
    
    # Issues
    if st.session_state['code_review'].get('issues', False) and len(st.session_state['code_review']['issues']) > 0:
        st.subheader('🎯 Issues')
        issues = st.session_state['code_review']['issues']
        for issue in issues:
            with st.expander(issue['title'], icon='🚨' if issue['severity']=='CRITICAL' else '⚠️'):
                st.caption(issue['description'])

                if issue['issue_type'] == 'Bugs':
                    issue_type = ":violet-badge[:material/bug_report: Bugs]"
                elif issue['issue_type'] == 'Security Issue':
                    issue_type = ":orange-badge[:material/security: Security Issues]"
                else:
                    issue_type = ":blue-badge[:material/swap_driving_apps_wheel: Performance Problem]"

                code_line_number = f'Line {issue['start_line']}-{issue['end_line']}' if issue['start_line'] != issue['end_line'] else f'Line {issue['start_line']}'
                st.markdown(issue_type+' '+code_line_number)
                
                st.code('\n'.join(issue['code_snippet']))
    else:
        with st.container(border=True):
            msg_before_click = "To check the report, enter the code and click the 'Submit' button."
            st.caption(msg_before_click)

    
    # Refactoring Code
    if st.session_state['code_review'].get('refactoring_code', False):
        st.subheader('✏️ Refactored Code Suggestion')
        refactoring_code = st.session_state['code_review']['refactoring_code']
        st.code(refactoring_code, language='python')
    

    # Unit code
    if st.session_state['code_review'].get('unit_code', False):
        st.subheader('⚒️ Unit Test Generation')
        unit_test_code = st.session_state['code_review']['unit_code']
        st.code(unit_test_code, language='python')
    