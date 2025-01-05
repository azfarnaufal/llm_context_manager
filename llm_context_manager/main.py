import os
from typing import List, Dict
import json
import tiktoken
from abc import ABC, abstractmethod
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIProvider(ABC):
	@abstractmethod
	def generate_summary(self, text: str, system_prompt: str) -> str:
		pass

class OpenAIProvider(AIProvider):
	def __init__(self):
		self.client = OpenAI(
			api_key=os.getenv("OPENAI_API_KEY")
		)
		self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4")

	def generate_summary(self, text: str, system_prompt: str) -> str:
		try:
			response = self.client.chat.completions.create(
				model=self.model_name,
				messages=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": text}
				],
				max_tokens=int(os.getenv("MAX_TOKENS_PER_REQUEST", 4000)),
				temperature=0.7
			)
			return response.choices[0].message.content
		except Exception as e:
			print(f"OpenAI API Error: {str(e)}")
			return f"Error in summarization: {str(e)}"

class GeminiProvider(AIProvider):
	def __init__(self):
		api_key = os.getenv("GEMINI_API_KEY")
		genai.configure(api_key=api_key, transport="rest")  # Using direct REST transport
		self.model = genai.GenerativeModel(os.getenv("GEMINI_MODEL_NAME", "gemini-pro"))

	def generate_summary(self, text: str, system_prompt: str) -> str:
		try:
			prompt = f"{system_prompt}\n\n{text}"
			response = self.model.generate_content(prompt)
			return response.text
		except Exception as e:
			print(f"Gemini API Error: {str(e)}")
			return f"Error in summarization: {str(e)}"

class ConversationManager:
	def __init__(self, chunk_size: int = 30000):
		self.chunk_size = chunk_size
		self.summaries = []
		self.current_position = 0
		
		# Initialize AI provider based on environment variable
		provider_type = os.getenv("AI_PROVIDER", "openai").lower()
		if provider_type == "openai":
			self.ai_provider = OpenAIProvider()
			self.encoding = tiktoken.encoding_for_model(os.getenv("OPENAI_MODEL_NAME", "gpt-4"))
		elif provider_type == "gemini":
			self.ai_provider = GeminiProvider()
			# For Gemini, we'll use a simple character-based approximation
			self.encoding = None
		else:
			raise ValueError(f"Unsupported AI provider: {provider_type}")

	def count_tokens(self, text: str) -> int:
		"""Count the number of tokens in a text string."""
		if self.encoding:
			return len(self.encoding.encode(text))
		else:
			# Simple approximation for Gemini (4 characters ≈ 1 token)
			return len(text) // 4

	def chunk_conversation(self, text: str) -> List[str]:
		"""Split conversation into chunks based on token count."""
		chunks = []
		current_chunk = ""
		current_tokens = 0
		
		sentences = text.replace("! ", "!<SPLIT>").replace("? ", "?<SPLIT>").replace(". ", ".<SPLIT>").split("<SPLIT>")
		
		for sentence in sentences:
			sentence_tokens = self.count_tokens(sentence)
			
			if current_tokens + sentence_tokens < self.chunk_size:
				current_chunk += sentence + " "
				current_tokens += sentence_tokens
			else:
				if current_chunk:
					chunks.append(current_chunk.strip())
				current_chunk = sentence + " "
				current_tokens = sentence_tokens
		
		if current_chunk:
			chunks.append(current_chunk.strip())
		
		return chunks

	def summarize_chunk(self, chunk: str) -> str:
		"""Summarize a single chunk of conversation."""
		system_prompt = "You are a helpful assistant that summarizes conversations. Create a concise summary that captures the main points and context of the conversation."
		return self.ai_provider.generate_summary(
			f"Please summarize the following conversation chunk:\n\n{chunk}",
			system_prompt
		)

	def process_conversation(self, conversation_text: str) -> str:
		"""Process entire conversation and create hierarchical summaries."""
		print("Starting conversation processing...")
		
		chunks = self.chunk_conversation(conversation_text)
		print(f"Split conversation into {len(chunks)} chunks")
		
		chunk_summaries = []
		for i, chunk in enumerate(chunks, 1):
			print(f"Processing chunk {i}/{len(chunks)}")
			summary = self.summarize_chunk(chunk)
			chunk_summaries.append(summary)
			self.summaries.append(summary)

		print("Creating final meta-summary...")
		final_summary = self.create_meta_summary(chunk_summaries)
		return final_summary

	def create_meta_summary(self, summaries: List[str]) -> str:
		"""Create a summary of summaries with progress points."""
		system_prompt = """Create a comprehensive meta-summary that:
		1. Combines and synthesizes multiple conversation summaries into a coherent narrative
		2. Ends with a 'Progress Points' section that includes:
		   - Key decisions or conclusions reached
		   - Last discussed topics or events
		   - Current status or next steps
		Format the progress points as bullet points for clarity."""
		
		combined_summaries = "\n\n".join([f"Summary {i+1}: {summary}" for i, summary in enumerate(summaries)])
		return self.ai_provider.generate_summary(
			f"Create a final summary that combines these summaries and includes progress points:\n\n{combined_summaries}",
			system_prompt
		)

	def save_state(self, filepath: str):
		"""Save the current state of summaries to a file with timestamp and progress."""
		from datetime import datetime
		
		state = {
			"summaries": self.summaries,
			"current_position": self.current_position,
			"last_updated": datetime.now().isoformat(),
			"last_summary": self.summaries[-1] if self.summaries else None
		}
		
		with open(filepath, 'w') as f:
			json.dump(state, f, indent=2)
		print(f"State saved to {filepath}")

	def load_state(self, filepath: str):
		"""Load previous state of summaries and display last session info."""
		if os.path.exists(filepath):
			with open(filepath, 'r') as f:
				state = json.load(f)
				self.summaries = state["summaries"]
				self.current_position = state["current_position"]
				
				# Display previous session information
				print("\nPrevious Session Information:")
				print(f"Last Updated: {state.get('last_updated', 'Unknown')}")
				if state.get('last_summary'):
					print("\nLast Progress Summary:")
					print(state['last_summary'])
				print("-" * 50)

def process_file(filepath: str, output_filepath: str = "conversation_state.json"):
	"""Process a conversation file and save the results."""
	try:
		with open(filepath, 'r', encoding='utf-8') as f:
			conversation_text = f.read()
		
		manager = ConversationManager()
		final_summary = manager.process_conversation(conversation_text)
		
		manager.save_state(output_filepath)
		
		summary_filepath = output_filepath.replace('.json', '_summary.txt')
		with open(summary_filepath, 'w', encoding='utf-8') as f:
			f.write(final_summary)
		
		print(f"Processing complete. Summary saved to {summary_filepath}")
		return final_summary
		
	except Exception as e:
		print(f"Error processing file: {str(e)}")
		return None

def main():
	import sys
	
	if len(sys.argv) > 1:
		input_file = sys.argv[1]
		final_summary = process_file(input_file)
		if final_summary:
			print("\nFinal Summary:")
			print(final_summary)
	else:
		print("Please provide an input file path as argument")
		print("Usage: python main.py <input_file>")

if __name__ == "__main__":
	main()