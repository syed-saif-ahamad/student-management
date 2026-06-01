import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import google.generativeai as genai

# Configure Gemini AI if the API key is present
api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)

@csrf_exempt
@login_required
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'error': 'Message is required'}, status=400)
            
            # If no API key is set, return a mock response guiding the user
            if not api_key:
                mock_response = (
                    "⚠️ **API Key Missing!**\n\n"
                    "I cannot analyze or explain the meaning of your sentence because the `GEMINI_API_KEY` environment variable is not set.\n\n"
                    "Please get a free API key from Google AI Studio and add it to your Vercel Environment Variables. Once added, I will be able to explain the meaning of: *" + user_message + "*"
                )
                return JsonResponse({'reply': mock_response})
            
            # Initialize Gemini model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Construct a prompt giving the AI context about the user
            context_prompt = (
                f"You are a helpful dictionary and language AI assistant. "
                f"The user ({request.user.username}) will give you a prompt, word, or sentence. "
                f"Your primary job is to explain the exact meaning of the particular input sentence or word they provide. "
                f"Keep your answers concise, educational, and formatted nicely with markdown. "
                f"The user says: {user_message}"
            )
            
            response = model.generate_content(context_prompt)
            
            return JsonResponse({'reply': response.text})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)
