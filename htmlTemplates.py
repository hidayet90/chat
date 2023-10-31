css = '''
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
[data-testid="stExpander"] div:has(>.streamlit-expanderContent) {
        overflow: scroll;
        height: 350px;
    }
.stButton > button {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100%;
    padding: 0.5em 1em;
    color: #FFFFFF;
    background-color: #00A36C;
    border-radius: 3px;
    text-decoration: none;
    cursor: pointer;
    border: none;
    font-size: 1rem;
    outline: none;
}
.stButton > button, .stButton > button a {
    color: #FFFFFF !important;
    text-decoration: none !important;
}
.stButton > button:hover,
.stButton > button:active,
.stButton > button:focus {
    background-color: #00A36C;
    color: #FFFFFF;
    text-decoration: none;
    box-shadow: none;
}
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://static.vecteezy.com/system/resources/previews/009/971/219/non_2x/chat-bot-icon-isolated-contour-symbol-illustration-vector.jpg" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://static.vecteezy.com/system/resources/previews/016/009/835/original/the-human-icon-and-logo-vector.jpg">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''