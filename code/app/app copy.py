import streamlit as st
import json
from openai_client import ask_openai, SYSTEM_PROMPT
from utils import execute_sql, make_plot

st.title('SQLite QA Agent')

if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

user_question = st.text_input('Ask a question about the database:')
if st.button('Submit') and user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    response = ask_openai(st.session_state.messages)
    # Call and log the OpenAI assistant response TODO del
    print(f"User question: {user_question}")
    response = ask_openai(st.session_state.messages)
    msg = response.choices[0].message

    # Handle function calls
    # Check for function_call attribute on message
    if hasattr(msg, 'function_call') and msg.function_call:
        fn_name = msg.function_call.name
        args = json.loads(msg.function_call.arguments)
        if fn_name == 'execute_sql':
            try:
                rows = execute_sql(args['query'])
                st.write('Query results:', rows)
                st.session_state.messages.append({"role":"assistant","content":None,"function_call":msg.function_call})
                st.session_state.messages.append({"role":"function","name":"execute_sql","content":json.dumps(rows)})
            except Exception as e:
                st.error(f"SQL Error: {e}")
        elif fn_name == 'make_plot':
            try:
                path = make_plot(args['data'], args['config'])
                st.image(path)
                st.session_state.messages.append({"role":"assistant","content":None,"function_call":msg.function_call})
                st.session_state.messages.append({"role":"function","name":"make_plot","content":path})
            except Exception as e:
                st.error(f"Plot Error: {e}")
        # After handling, get a final answer
        followup = ask_openai(st.session_state.messages)
        final = followup.choices[0].message
        st.write(final.content)
        st.session_state.messages.append({"role":"assistant","content":final.content})
