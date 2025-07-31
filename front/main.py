import streamlit as st

# PAGE LAYOUT
title = "Automated Code Review and Enhancement"
st.set_page_config(page_title=title, layout="wide")
st.title(title)

# Variables
test_case = {
    'Test Case 1': 'test case 1',
    'Test Case 2': 'test case 2',
    'Test Case 3': 'test case 3',
    }
test_case['자유 작성'] = ''

# UI
input_area, output_area = st.columns(2)
with input_area:
    selected = st.selectbox(
        label="Test Case",
        options=test_case.keys(),
        index=None
    )
    st.text_area(label='Enter Python code to review...', 
                 value=test_case[selected] if selected else '')

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