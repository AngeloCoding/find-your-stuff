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
    # Call and log the OpenAI assistant response
    response = ask_openai(st.session_state.messages)
    msg = response.choices[0].message

    # Handle function calls
    if hasattr(msg, 'function_call') and msg.function_call:
        fn_name = msg.function_call.name
        args = json.loads(msg.function_call.arguments)
        if fn_name == 'execute_sql':
            try:
                rows = execute_sql(args['query'])
                st.write('Query results:', rows)
                # Append the function call and its result to context properly
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": fn_name,
                        "arguments": msg.function_call.arguments
                    }
                })
                st.session_state.messages.append({
                    "role": "function",
                    "name": "execute_sql",
                    "content": json.dumps(rows)
                })
            except Exception as e:
                st.error(f"SQL Error: {e}")
        elif fn_name == 'make_plot':
            try:
                path = make_plot(args['data'], args['config'])
                st.image(path)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": fn_name,
                        "arguments": msg.function_call.arguments
                    }
                })
                st.session_state.messages.append({
                    "role": "function",
                    "name": "make_plot",
                    "content": path
                })
            except Exception as e:
                st.error(f"Plot Error: {e}")
        # After handling, get a final answer without resending full schema
        # Use a minimal system prompt for follow-up to avoid re-sending large schema
        minimal_system = {"role": "system", "content": "You are a SQL assistant for a SQLite database. Continue the conversation."}
        # Exclude original system prompt when making the follow-up
        followup_messages = [minimal_system] + [m for m in st.session_state.messages if m.get('role') != 'system']
        followup = ask_openai(followup_messages)
        final = followup.choices[0].message
        st.write(final.content)
        st.session_state.messages.append({"role": "assistant", "content": final.content})
        followup = ask_openai(st.session_state.messages)
        final = followup.choices[0].message
        st.write(final.content)
        st.session_state.messages.append({"role":"assistant","content":final.content})
