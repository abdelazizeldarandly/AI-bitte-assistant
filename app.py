import streamlit as st
from dotenv import load_dotenv
from typing import List , Dict , Any
import os
import base64
from openai import OpenAI

load_dotenv()

st.set_page_config(
    page_title="bitte RAG chatbot",
    page_icon=":material/chat_bubble:",
    layout="centered",
)

st.title("bitte RAG chatbot")
st.write("Your intelligent RAG assistant")
st.divider()

with st.expander("About this web app", expanded=False):
    st.markdown(
        """
        This is a Streamlit app scaffold for your RAG chatbot.
        Add your OpenAI + retrieval logic in this file, then rerun the app.
        """
    )

st.info("UI is loading correctly. Next step: connect your chat logic.")

# retrieve the credentials
openai_api_key = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")
try:
    if not openai_api_key:
        openai_api_key = st.secrets["OPENAI_API_KEY"]
    if not VECTOR_STORE_ID:
        VECTOR_STORE_ID = st.secrets["VECTOR_STORE_ID"]
except Exception:
    pass

#set the openai key is the os
if openai_api_key:
    os.environ["OPENAI_API_KEY"] = openai_api_key

# initialize the openai client
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# warn if openai api key or vector store id are not set
if not openai_api_key:
    st.warning("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable or add it to the Streamlit secrets.")
if not VECTOR_STORE_ID:
    st.warning("Vector store ID is not set. Please set the VECTOR_STORE_ID environment variable or add it to the Streamlit secrets.")

# configuriation of system prompt
system_prompt = """
You are a toxic ceo that can answer questions:
"""

# store the previouse responce id
if "previous_response_id" not in st.session_state:
    st.session_state.previous_response_id = None

# initalize the chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# create a sidebar with user control
with st.sidebar:
    st.header("User Control")
    st.divider()
# clear the conversation history - reset the chat history
    if st.button("Clear Conversation History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.previous_response_id = None
        # reset the page
        st.rerun()


# helper function
def bulid_input_parts(text:str, images : List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    """
    bulid the input parts array for the openai from the text and images.

      Args:
         text: the text to be sent to the opeanai
         image:the image to be sent to the openai

      Returns:
          a list of input parts compatiable with the opeanai responsec api       
    """
    content = []
    if text and text.strip():
        content.append({
            "type":"input_text",
            "text":text.strip()
        })
    for img in images:
        content.append({
            "type":"input_image",
            "image_url":img["data_url"],
        })
    return [{"type":"message","role":"user","content":content}] if content else []


# user interface (the input) - upload image
uploaded_files = st.file_uploader("Upload images", type=["png", "jpg", "jpeg","webp"], accept_multiple_files=True)
# user interface (the input) - chat input
prompt = st.chat_input("Enter your message here")

# render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt is not None:
    #process the images into a api compatible format
    images = [
        {
            "mime_type": f.type or "image/png",
            "data_url": f"data:{(f.type or 'image/png')};base64,{base64.b64encode(f.read()).decode('utf-8')}"
        } for f in uploaded_files or []
    ]

    # show and store the user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    input_parts = bulid_input_parts(prompt, images)

    # generate assistant reply with visible "thinking" state
    with st.chat_message("assistant"):
        thinking_box = st.empty()
        thinking_box.info("Thinking... analyzing your message.")

        if client is None:
            assistant_text = "I received your message, but OPENAI_API_KEY is missing."
        else:
            try:
                with st.spinner("Generating response..."):
                    response = client.responses.create(
                        model="gpt-4.1-mini",
                        input=input_parts,
                        instructions=system_prompt,
                        previous_response_id=st.session_state.previous_response_id,
                    )
                assistant_text = response.output_text or "I could not generate a response."
                st.session_state.previous_response_id = response.id
            except Exception as e:
                assistant_text = f"Error generating response: {e}"

        thinking_box.empty()
        st.markdown(assistant_text)

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
