
from agno.knowledge.reader.pdf_reader import PDFReader
import os

def test_pdf_reader():
    filename = "test_doc.pdf"
    # create_dummy_pdf(filename) # Using downloaded file
    
    try:
        reader = PDFReader()
        docs = reader.read(filename)
        print(f"Read {len(docs)} documents.")
        for doc in docs:
            print("Content:", doc.content)
    except Exception as e:
        print(f"Error reading PDF: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_pdf_reader()
