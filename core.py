from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from huggingface_hub import login
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import os


def load_environment_variables():
    """Load and validate environment variables."""
    load_dotenv()
    
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1" 
    
    hf_token = os.getenv("HF_TOKEN")
    if hf_token is None:
        raise ValueError("HF_TOKEN is not set in the environment variables.")
    
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_api_key is None:
        raise ValueError("DEEPSEEK_API_KEY is not set in the environment variables.")
    
    deepseek_api_base = os.getenv("DEEPSEEK_API_BASE")
    if deepseek_api_base is None:
        raise ValueError("DEEPSEEK_API_BASE is not set in the environment variables.")
    
    return hf_token, deepseek_api_key, deepseek_api_base

def authenticate_huggingface(token):
    """Login to HuggingFace."""
    login(token=token, add_to_git_credential=False)

def load_and_split_documents(pdf_path, chunk_size=10000, chunk_overlap=200):
    """Load PDF and split into chunks."""
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(pages)
    
    return chunks

def create_vector_store(chunks):
    """Create embeddings and vector store."""
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    return vectorstore

def get_deepseek_llm(api_key, api_base, temperature=1.3, max_tokens=500):
    """Configure the DeepSeek LLM."""
    return ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=api_key,
        openai_api_base=api_base,
        temperature=temperature,
        max_tokens=max_tokens
    )

def create_qa_chain(llm, vectorstore):
    """Create the RAG pipeline for question answering."""
    return RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

def ask_question(qa_chain, query):
    """Run a query through the QA chain."""
    return qa_chain.invoke(query)

def pipeline(filename="data/B-SVR-500_project.pdf", user_query="What is the goal of the project in two-three small sentences"):
    """Main function to run the entire pipeline."""
    # Step 1: Load environment variables
    hf_token, deepseek_api_key, deepseek_api_base = load_environment_variables()
    
    # Step 2: Authenticate with HuggingFace
    authenticate_huggingface(hf_token)
    
    # Step 3: Load and split documents
    chunks = load_and_split_documents(filename)
    
    # Step 4: Create vector store
    vectorstore = create_vector_store(chunks)
    
    # Step 5: Set up the LLM
    llm = get_deepseek_llm(deepseek_api_key, deepseek_api_base)
    
    # Step 6: Create QA chain
    qa_chain = create_qa_chain(llm, vectorstore)
    
    # Step 7: Ask a question
    response = ask_question(qa_chain, user_query)
    
    return response["result"]

if __name__ == "__main__":
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console()
    console.print(Markdown(pipeline()))
