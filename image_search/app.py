import pretty_errors
from jina import Flow, DocumentArray, Document
from jina.types.document.generators import from_files
from executors import ProcessFile
import os
import sys

NUM_DOCS = 10000
FORMATS = ["jpg", "png"]
DATADIR = "data"

flow = (
    Flow()
    .add(uses=ProcessFile, name="processor") # Embed image in doc, not just filename
    .add(
        uses="jinahub+docker://ImageNormalizer",
        name="crafter",
        uses_with={"target_size": 40},
    )
    .add(
        uses="jinahub+docker://BigTransferEncoder",
        uses_with={"model_name": "Imagenet1k/R50x1", "model_path": "model"},
        uses_metas={"workspace": "workspace"},
        name="image_encoder",
        volumes="./data:/encoder/data",
    )
    .add(
        uses="jinahub+docker://SimpleIndexer",
        uses_with={"index_file_name": "index"},
        uses_metas={"workspace": "workspace"},
        name="image_indexer",
        volumes="./workspace:/workspace/workspace",
    )
)

def generate_docs(directory, num_docs=NUM_DOCS, formats=FORMATS):
    docs = DocumentArray()
    for format in formats:
        docarray = DocumentArray(from_files(f"{directory}/**/*.{format}", size=num_docs))
        docs.extend(docarray)

    return docs[:num_docs]
        

def index():
    if os.path.exists("workspace"):
        print("'workspace' folder exists. Please delete")
        sys.exit()

    docs = generate_docs(DATADIR, NUM_DOCS)

    with flow:
        flow.index(inputs=docs, show_progress=True)


def query_restful():
    flow.protocol = "http"
    flow.port_expose = 12345

    with flow:
        flow.block()


if len(sys.argv) < 1:
    print("Supported arguments: index, query_restful, query_grpc")
if sys.argv[1] == "index":
    index()
elif sys.argv[1] == "query_restful":
    query_restful()
else:
    print("Supported arguments: index, query_restful")
