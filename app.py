from flask import Flask, request, jsonify, render_template
from langchain_ollama import ChatOllama
import shutil
import atexit
from document_loader import DataLoader
from text_splitter import TextSplitter
from vector_store import VectorStore
from rag_chain import Chain
from flask_cors import CORS
from langchain_community.vectorstores import FAISS

import os
import sys

# Configure Flask to not watch TensorFlow files for changes
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"
extra_dirs = ['templates', 'static']  # Only watch these directories
extra_files = extra_dirs[:]

# Vector store path
VECTOR_PATH = './Vector_store'

# Register cleanup function on shutdown
def clean_up_on_exit():
    # Clear the vector store
    vector_store = VectorStore()
    vector_store.clear_vectors()
    
    # Clear the data folder
    data_folder = os.path.join(os.getcwd(), 'data')
    if os.path.exists(data_folder):
        for file in os.listdir(data_folder):
            file_path = os.path.join(data_folder, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {str(e)}")
    
    print("✅ Cleanup completed on exit.")

atexit.register(clean_up_on_exit)



# Vector store path
VECTOR_PATH = './Vector_store'

# Initialize LLM and Flask
llm = ChatOllama(model="llama3.2")
app = Flask(__name__)
CORS(app)

# Upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Static folder for JavaScript
os.makedirs(os.path.join(os.getcwd(), 'static'), exist_ok=True)

# Initialize vector store
vector_store = VectorStore()
chain_builder = Chain()
chain = None

@app.route('/')
def index():
    return render_template('index.html')






@app.route('/upload', methods=['POST'])
def upload_file():
    global chain

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Process the file
        try:
            process_file(filepath)
        except Exception as e:
            return jsonify({'error': f'File processing error: {str(e)}'}), 500

        # Delete the file after processing
        os.remove(filepath)

        return jsonify({'message': f'{file.filename} uploaded and processed successfully!'}), 200
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500







def process_file(filepath):
    global chain

    try:
        # Check if Ollama is responsive
        try:
            # Simple test to see if Ollama is working
            test_result = llm.invoke("test")
            if not test_result:
                raise Exception("Ollama LLM not responding")
        except Exception as llm_err:
            raise Exception(f"LLM connection error: {str(llm_err)}")
            
        # Rest of your function with added logging...
        print(f"Loading file: {filepath}")
        loader = DataLoader(folder_path=app.config['UPLOAD_FOLDER'])
        documents = loader.load_file([filepath])
        
        print(f"Documents loaded: {len(documents) if documents else 0}")
        if not documents or len(documents) == 0:
            raise Exception("No content extracted from document")
            
        print("Splitting text...")
        splitter = TextSplitter()
        chunks = splitter.split_text(documents)
        print(f"Created {len(chunks)} chunks")
        
        print("Creating vector store...")
        db = vector_store.get_vectors(chunks)
        
        print("Building chain...")
        chain = chain_builder.build_chain(vector_db=db)
        print("Processing complete!")
    except Exception as e:
        print(f"Error processing file {filepath}: {str(e)}")
        raise e






@app.route('/ask', methods=['POST'])
def ask():
    global chain

    data = request.get_json()
    question = data.get('question', '')

    if question == "system_check":
        try:
            db = vector_store.load_existing_vectors()
            if db:
                chain = chain_builder.build_chain(vector_db=db)
                return jsonify({'status': 'ready'}), 200
            else:
                return jsonify({'status': 'no_knowledge_base'}), 200
        except Exception:
            return jsonify({'status': 'no_knowledge_base'}), 200

    try:
        if not chain:
            db = vector_store.load_existing_vectors()
            if db:
                chain = chain_builder.build_chain(vector_db=db)

        if chain:
            response = chain.invoke({"question": question})
        else:
            response = llm.invoke(question)

        # ✅ Ensure response is serializable
        answer = response.content if hasattr(response, 'content') else str(response)

        return jsonify({'answer': answer}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

