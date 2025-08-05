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

with output_area.container(border=True):
    st.header('Report')
    msg_before_click = "To check the report, enter the code and click the 'Submit' button."
    
    st.subheader('🎯 Issues')
    if st.session_state['code_review'].get('issues', False) and len(st.session_state['code_review']['issues']) > 0:
        issues = st.session_state['code_review']['issues']
        for issue in issues:
            with st.expander(issue['title'], icon='🚨' if issue['severity']=='CRITICAL' else '⚠️'):
                st.caption(issue['summary'])

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
            st.caption(msg_before_click)

    st.subheader('✏️ Refactored Code Suggestion')
    if st.session_state['code_review'].get('refactored_code', False):
        refactored_code = st.session_state['code_review']['refactored_code']
        st.code(refactored_code, language='python')
    else:
        with st.container(border=True):
            st.caption(msg_before_click)

    st.subheader('⚒️ Unit Test Generation')
    if st.session_state['code_review'].get('unit_code', False):
        refactored_code = '''유닛 테스트 코드'''
        st.code(refactored_code, language='python')
    else:
        with st.container(border=True):
            st.caption(msg_before_click)