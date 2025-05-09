import os
import json
import openai
from pinecone import Pinecone, ServerlessSpec
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
from utils.flatten_dict import flatten_dict
from typing import Optional, List
from pydantic import BaseModel

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class AtHearthResponse(BaseModel):
    response: str
    generate_query: bool
    metadata_query: Optional[str] = None

def chatbot(user_query, index, st):
    try:
        # Create embedding for the user's query
        openai.api_key = OPENAI_API_KEY
        query_response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=user_query
        )
        system_message = """If the user's question is about cheese and you need to generate a pinecone vectorDB metadata query filter to search for the cheese,
        1. Set generate_query to True
        2. Set metadata_query to the query that you need to search for the cheese.
        3. If the user's question is not about cheese, set generate_query to False and metadata_query to None.
        4. If the user's question is about cheese, but you don't need to search for the cheese, set generate_query to False and metadata_query to None.

        The fields you need to make the correct matadata query filter are as follows:
        - brand
        - KPU
        - UPC
        - case_weight(weight of case, example: 10 lbs) 
        - case_count(count of case, example: 2 Eaches)
        - each_weight(weight of each, example: 5 LBS)
        - case_price(price of case, example: $49.06)
        - each_price(price of each, example: $19.06)
        - case_price_per_lb(price per pound of case, example: $4.91/lb)
        - each_price_per_lb(price per pound of each, example: $4.91/lb)

        VALID FILTER EXAMPLES:
        1. Single condition:
        {"brand": {"$eq": "Kraft"}}
        {"case_price": {"$lt": 50.00}}
        {"case_weight": {"$gte": 5}}

        2. Multiple conditions using AND:
        {
            "$and": [
            {"brand": {"$eq": "Kraft"}},
            {"case_price": {"$lt": 50.00}}
            ]
        }

        3. Multiple conditions using OR:
        {
            "$or": [
            {"brand": {"$eq": "Kraft"}},
            {"brand": {"$eq": "Sargento"}}
            ]
        }

        4. Range queries:
        {"each_price": {"$gte": 20, "$lte": 50}}

        INVALID FILTERS TO AVOID:
        ❌ {"brand": ["Kraft", "Sargento"]}  # Don't use direct arrays
        ❌ {"brand": {"$eq": ["Kraft", "Sargento"]}}  # Don't use arrays with $eq
        ❌ {"metadata.brand": {"$eq": "Kraft"}}  # Don't include "metadata." prefix

        Available operators:
        - $eq: Equal to
        - $ne: Not equal to
        - $gt: Greater than
        - $gte: Greater than or equal to
        - $lt: Less than
        - $lte: Less than or equal to
        - $in: In array of values
        - $nin: Not in array of values
        - $exists: Field exists
        - $and: Logical AND
        - $or: Logical OR

        Always return properly formatted JSON for metadata_query. Keep filters simple and avoid nesting too deeply.
        - If the question is superative adjective, you need to set the relevant query threshold for your self and generate the query but it becomes have data in the metadata(price:smallest:5, biggest:180).
        - If the question is about the cheese, you need to generate the query for each item (price: each_price, weight: each_weight, price per pound: each_price_per_lb).
        """

        completion = openai.beta.chat.completions.parse(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_query}
            ],
            response_format=AtHearthResponse
        )
        
        response = completion.choices[0].message.parsed
        print(response.metadata_query)
        query_embedding = query_response.data[0].embedding
        # response = None
        # Query Pinecone
        try:
            if response.generate_query:
                query_results = index.query(
                    vector=query_embedding,
                    top_k=98,
                    include_metadata=True,
                    namespace="cheeseData",
                    # filter={
                    #     "metadata.category": response.metadata_query
                    # }
                    # filter=json.loads(response.metadata_query)
            
                )
            else:
                query_results = index.query(
                    vector=query_embedding,
                    top_k=30,
                    include_metadata=True,
                    namespace="cheeseData",
                    )
        except Exception as e:
            print(e)
            query_results = index.query(
                vector=query_embedding,
                top_k=30,
                include_metadata=True,
                namespace="cheeseData",
                )
        # Format context from the results
        context = ""
        for match in query_results['matches']:
            metadata = match['metadata']
            context += flatten_dict(metadata)
            context += "---\n"
        previous_messages = ', '.join(f"{msg['role']}:{msg['content']}" for msg in st.session_state.messages)
        # Create prompt for OpenAI
        prompt = f"""You are a helpful cheese expert assistant. Use the following cheese product information to answer the question.
- So, for the question, you need to find the cheese that the user is asking about. And you need to show the images for the cheese using the image url. 
- Also you don't need to show all data of the cheese. Show the Description, image, Category, Case and Each Price, Each Price per pound and the url of the cheese. And in the url of the cheese, unnecessary strign '-' or '---' and so on and added so you need to remove it. Also, don't show url directly, show "View More" instead.
- If show the relate items, don't show the image.
- The unit of the price is dollar and the unit of the price per pound is dollar per pound and the unit of the weight is pound.
- Please provide a helpful, informative response based on the cheese products shown above. If the question cannot be answered based on the given context, please say so.
- And When a greeting such as hi and hello or general conversation comes in as a question, you need to answer with a greeting but not show the cheese data.
- But with a greeting, the question is also about cheese, you need to answer with cheese data.
- And If the content of the question is not related to cheese, you need to deal with it as a general conversation actively with a knowledge you know.
- Be concise, but provide all relevant details found in the context.
- Do not repeat yourself or include unnecessary sentences.
- Use bullet points or lists if the user asks for comparisons or recommendations.
- Answer the pros and cons of  each cheese briefly.
- If the user asks for a specific cheese, provide the details of the cheese.
- If the user asks for a general cheese recommendation, consider the cheese's flavor, texture, and aroma.
- Maintain a friendly and knowledgeable tone.
- If the user asks about something outside of cheese, ask them to provide a cheese-related question.
- If the answer is partial, offer to help further if the user can clarify their preferences.
- Briefly explain why you made a recommendation, using facts from the context (e.g., "I recommend Mozzarella because it is described here as mild and melts well.")
- Suggest similar cheeses only if they are present in the context.
- If the user's preferences are not fully met by any product, recommend the closest option found.
- Usually show 3 cheese. If the number of cheese products is too much, reduce you self from 3 products to 5 products with the most suitable products and if user want to see more, you need to show all products.
- When output, Correct the writing of space between words.
- It there is no cheese data, you need to answer with "I'm sorry, There is no cheese data for that question."
- Answer the question based on the context and previous messages.  
Context:
{context}
Previous Messages:
{previous_messages}
Question: {user_query}
"""

        # Get response from OpenAI
        chat = ChatOpenAI(
            model="gpt-4.1",
            temperature=0.7,
            openai_api_key=OPENAI_API_KEY
        )
        response = chat.invoke(prompt)
        
        return response.content

    except Exception as e:
        st.error(f"Error in query_and_respond: {e}")
        return "I apologize, but I encountered an error. Please try asking your question differently."
