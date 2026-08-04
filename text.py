import streamlit as st
from openai import OpenAI
import os
import datetime
import json

st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

#生成会话标识
def generate_session_name():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_session():
    if st.session_state.current_session:
        #构建会话对象
        session_data = {
            "nick_name": st.session_state.nick_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "message": st.session_state.messages
        }
        #如session不存在，就创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        #保存会话数据
        with open(f"sessions/{session_data['current_session']}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

#加载【所有会话列表】（无参数！复数sessions）
def load_sessions():
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for file in file_list:
            file_path = os.path.join("sessions", file)
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                session_list.append(session_data)
    session_list.sort(reverse=True)
    return session_list

#加载【单个会话】（需要传入session_name，单数session）
def load_session(session_name):
    try:
        file_path = f"sessions/{session_name}.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["message"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_name
    except Exception:
        st.error("加载会话失败")

#删除会话
def delete_session(session_name):
    try:
        file_path = f"sessions/{session_name}.json"
        if os.path.exists(file_path):
            os.remove(file_path)
            #如果删除当前会话，就删掉当前的列表
            if session_name == st.session_state.current_session:
                st.session_state.current_session = generate_session_name()
                st.session_state.messages = []
    except Exception:
        st.error("删除失败")


st.title("AI智能伴侣")

# st.logo("194be987912fe7cef07401ab50ce756b.jpg")

system_prompt = """
你叫%s，现在是用户的真实伴侣，请完全代入伴侣角色。：
规则：
1．每次只回1条消息
2．禁止任何场景或状态描述性文字
3．匹配用户的语言
4．回复简短，像微信聊天一样
5．有需要的话可以用❤️🌸等emoji表情
6．用符合伴侣性格的方式对话
7．回复的内容，要充分体现伴侣的性格特征

伴侣性格：
- %s

你必须严格遵守上述规则来回复用户。
"""

#聊天信息、昵称、性格
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小甜甜"
if "nature" not in st.session_state:
    st.session_state.nature = "活泼开朗的东北姑娘"

#会话标识
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

#展示聊天信息
st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# 创建与AI大模型交互的客户端对象
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

#侧边栏
with st.sidebar:
    st.subheader("AI控制面板")
    if st.button('新建会话', width="stretch"):
        #先保存当前会话
        save_session()
        #清空消息，新建会话
        st.session_state.messages = []
        st.session_state.current_session = generate_session_name()
        st.rerun()

    st.text("会话历史")

    #加载全部会话列表
    session_list = load_sessions()

    for session in session_list:
        session_name = session["current_session"]
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(
                session_name,
                width="stretch",
                key=f"load_{session_name}",
                type="primary" if session_name == st.session_state.current_session else "secondary"
            ):
                load_session(session_name)
                st.rerun()
        with col2:
            if st.button("X", width="stretch", key=f"delete_{session_name}"):
                delete_session(session_name)
                st.rerun()

    #分割线
    st.divider()

    st.subheader("伴侣信息")
    nick_name = st.text_input("昵称", placeholder="请输入昵称", value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name
    nature = st.text_area("性格", placeholder="请输入性格", value=st.session_state.nature)
    if nature:
        st.session_state.nature = nature

# 与AI大模型进行交互
prompt = st.chat_input("请输入你的问题：")
if prompt:
    st.chat_message("user").write(prompt)
    # 用户消息先存入上下文
    st.session_state.messages.append({"role": "user", "content": prompt})

    print("------->调用AI大模型，提示词：", prompt)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
            *st.session_state.messages
        ],
        stream=True
    )

    # 流式输出
    response_message = st.empty()
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    #保存AI返回结果
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    #保存对话信息
    save_session()