from document_loader import DataLoader
from text_splitter import TextSplitter
from vector_store import VectorStore
from rag_chain import Chain
import os

def main():
    # Check and create data directory if it doesn't exist
    data_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"[INFO] Created data directory at {data_dir}")
    
    # Initialize vector store
    print("[INFO] Initializing vector store...")
    vector_store = VectorStore()
    
    # Try loading existing vectors
    db = vector_store.load_existing_vectors()
    if db:
        print("[INFO] Loaded existing vector store.")
    else:
        # Check if there are files to process
        loader = DataLoader(folder_path=data_dir)
        file_paths = loader.get_docs()
        
        if file_paths:
            print(f"[INFO] Found {len(file_paths)} files to process.")
            documents = loader.load_file(file_paths)
            print(f"[INFO] Loaded {len(documents)} documents.")
            
            # Split documents
            print("[INFO] Splitting documents...")
            splitter = TextSplitter()
            chunks = splitter.split_text(documents)
            print(f"[INFO] Created {len(chunks)} chunks.")
            
            # Create vector store
            print("[INFO] Creating vector store...")
            db = vector_store.get_vectors(chunks)
            
            # Delete processed files
            for file_path in file_paths:
                try:
                    os.remove(file_path)
                    print(f"[INFO] Deleted processed file: {file_path}")
                except Exception as e:
                    print(f"[ERROR] Failed to delete file {file_path}: {str(e)}")
        else:
            print("[INFO] No files found to process.")
    
    # Build RAG chain if we have vectors
    if db:
        print("[INFO] Building RAG chain...")
        chain_builder = Chain()
        chain = chain_builder.build_chain(vector_db=db)
        print("[INFO] System is ready for Q&A.")
        
        # Begin Q&A loop
        print("[INFO] Ask your questions. Type 'exit' to quit.")
        while True:
            user_input = input("\nAsk a question: ")
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            
            response = chain.invoke(user_input)
            print(f"\n[Answer]: {response}")
    else:
        print("[INFO] No vector database available. Please add documents to the 'data' folder.")

if __name__ == "__main__":
    main()