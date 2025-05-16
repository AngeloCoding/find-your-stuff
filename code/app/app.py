import streamlit as st
import json
from openai_client import ask_openai, SYSTEM_PROMPT
from utils import execute_sql, make_plot

st.title('SQLite QA Agent')

if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

def handle_query(user_question: str):
    # 1) Append user question
    st.session_state.messages.append({"role": "user", "content": user_question})

    # 2) First OpenAI call
    resp = ask_openai(st.session_state.messages)
    msg = resp.choices[0].message  # ChatCompletionMessage object

    # 3) If OpenAI asked for a function call
    if msg.function_call is not None:
        func_name = msg.function_call.name
        func_args = json.loads(msg.function_call.arguments)

        # 4) Execute the function, but don’t display its raw JSON
        try:
            if func_name == "execute_sql":
                rows = execute_sql(func_args["query"])
                func_response = json.dumps(rows)

            elif func_name == "make_plot":
                rows = execute_sql(func_args["query"])
                img_path = make_plot(rows, func_args["config"])
                # Show only the image, not the JSON
                st.image(img_path, use_column_width=True)
                func_response = json.dumps({"plot_path": img_path})

            else:
                st.error(f"Unknown function `{func_name}` requested.")
                return

        except Exception as e:
            st.error(f"Error during `{func_name}`: {e}")
            return

        # 5) Feed the function result back to the LLM
        st.session_state.messages.append({
            "role": "assistant",
            "content": None,
            "function_call": {
                "name": func_name,
                "arguments": msg.function_call.arguments
            }
        })
        st.session_state.messages.append({
            "role": "function",
            "name": func_name,
            "content": func_response
        })

        # 6) Finalize with one more LLM call and display only its text
        final = ask_openai(st.session_state.messages)
        final_msg = final.choices[0].message
        st.write(final_msg.content)
        st.session_state.messages.append({"role": final_msg.role, "content": final_msg.content})

    else:
        # No function call → display the direct assistant reply
        st.write(msg.content)
        st.session_state.messages.append({"role": msg.role, "content": msg.content})


# In your main Streamlit code:
if "messages" not in st.session_state:
    st.session_state.messages = []

user_q = st.text_input("Ask a question about the database:")
if st.button("Submit") and user_q:
    handle_query(user_q)
