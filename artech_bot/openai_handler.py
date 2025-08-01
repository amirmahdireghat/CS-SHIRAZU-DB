import os
import django
from openai import OpenAI
import base64

# Load environment variables
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "artech_bot.settings"
)  # Replace with your project name
django.setup()
from admin_panel.models import user_data, Chat
from admin_panel.models import prompt
# Set the OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_response(user_id: int, user_message: str) -> str:
    prompt_text = ""
    try:
        # Retrieve the user data from the database
        user = user_data.objects.get(id=user_id)
        if user.selected_prompt == 1:
            token_option = prompt.objects.get(prompt_id=1)
            prompt_text = token_option.prompt_text
        else:
            token_option = prompt.objects.get(prompt_id=2)
            prompt_text = token_option.prompt_text
        # Retrieve the user's chat history (e.g., last 10 messages for memory purposes)
        previous_chats = Chat.objects.filter(user_id=user).order_by("-timestamp")[:10]

        # Prepare the messages for the OpenAI API
        messages = []

        # Add a system message to guide the assistant's behavior
        system_message = {
            "role": "system",
            "content": prompt_text
        }
        messages.append(system_message)
        # Add previous chats to the messages
        for chat in reversed(previous_chats):  # Reverse to maintain chronological order
            messages.append({"role": "user", "content": chat.message})
            messages.append({"role": "assistant", "content": chat.response})

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        # Make a request to the OpenAI API
        completion = client.chat.completions.create(
            model=user.selected_llm,  # Specify the model you want to use
            messages=messages,
            temperature=0.6,  # Controls the randomness (0.0 - 1.0)
            top_p=0.85,  # Nucleus sampling (0.0 - 1.0)
            frequency_penalty=0.2,  # Discourages repetition (-2.0 - 2.0)
            presence_penalty=0.3,  # Encourages new topics (-2.0 - 2.0)
        )

        # Access the response correctly
        return completion.choices[0].message.content
    except user_data.DoesNotExist:
        return "Error: User data not found."
    except Exception as e:
        return f"Error: {str(e)}"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def openai_image_handler(user_id, media_path):
    # Retrieve the user data from the database
    user = user_data.objects.get(id=user_id)
    # Add a system message to guide the assistant's behavior
    system_message= []
    system_message.append({
        "role": "system",
        "content": prompt.objects.get(prompt_id=3).prompt_text
    })
    base64_image = encode_image(media_path)
    system_message.append({"role": "user", "content": [{"type": "image_url","image_url": {"url": f"data:image/png;base64,{base64_image}"}}]})
    response = client.chat.completions.create(
        model="gpt-4o",
        messages = system_message,
        max_tokens=300,
    )
    return response.choices[0].message.content

def openai_generate_image(user_id: int, prompt_text: str) -> str:
    """
    Generates an image using OpenAI's image generation API with the DALL-E 3 model.
    Returns the URL of the generated image.
    """
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_text,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        return f"Error: {str(e)}"