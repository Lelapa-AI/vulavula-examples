import os
from client.vulavula_client import VulavulaClient
from domain.schema.knowledgebase import *


# Main entry point for the script
if __name__ == "__main__":
    # Path to the document to be uploaded to the knowledgebase
    document_file_path = "data/Jackson-1995-The-world-and-the-machine.pdf"

    # Initialize the VulavulaClient with an API key from the environment variables
    # Ensure the "VULAVULA_API_KEY" environment variable is set before running the script
    vulavula_client = VulavulaClient(vulavula_api_key=os.getenv("VULAVULA_API_KEY"))

    # Define the knowledgebase creation request with the name of the knowledgebase
    knowledgebase_create_request = KnowledgebaseCreateRequest(
        knowledgebase_name="The world and the machine"
    )

    print("Creating knowledgebase...\n")
    # Send the request to create a new knowledgebase and store the response
    knowledgebase_create_response = vulavula_client.create_knowledge_base(
        knowledgebase_create_request=knowledgebase_create_request
    )

    print("Adding document to knowledgebase...\n")
    # Upload the document file to the created knowledgebase
    # The document is associated with the ID of the newly created knowledgebase
    knowledgebase_document_response = vulavula_client.add_document_to_knowledgebase(
        knowledgebase_id=knowledgebase_create_response.id,
        file_path=document_file_path
    )

    # Define a query to search the knowledgebase
    # The query is designed to retrieve specific information related to the document
    knowledgebase_query = KnowledgebaseQuery(
        query="What is the purpose of the machine relative to the world?"
    )

    print("Querying knowledgebase...\n")
    # Execute the query against the knowledgebase and store the results
    knowledgebase_query_response = vulavula_client.query_knowledgebase(
        knowledgebase_id=knowledgebase_create_response.id,
        query=knowledgebase_query
    )

    print("Displaying results of the knowledgebase search...\n\n")
    # Iterate over the search results and print the text and confidence score for each result
    for result in knowledgebase_query_response.search_results:
        print(result.text)
        print(f"*** Confidence score \t{result.score} ***\n\n")

    # Clean up: delete the created knowledgebase and associated documents to free up resources
    print("Now deleting the knowledgebase...")
    vulavula_client.delete_knowledgebase(knowledgebase_id=knowledgebase_create_response.id)