"""
JARVIS Terminal Chat Interface
Simple terminal-based chatbot using LLM router
"""

import os
import sys
import asyncio
from datetime import datetime
from jarvis_router import process_jarvis_query, router


class TerminalChat:
    """Simple terminal chat interface"""
    
    def __init__(self):
        self.user_id = "terminal_user"
        self.conversation_history = []
        self.session_active = True
    
    def display_welcome(self):
        """Show welcome message"""
        print("=" * 60)
        print("JARVIS Terminal Chat")
        print("=" * 60)
        print("Type 'quit', 'exit', or 'bye' to end the session")
        print("Type 'clear' to clear conversation history")
        print("Type 'status' to see system status")
        print("-" * 60)
    
    def display_prompt(self):
        """Show input prompt"""
        return input("\nYou: ").strip()
    
    def display_response(self, response_data):
        """Display AI response"""
        if response_data["success"]:
            print(f"\nJARVIS: {response_data['response']}")
            print(f"\n[Model: {response_data['model_used']} | Time: {response_data['processing_time']:.2f}s]")
        else:
            print(f"\nJARVIS: {response_data['response']}")
            print(f"\n[Error: {response_data.get('error', 'Unknown error')}]")
    
    def handle_command(self, user_input):
        """Handle special commands"""
        command = user_input.lower()
        
        if command in ['quit', 'exit', 'bye']:
            print("\nGoodbye!")
            self.session_active = False
            return True
        
        elif command == 'clear':
            self.conversation_history = []
            os.system('cls' if os.name == 'nt' else 'clear')
            self.display_welcome()
            print("Conversation history cleared.")
            return True
        
        elif command == 'status':
            status = router.get_status()
            print("\nSystem Status:")
            print(f"Active sessions: {status['active_sessions']}")
            print(f"Cerebras available: {status['cerebras_available']}")
            print(f"Current hour: {status['current_hour']}")
            print("\nRate limits:")
            for provider, limit_info in status['rate_limits'].items():
                used = limit_info['count']
                max_limit = limit_info['max']
                print(f"  {provider}: {used}/{max_limit}")
            return True
        
        return False
    
    def build_context(self):
        """Build context from conversation history"""
        if not self.conversation_history:
            return ""
        
        # Include last 3 exchanges for context
        recent_history = self.conversation_history[-6:]  # 3 pairs of user/assistant
        context_parts = []
        
        for i in range(0, len(recent_history), 2):
            if i + 1 < len(recent_history):
                user_msg = recent_history[i]
                assistant_msg = recent_history[i + 1]
                context_parts.append(f"User: {user_msg}")
                context_parts.append(f"Assistant: {assistant_msg}")
        
        return " | ".join(context_parts[-4:])  # Last 2 exchanges
    
    async def chat_loop(self):
        """Main chat loop"""
        self.display_welcome()
        
        while self.session_active:
            try:
                # Get user input
                user_input = self.display_prompt()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if self.handle_command(user_input):
                    continue
                
                # Add to conversation history
                self.conversation_history.append(user_input)
                
                # Build context
                context = self.build_context()
                
                # Prepare user context
                user_context = {
                    "user_id": self.user_id,
                    "authenticated": True,
                    "context": {"conversation_history": context}
                }
                
                # Get response from LLM
                print("\nJARVIS: Thinking...")
                response_data = await process_jarvis_query(user_input, user_context)
                
                # Display response
                self.display_response(response_data)
                
                # Add response to history
                if response_data["success"]:
                    self.conversation_history.append(response_data["response"])
                
                # Limit history size
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
            
            except KeyboardInterrupt:
                print("\n\nSession interrupted by user.")
                self.session_active = False
                break
            
            except Exception as e:
                print(f"\nError: {e}")
                print("Please try again.")


def setup_environment():
    """Setup required environment variables"""
    # Set Cerebras API key
    if not os.getenv("CEREBRAS_API_KEY"):
        os.environ["CEREBRAS_API_KEY"] = "csk-44c3n6nehvh63vmw4r3n8hmkr5hx6pcdrdtt6fnem3cetpeh"
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


async def main():
    """Main function"""
    setup_environment()
    
    # Initialize chat
    chat = TerminalChat()
    
    # Start chat loop
    await chat.chat_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)