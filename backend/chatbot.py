from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("groq_api_key")

# Initialize LLM
llm = ChatGroq(
    temperature=0.7,
    groq_api_key=groq_api_key,
    model_name="llama-3.1-8b-instant"
)

# Chatbot prompt
chatbot_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI travel assistant for the Travel Web application by PCS Techno Pvt Ltd.
    
    You can help users with:
    - Travel planning and itinerary questions
    - Destination information and recommendations
    - Budget planning and cost estimates
    - Packing tips and travel gear advice
    - Cultural information and local customs
    - Transportation options between cities
    - Hotel and accommodation suggestions
    - Best times to visit destinations
    - Visa and documentation requirements
    
    IMPORTANT FORMATTING RULES:
    - Use bullet points (•) for lists
    - Use numbered lists (1., 2., 3.) for steps or sequences
    - Use line breaks between sections
    - Use emojis to make responses engaging (✈️ 🏨 🌍 💰 🎒 etc.)
    - Bold important information using **text**
    - Keep responses well-structured and easy to read
    - Use short paragraphs (2-3 sentences max)
    
    Provide concise, helpful, and friendly responses. If you don't know something specific, 
    suggest the user use the main application features for detailed planning.
    
    Keep responses under 200 words unless more detail is specifically requested."""),
    ("human", "{message}")
])

# Create chain
chatbot_chain = chatbot_prompt | llm | StrOutputParser()

def get_chatbot_response(user_message: str, conversation_history: list = None) -> str:
    """
    Get chatbot response for user message
    
    Args:
        user_message: The user's question or message
        conversation_history: Optional list of previous messages for context
        
    Returns:
        str: The chatbot's response
    """
    try:
        # If conversation history provided, include context
        if conversation_history:
            context = "\n".join([
                f"{'User' if i % 2 == 0 else 'Assistant'}: {msg}" 
                for i, msg in enumerate(conversation_history[-6:])  # Last 3 exchanges
            ])
            enhanced_message = f"Previous conversation:\n{context}\n\nCurrent question: {user_message}"
        else:
            enhanced_message = user_message
            
        response = chatbot_chain.invoke({"message": enhanced_message})
        return response
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try again."

def get_travel_suggestion(destination: str, interests: list) -> str:
    """
    Get personalized travel suggestions based on destination and interests
    
    Args:
        destination: Country or city name
        interests: List of user interests
        
    Returns:
        str: Personalized travel suggestions
    """
    interests_str = ", ".join(interests) if interests else "general travel"
    message = f"I'm planning to visit {destination}. My interests include {interests_str}. Can you give me 3-5 quick tips or must-see recommendations?"
    return get_chatbot_response(message)
