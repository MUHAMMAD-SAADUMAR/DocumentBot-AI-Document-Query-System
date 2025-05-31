from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import os
import pickle
import shutil

class VectorStore:
    def __init__(self, embedding_model="nomic-embed-text", collection_name="document_collection"):
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.vector_store_path = './Vector_store'
        self.store_file = os.path.join(self.vector_store_path, f"{collection_name}.pkl")
        self.emb_model = OllamaEmbeddings(model=self.embedding_model)
        
        # Ensure vector store directory exists
        if not os.path.exists(self.vector_store_path):
            os.makedirs(self.vector_store_path)

    def get_vectors(self, data_chunks):
        try:
            # Check if collection exists
            if os.path.exists(self.store_file):
                # Load existing DB
                db = self.load_existing_vectors()
                if db and data_chunks:
                    # Get all existing documents and their embeddings
                    existing_docs = list(db.docstore._dict.values())
                    print(f"[INFO] Found {len(existing_docs)} existing documents in the vector store")
                    
                    # Create a new db with both existing and new docs
                    combined_docs = existing_docs + data_chunks
                    print(f"[INFO] Creating a new vector store with {len(combined_docs)} total documents")
                    
                    db = FAISS.from_documents(
                        documents=combined_docs,
                        embedding=self.emb_model
                    )
                    self._save_vectors(db)
                    return db
            
            # Create new vector database if it doesn't exist or couldn't load
            if data_chunks:
                print(f"[INFO] Creating a new vector store with {len(data_chunks)} documents")
                db = FAISS.from_documents(
                    documents=data_chunks,
                    embedding=self.emb_model
                )
                self._save_vectors(db)
                return db
            return None
        except Exception as e:
            print(f"[ERROR] Failed to create vector store: {str(e)}")
            raise

    def load_existing_vectors(self):
        try:
            if os.path.exists(self.store_file):
                with open(self.store_file, "rb") as f:
                    return pickle.load(f)
            return None
        except Exception as e:
            print(f"[ERROR] Failed to load existing vector store: {str(e)}")
            # If loading fails, try to remove corrupted store
            if os.path.exists(self.store_file):
                try:
                    os.remove(self.store_file)
                    print(f"[INFO] Removed corrupted vector store file")
                except:
                    pass
            return None
            
    def _save_vectors(self, db):
        """Save vectors to disk"""
        try:
            with open(self.store_file, "wb") as f:
                pickle.dump(db, f)
            print(f"[INFO] Vector store saved successfully with {len(db.docstore._dict)} documents")
        except Exception as e:
            print(f"[ERROR] Failed to save vector store: {str(e)}")
            
    def clear_vectors(self):
        """Clear the vector store"""
        if os.path.exists(self.store_file):
            try:
                os.remove(self.store_file)
                print(f"[INFO] Vector store cleared")
                return True
            except Exception as e:
                print(f"[ERROR] Failed to clear vector store: {str(e)}")
                return False
        return True