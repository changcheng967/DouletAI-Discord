import os
import discord
from discord.ext import commands
from flask import Flask, render_template
from threading import Thread
import uuid
import json
import asyncio
from queue import Queue

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Create response queue
response_queue = Queue()

# Flask server setup
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('puter_bot.html')

@app.route('/generate', methods=['POST'])
def generate():
    request_id = str(uuid.uuid4())
    data = request.json
    prompt = data['prompt']
    
    # Send message to iframe
    return json.dumps({
        'requestId': request_id,
        'prompt': prompt
    })

# Discord bot commands
@bot.event
async def on_ready():
    print(f'🔗 Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'📎 Invite link: https://discord.com/oauth2/authorize?client_id={bot.user.id}&scope=bot')

async def get_puter_response(prompt):
    """Get response from Puter.js"""
    request_id = str(uuid.uuid4())
    
    # Create iframe communication
    iframe_html = f"""
    <iframe src="/" style="display:none"></iframe>
    <script>
        const iframe = document.querySelector('iframe');
        iframe.onload = () => {{
            iframe.contentWindow.postMessage({{
                type: 'generate',
                prompt: '{prompt.replace("'", "\\'")}',
                requestId: '{request_id}'
            }}, '*');
        }};
        
        // Listen for responses
        window.addEventListener('message', (event) => {{
            if (event.data.requestId === '{request_id}') {{
                if (event.data.type === 'response') {{
                    fetch(`/response/{request_id}`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ response: event.data.message }})
                    }});
                }}
            }}
        }});
    </script>
    """
    return iframe_html

@bot.event
async def on_message(message):
    if message.guild is None or message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not prompt:
            await message.reply("Hello! How can I assist you today?")
            return
        
        try:
            # Show typing indicator
            async with message.channel.typing():
                # Get Puter.js response
                response_html = await get_puter_response(prompt)
                
                # For demo: Just show the concept
                await message.reply(f"🤖 Generating response via Puter.js...\n(Puter.js implementation would go here)")
                
                # In production: You'd parse the actual response
                # from the Flask endpoint
                
        except Exception as e:
            await message.reply(f"🚨 Error: {str(e)[:1900]}")

# Start Flask server in background
Thread(target=lambda: app.run(port=8080, host='0.0.0.0')).start()

# Start Discord bot
bot.run(os.getenv('DISCORD_TOKEN'))
