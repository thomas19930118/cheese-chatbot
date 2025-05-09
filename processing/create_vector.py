import os
import json
import openai
import uuid
from pinecone import Pinecone, ServerlessSpec
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
from utils.flatten_dict import flatten_dict
from utils.flatten_pinecone_metadata import flatten_pinecone_metadata

load_dotenv()

# Get API keys from environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



def load_cheese_data(file_path):
    print("Loading cheese data...")
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def initialize_pinecone():
    print("Initializing Pinecone...")
    try:
        pc = Pinecone(
            api_key=PINECONE_API_KEY
        )
        
        index_name = "cheese-index"
        dimension = 1536
        
        if index_name not in pc.list_indexes().names():
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        
        return pc.Index(index_name)
    except Exception as e:
        print(f"An error occurred in initialize_pinecone: {e}")
        raise

def create_embeddings_and_store(cheese_data, index):
    print("Creating embeddings and storing in Pinecone...")
    try:
        # Initialize embeddings with explicit API key
        openai.api_key = OPENAI_API_KEY
        
        # Prepare texts and metadata
        vectors = []
        for cheese_item in cheese_data:
            # Create a descriptive text from the cheese item properties
            cheese_text = flatten_dict(flatten_pinecone_metadata(cheese_item))
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=cheese_text
            )
            
            # Get the embedding from the response
            embedding = response.data[0].embedding
            print(embedding)
            # Create vector with metadata
            vectors.append({
                "id": str(uuid.uuid4()),
                "values": embedding,
                "metadata": flatten_pinecone_metadata(cheese_item)
            })
    
        # Use the index directly as it's already initialized
        index.upsert(vectors=vectors, namespace="cheeseData")

        print(f"Successfully stored {len(vectors)} cheese entries in Pinecone")
        return vectors
    except Exception as e:
        print(f"An error occurred in create_embeddings_and_store: {e}")
        raise

def create_vector():
    # First make sure we have the cheese data
    cheese_data = load_cheese_data('./data/cheese_products.json')
    if not cheese_data:
        print("Please run your cheese scraping script first to create cheese_data.json")
        return

    # Initialize Pinecone
    index = initialize_pinecone()
    if not index:
        return
    
    # Check if vectors need to be created and stored
    vector_store = create_embeddings_and_store(cheese_data, index)
    if not vector_store:
        return
    print("Setup completed successfully!")

if __name__ == "__main__":
    create_vector()


