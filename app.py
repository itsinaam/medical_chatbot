from flask import Flask, render_template, request
from dotenv import load_dotenv
import os

# Corrected Imports
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate

# Local imports
from src.prompt import system_prompt
from src.helper import download_hugging_face_embeddings

# Initialize Flask App
app = Flask(__name__)

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Set environment variables
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Load embeddings
embeddings = download_hugging_face_embeddings()

# Define Pinecone index
index_name = "medicalbot-1"
docsearch = Pinecone.from_existing_index(index_name=index_name, embedding=embeddings)
retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# Define OpenAI LLM
llm = OpenAI(temperature=0.4, max_tokens=500)

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

@app.route("/")
def index():
    return render_template('chat.html')

@app.route("/get", methods=["POST"])
def chat():
    msg = request.form["msg"]
    print(f"User Input: {msg}")

    # Retrieve relevant documents from Pinecone
    retrieved_docs = retriever.get_relevant_documents(msg)
    print(retrieved_docs)
    # Check if relevant documents exist
    if not retrieved_docs:
        print("No relevant context found in Pinecone.")
        return "please ask relevant questions according to Medical Book!..."

    # Extract the context from retrieved docs
    context = "\n".join([doc.page_content for doc in retrieved_docs])

    # Construct final prompt with context
    formatted_prompt = prompt.format(context=context, input=msg)

    # Generate response using OpenAI
    response = llm.invoke(formatted_prompt)
    print("Response:", response)

    return response

# Run Flask App
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
