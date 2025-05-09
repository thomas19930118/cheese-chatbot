import os
import streamlit as st
from service.cheese_chatbot import chatbot
from pinecone import Pinecone
from dotenv import load_dotenv
from processing.scraping_cheese import scrape_cheese
from processing.create_vector import create_vector

# Configure the page with custom menu items
st.set_page_config(
    page_title="Cheese Assistant Chatbot",
    page_icon="🧀",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': '''
        ## Cheese Expert Chatbot
        A chatbot that helps you discover and learn about cheeses.
        ''',
    }
)

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Initialize states for process control
if 'show_confirm_reload' not in st.session_state:
    st.session_state.show_confirm_reload = False
if 'show_confirm_clear' not in st.session_state:  # Add new state for clear confirmation
    st.session_state.show_confirm_clear = False
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'should_cancel' not in st.session_state:
    st.session_state.should_cancel = False


# Function to handle reload confirmation
def handle_reload_confirm():
    if st.session_state.show_confirm_reload:
        col1, col2 = st.sidebar.columns(2)
        
        # Yes button - disabled during processing
        with col1:
            yes_button = st.button(
                "Yes, Reload",
                key="confirm_yes",
                disabled=st.session_state.is_processing
            )
            
        # Cancel button - enabled only during processing
        with col2:
            if st.button(
                "Cancel",
                key="confirm_no",
            ):
                st.session_state.should_cancel = True
                st.session_state.is_processing = False
                st.session_state.show_confirm_reload = False
                st.rerun()
        print(st.session_state.is_processing)
        print(yes_button)
        print(st.session_state.show_confirm_reload)
        print(st.session_state.should_cancel)
        if yes_button and not st.session_state.is_processing:
            try:
                st.session_state.is_processing = True
                # Create a progress bar
                progress_bar = st.sidebar.progress(0)
                status_text = st.sidebar.empty()
                
                # Check for cancellation before scraping

                status_text.text("Scraping cheese data...")
                progress_bar.progress(25)
                scrape_cheese()
                
                # Check for cancellation before vector creation
                if not st.session_state.should_cancel:
                    status_text.text("Creating vectors...")
                    progress_bar.progress(75)
                    create_vector()
                    
                    # Complete the progress only if not cancelled
                    progress_bar.progress(100)
                    status_text.text("✅ Reload completed!")
                
                    # Clear progress after a short delay
                import time
                time.sleep(1)
                
                # Clean up
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                st.sidebar.error(f"Error during reload: {str(e)}")
            
            finally:
                # Reset states
                st.session_state.is_processing = False
                st.session_state.should_cancel = False
                st.session_state.show_confirm_reload = False
                st.rerun()

        # Show warning message
        if not st.session_state.is_processing:
            st.sidebar.warning("⚠️ This will construct the vector database again. Are you sure?")
        else:
            st.sidebar.info("💫 Processing... You can cancel the operation.")

# Add the reload button to the sidebar header
if not st.session_state.show_confirm_reload:
    if st.sidebar.button('🔄 Reload Cheese Data', key='reload_data'):
        st.session_state.show_confirm_reload = True
        st.rerun()

# Show confirmation dialog if needed
handle_reload_confirm()

# Add Clear Chat History button
if not st.session_state.show_confirm_clear:
    if st.sidebar.button('🗑️ Clear Chat History', key='clear_history'):
        st.session_state.show_confirm_clear = True
        st.rerun()

# Handle clear history confirmation
if st.session_state.show_confirm_clear:
    st.sidebar.warning("⚠️ Are you sure you want to clear the chat history?")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Yes, Clear", key="confirm_clear_yes"):
            st.session_state.messages = []  # Clear the messages
            st.session_state.show_confirm_clear = False
            st.rerun()
    with col2:
        if st.button("No, Cancel", key="confirm_clear_no"):
            st.session_state.show_confirm_clear = False
            st.rerun()

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load external CSS
def load_css():
    # Load CSS
    with open("static/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Load JavaScript
    with open("static/menu_handler.js") as f:
        st.components.v1.html(
            f"""
            <script>{f.read()}</script>
            """,
            height=0,
        )

# Load CSS at the start
load_css()

def initialize_pinecone():
    """Initialize Pinecone connection"""
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        return pc.Index("cheese-index")
    except Exception as e:
        st.error(f"Error initializing Pinecone: {e}")
        return None
            
def main():
    st.markdown("""
        <div class='header-container'>
            <h1 class='main-title'>🧀 Cheese Assistant Chatbot 🧀</h1>
            <div class='welcome-message'>
                <span style='font-size: 24px;'>👋</span> 
                Welcome to your personal cheese expert! I'm here to help you discover and learn about our amazing selection of cheeses.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Initialize Pinecone
    index = initialize_pinecone()
    if not index:
        st.error("Failed to initialize Pinecone. Please check your API key and connection.")
        return

    chat_container = st.container()
    with chat_container:
        # Display chat messages from history
        for message in st.session_state.messages:
            if message["role"] == "user":
                # User avatar can be an emoji, image URL, or a PIL Image
                avatar_user = "🧑‍🍳"  # Using an emoji as avatar
                # Or use an image: avatar_user = "https://path-to-user-image.jpg"
                
                with st.chat_message(message["role"], avatar=avatar_user):
                    st.markdown(message["content"])
                    
            elif message["role"] == "assistant":
                # Assistant avatar
                avatar_assistant = "🤖"  # Using an emoji as avatar
                # Or use an image: avatar_assistant = "https://path-to-assistant-image.jpg"
                
                with st.chat_message(message["role"], avatar=avatar_assistant):
                    st.markdown(message["content"])


    # Accept user input
    if prompt := st.chat_input("Ask about cheese..."):
        # Display user message in chat message container
        with st.chat_message("user", avatar="🧑‍🍳"):
            st.markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "🧑‍🍳"})

        # Display assistant response in chat message container with loading indicator
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            with st.spinner("..."):
                response = chatbot(prompt, index, st)
                message_placeholder.markdown(response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()