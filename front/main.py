import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# PAGE LAYOUT
title = "Automated Code Review and Enhancement"
st.set_page_config(page_title=title, layout="wide")
st.title(title)

# Functions
def _changeFileName(file_name):
    ''' _changeFileName
    I: snake 표기법으로 작성된 파일명 (String) -> 예: test_case_1.txt
    O: 첫 글자 대문자 및 띄워쓰기로 작성된 파일명 (String) -> 예: Test Case 1
    '''
    file_name = file_name.removesuffix(".txt")
    file_name = ' '.join([piece.capitalize() for piece in file_name.split('_')])

    return file_name

def _loadTestCase(dir):
    ''' _loadTestCase
        I: Test Case 문서가 저장된 폴더 경로 (String)
        O: 경로 내 포함된 txt 파일들의 이름과 내용이 담긴 딕셔너리 (DICT<파일명: 본문 내용>)
    '''
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


# Variables
dir = "./data/task1"
examples = _loadTestCase(dir)
examples['자유 작성'] = ''


# UI
input_area, output_area = st.columns(2)
with input_area:
    selected = st.selectbox(
        label="Test Case",
        options=examples.keys(),
        index=len(examples)-1,
    )
    st.text_area(
        label='Enter Python code to review...', 
        value=examples[selected] if selected else '',
        height='content'
    )

    _, btn_col = st.columns([4, 1])
    btn_col.button('Submit', type='primary', use_container_width=True)

with output_area.container(border=True):
    st.header('Report')

    st.subheader('🚨 Bugs & Security Issues')
    with st.expander("Contains SQL injection vulnerability"):
        code = '''query = f"SELECT * FROM users WHERE id = {user_data['id']}"'''
        st.code(code)
    with st.expander("Contains buffer overflow risk"):
        code = '''buffer = [0] * 10
    for i in range(len(user_data['items'])):  # No bounds checking
        buffer[i] = user_data['items'][i]'''
        st.code(code)

    st.subheader('⚠️ Performance Problems')
    with st.expander("Inefficient list operations"):
        code = '''result = []'''
        st.code(code)
    with st.expander("Repeated calculations"):
        code = '''mean = sum(data_list) / len(data_list)'''
        st.code(code)
    with st.expander("Unnecessary list creation"):
        code = '''filtered = [x for x in data_list if x > mean]'''
        st.code(code)

    st.subheader('✏️ Refactored Code Suggestion')
    refactored_code = '''리팩토링한 코드'''
    st.code(refactored_code, language='python')

    st.subheader('⚒️ Unit Test Generation')
    refactored_code = '''유닛 테스트 코드'''
    st.code(refactored_code, language='python')