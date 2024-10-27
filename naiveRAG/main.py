from dotenv import load_dotenv
load_dotenv()
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
import requests
import os
import json
from pinecone import Pinecone

# Parsing the PDF file
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

parser = LlamaParse(
    result_type="markdown",
)

file_extractor = {".pdf": parser}
output_docs = SimpleDirectoryReader(
    input_files=['./data/Git CheatSheet.pdf'], file_extractor=file_extractor
)
docs = output_docs.load_data()
md_text = ""
for doc in docs:
    md_text += doc.text

with open("output.md", "w") as file_handle:
    file_handle.write(md_text)

print("Markdown file created successfully")

chunk_size = 1000
overlap = 200


# Chunking the parsed markdown
def fixed_size_chunking(text, chunk_size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


chunks = fixed_size_chunking(md_text, chunk_size, overlap)
print("Number of chunks:", len(chunks))
print(f"Number of chunks: {len(chunks)}")

# Embedding
jina_api_key = os.getenv("JINA_API_KEY")
headers = {
    "Authorization": f"Bearer {jina_api_key}",
    "Content-Type": "application/json",
}
url = "https://api.jina.ai/v1/embeddings"

embedded_chunks = []
for chunk in chunks:
    payload = {"input": chunk, "model": "jina-embeddings-v3"}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        embedded_chunks.append(response.json()["data"][0]["embedding"])
    else:
        print("Error during the embedding process")

output_file = "embedded_chunks.json"
data = {"chunks": chunks, "embeddings": embedded_chunks}

with open(output_file, "w") as f:
    json.dump(data, f)
print(f"Embedded chunks saved to {output_file}")

#Pinecone Integration
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index_name = "pesuio-naive-rag"  # Replace with your preferred index name

# Create index if it doesn't exist
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=768,  # Dimension of Jina embeddings
        metric='cosine'
    )

index = pc.Index(index_name)

# Prepare and upload vectors
vectors_to_upsert = [
    {
        'id': f'chunk_{i}',
        'values': embedding,
        'metadata': {'text': chunk}
    }
    for i, (chunk, embedding) in enumerate(zip(chunks, embedded_chunks))
]

index.upsert(vectors=vectors_to_upsert)
print(f"Uploaded {len(vectors_to_upsert)} vectors to Pinecone")