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
                    "I am the SMS Assistant! 🎓\n\n"
                    "*(Note: The Gemini API key is currently missing from the environment variables. "
                    "To enable real AI responses, please add GEMINI_API_KEY to your Vercel settings.)*\n\n"
                    f"You said: '{user_message}'"
                )
                return JsonResponse({'reply': mock_response})
            
            # Initialize Gemini model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Construct a prompt giving the AI context about the user
            context_prompt = (
                f"You are a helpful and professional chatbot assistant for a Student Management System (SMS). "
                f"You are talking to a user named {request.user.username} "
                f"(Role: {'Faculty' if request.user.groups.filter(name='Faculty').exists() else 'Student'}). "
                f"Keep your answers concise and formatted nicely with markdown if appropriate. "
                f"The user says: {user_message}"
            )
            
            response = model.generate_content(context_prompt)
            
            return JsonResponse({'reply': response.text})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)
