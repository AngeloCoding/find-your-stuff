import streamlit as st
import json
from openai_client import ask_openai, SYSTEM_PROMPT
from utils import execute_sql, make_plot


few_shot_examples = [
    {
        "question": "Wie viele Gegenstände wurden um 7 Uhr gefunden?",
        "answer": "SELECT count(*) AS count FROM Gegenstand WHERE strftime('%H', FundDatum) = '19';",
    },
    {
        "question": "In welchem Monat wurden die meisten Gegenstände verloren?",
        "answer": "SELECT strftime('%Y-%m', g.FundDatum) AS Monat, COUNT(*) AS AnzahlVerloren FROM Gegenstand g JOIN PersonGegenstand pg ON g.gid = pg.idGGST WHERE pg.FinderVerlierer = 0 GROUP BY Monat ORDER BY AnzahlVerloren DESC LIMIT 1;",
    },
    {
        "question": "Wie viele Gegenstände wurden im Jahr 2020 gefunden?",
        "answer": "SELECT COUNT(*) AS AnzahlGefunden FROM Gegenstand WHERE strftime('%Y', FundDatum) = '2020';",
    },
    {
        "question": "Welche Subkategorie hat die meisten Funde?",
        "answer": "SELECT sk.Beschreibung AS Subkategorie, COUNT(*) AS Anzahl FROM Gegenstand g JOIN SubKategorie sk ON g.idSubkategorie = sk.skid GROUP BY sk.Beschreibung ORDER BY Anzahl DESC LIMIT 1;",
    },
    {
        "question": "Wie viele Smartphones wurden gefunden, die von Swisscom sind?",
        "answer": "SELECT COUNT(*) AS AnzahlSmartphones FROM Gegenstand WHERE Natel = 1 AND NatelProvider = 'Swisscom';",
    },
    {
        "question": "Wie viele Velos wurden gefunden?",
        "answer": "SELECT COUNT(*) AS AnzahlVelos FROM Gegenstand g JOIN SubKategorie sk ON g.idSubkategorie = sk.skid WHERE LOWER(sk.Beschreibung) LIKE '%velo%' OR LOWER(g.Beschreibung) LIKE '%velo%';"
    },
    {
        "question": "Was sind die Top 10 am häufigsten gefundenen Gegenständ",
        "answer": """
            SELECT 
                SK.Beschreibung AS Subkategorie,
                COUNT(*) AS Anzahl
            FROM 
                Gegenstand G
            JOIN 
                SubKategorie SK ON G.idSubkategorie = SK.skid
            GROUP BY 
                SK.Beschreibung
            ORDER BY 
                COUNT(*) DESC
            LIMIT 10;
        """,
    }
]


st.title('SQLite QA Agent')

if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Add few-shot examples as conversation turns
    for example in few_shot_examples:
        # User provides the example answer
        st.session_state.messages.append({"role": "user", "content": f"{example['question']}"})
        # Assistant provides the corresponding expert rating
        st.session_state.messages.append({"role": "assistant", "content": f"{example['answer']}"})

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


def on_submit():
    if st.session_state.user_q:
        handle_query(st.session_state.user_q)


# In your main Streamlit code:
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.form(key="query_form"):
    user_q = st.text_input("Ask a question about the database:", key="user_q")
    submitted = st.form_submit_button("Submit")
if submitted and user_q:
    handle_query(user_q)
