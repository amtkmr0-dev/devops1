from pyngrok import ngrok

# Set your Flask port
port = 5000

# Open a tunnel to the Flask app
public_url = ngrok.connect(port)
print(f"ngrok tunnel running at: {public_url}")
input("Press Enter to exit and close tunnel...")
ngrok.disconnect(public_url)
