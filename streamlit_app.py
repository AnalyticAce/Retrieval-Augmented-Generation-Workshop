import streamlit as st
import os
from core import (
    load_environment_variables,
    authenticate_huggingface,
    load_and_split_documents,
    create_vector_store,
    get_deepseek_llm,
    create_qa_chain,
    ask_question
)

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="assets/image.png",
    layout="centered"
)

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "Welcome to the AI Document Assistant! Upload a PDF document to get started."
    }]

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

with st.sidebar:
    st.image("assets/langchain.png", width=250)
    st.title("Document Upload")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        with open("temp_upload.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                try:
                    hf_token, deepseek_api_key, deepseek_api_base = load_environment_variables()
                    authenticate_huggingface(hf_token)
                    
                    chunks = load_and_split_documents("temp_upload.pdf")
                    vectorstore = create_vector_store(chunks)
                    llm = get_deepseek_llm(deepseek_api_key, deepseek_api_base)
                    qa_chain = create_qa_chain(llm, vectorstore)
                    
                    st.session_state.uploaded_file = uploaded_file.name
                    st.session_state.vectorstore = vectorstore
                    st.session_state.qa_chain = qa_chain
                    
                    st.success(f"✅ Successfully processed '{uploaded_file.name}'!")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"I've processed '{uploaded_file.name}'. You can now ask questions about it!"
                    })
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")

    if st.session_state.uploaded_file:
        st.info(f"Current document: {st.session_state.uploaded_file}")

st.title("AI Document Assistant")

for message in st.session_state.messages:
    avatar = "assets/image.png" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])

def pipeline(prompt):
    if st.session_state.qa_chain is None:
        return "Please upload and process a document first."
    
    response = ask_question(st.session_state.qa_chain, prompt)
    return response["result"]

if prompt := st.chat_input("Ask about the uploaded document..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="assets/image.png"):
        with st.spinner("Searching knowledge base..."):
            response = pipeline(prompt)
            st.write(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

if os.path.exists("temp_upload.pdf"):
    try:
        os.remove("temp_upload.pdf")
    except:
        pass