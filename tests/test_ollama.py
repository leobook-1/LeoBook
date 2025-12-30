import ollama
import sys

def test_model(model_name="qwen3-vl:2b"):
    print(f"Testing model: {model_name}...")
    try:
        response = ollama.chat(model=model_name, messages=[
            {'role': 'user', 'content': 'List 3 fruits.'},
        ])
        print("Success! Response:")
        print(response['message']['content'])
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the Ollama server is running and the model is pulled.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_model(sys.argv[1])
    else:
        test_model()
