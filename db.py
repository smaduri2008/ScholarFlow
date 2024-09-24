from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from bson import json_util
import numpy as np
from pymongo.operations import SearchIndexModel
from cerebras.cloud.sdk import Cerebras
import json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

llm_client = Cerebras(api_key="csk-5v5356rv35fdnc6ycnj2rvyf9n35wtr56mdek5e442ktk68k")

uri = "mongodb+srv://sahasmaduri:ajayavasi@penn.vuicg.mongodb.net/?retryWrites=true&w=majority&appName=Penn"
database_name = "pennapps"

client = MongoClient(uri, server_api=ServerApi('1'))
database = client[database_name]

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


def add_document(collection_name, document):
    collection = database[collection_name]
    collection.insert_one(document)


def get_document(collection_name, query):
    collection = database[collection_name]
    return collection.find_one(query)


def get_documents(collection_name, query):
    collection = database[collection_name]
    return collection.find(query)


def find_user_by_username(username):
    return get_document("users", {"username": username})


def login_successful(username, password):
    return get_document("users", {"username": username, "password": password}) is not None


def find_document_by_name(title):
    return get_document("articles", {"title": title})


def find_random_document():
    docs = []
    for doc in database["articles"].aggregate([{"$sample": {"size": 1}}]):
        docs.append(doc)
    return docs[0]

def update_user_likes(username, article_id):
    database.users.update_one({"username": username}, {"$addToSet": {"likes": article_id}})

def update_user_dislikes(username, article_id):
    database.users.update_one({"username": username}, {"$addToSet": {"dislikes": article_id}})

def get_account_from_id(account_id):
    return get_document("users", {"_id": ObjectId(account_id)})


def get_article_from_id(article_id):
    return get_document("articles", {"_id": ObjectId(article_id)})


def get_pref_vector(account_id):
    acc_info = get_account_from_id(account_id)
    alpha = 0.1
    likes = acc_info["likes"]
    dislikes = acc_info["dislikes"]
    if len(likes) == 0 or len(dislikes) == 0:
        return None
    np_matrix_arr_likes = []
    for like in likes:
        article = get_article_from_id(like)
        np_matrix_arr_likes.append(article["vector"])
    np_matrix_arr_likes = np.array(np_matrix_arr_likes)
    mean_like_vector = np.mean(np_matrix_arr_likes, axis=0)
    np_matrix_arr_dislikes = []
    for dislike in dislikes:
        article = get_article_from_id(dislike)
        np_matrix_arr_dislikes.append(article["vector"])
    np_matrix_arr_dislikes = np.array(np_matrix_arr_dislikes)
    mean_dislike_vector = np.mean(np_matrix_arr_dislikes, axis=0)
    return (mean_like_vector + (mean_like_vector - mean_dislike_vector) * alpha).tolist()


def get_articles_you_may_like(account_id, k):
    pref_vector = get_pref_vector(account_id)
    if pref_vector is None:
        return None
    pipeline = [
        {
            "$vectorSearch": {
                "index": "v_index",
                "queryVector": pref_vector,
                "path": "vector",
                "exact": False,
                "limit": k,
                "numCandidates": min(k * 10, 500)
            }
        },
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "description": 1,
                "author": 1,
                "link": 1,
                "author_scholar_id": 1,
                "college": 1,
                "author_homepage": 1,
                "score": {
                    "$meta": "vectorSearchScore"
                }
            }
        }
    ]
    # Execute the search
    results = database["articles"].aggregate(pipeline)
    return list(results)

def get_key_words(sentence):
    chat_completion = llm_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f'Extract all keywords from these sentences:"{sentence}". Put all important words in a list that should be used for a similarity search. "Research papers" are not important words. Only return that in a format like "keyword1 keyword2 keyword 3". DO NOT SAY ANYTHING ELSE',
            }
        ],
        model="llama3.1-8b",
    )
    text = chat_completion.to_dict()["choices"][0]["message"]["content"]
    return text

def get_summary(sentence):
    chat_completion = llm_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f'Give me a summary of the following sentences:"{sentence}". Do not give me any other information or instruction other than the summary itself',
            }
        ],
        model="llama3.1-8b",
    )
    text = chat_completion.to_dict()["choices"][0]["message"]["content"]
    return text

def RAG_retrival(query, k_documents=5):
    key_words = get_key_words(query)
    summary = get_summary(query)
    full_query = f"{key_words} {summary}"
    print(full_query)
    vector = model.encode(full_query)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "v_index",
                "queryVector": vector.tolist(),
                "path": "vector",
                "exact": False,
                "limit": k_documents,
                "numCandidates": 500
            }
        },
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "description": 1,
                "author": 1,
                "link": 1,
                "author_scholar_id": 1,
                "college": 1,
                "author_homepage": 1,
                "score": {
                    "$meta": "vectorSearchScore"
                }
            }
        }
    ]

    results = database["articles"].aggregate(pipeline)
    return list(results)

def llm_response(query, message_history):

    context = RAG_retrival(f'{query} - {str(message_history)}')
    expanded_query = f"Answer the query below by using the context provided.\nUser Query: {query}\nContext: {str(context)}\nUse the context to find a specific answer to the query. Do not explicitly state that you are taking information from the context. Additionally, provide the user with links and names. However, if the user does not seem to be asking about research papers, do not provide unnecessary information and act like a normal LLM assistant. If there is a link, put it in a 'a' tag from html. So put it like: <a href='link'>Link name</a>."
    message_history.append({
        "role": "user",
        "content": expanded_query,
    })
    chat_completion = llm_client.chat.completions.create(
        messages=message_history,
        model="llama3.1-8b",
    )
    text = chat_completion.to_dict()["choices"][0]["message"]["content"]

    return [{"role":"user", "content":query},{"role":"assistant", "content":text}]