import os
import yaml
from datetime import datetime
import logging
from DBConnection import (
    Conversation,
    Message,
    Agent,
    User,
    get_session,
)
from Defaults import DEFAULT_USER


def export_conversation(agent_name, conversation_name=None, user=DEFAULT_USER):
    session = get_session()
    user_data = session.query(User).filter(User.email == user).first()
    user_id = user_data.id
    agent = (
        session.query(Agent)
        .filter(Agent.name == agent_name, Agent.user_id == user_id)
        .first()
    )
    if not agent:
        global_user = session.query(User).filter(User.email == DEFAULT_USER).first()
        agent = Agent(name=agent_name, user_id=global_user.id)
        if not agent:
            logging.info(f"Agent '{agent_name}' not found in the database.")
            return
    if not conversation_name:
        conversation_name = f"{str(datetime.now())} Conversation"
    conversation = (
        session.query(Conversation)
        .filter(
            Conversation.name == conversation_name,
            Conversation.user_id == user_id,
        )
        .first()
    )
    if not conversation:
        logging.info(f"No conversation found for agent '{agent_name}'.")
        return

    messages = (
        session.query(Message).filter(Message.conversation_id == conversation.id).all()
    )

    history = {"interactions": []}

    for message in messages:
        interaction = {
            "role": message.role,
            "message": message.content,
            "timestamp": message.timestamp,
        }
        history["interactions"].append(interaction)

    agent_dir = os.path.join("agents", agent_name)
    os.makedirs(agent_dir, exist_ok=True)

    history_file = os.path.join(agent_dir, "history.yaml")
    with open(history_file, "w") as file:
        yaml.dump(history, file)

    logging.info(f"Exported conversation for agent '{agent_name}' to {history_file}.")


def get_conversations(agent_name, user=DEFAULT_USER):
    session = get_session()
    user_data = session.query(User).filter(User.email == user).first()
    user_id = user_data.id
    conversations = (
        session.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
        )
        .all()
    )
    return [conversation.name for conversation in conversations]


def get_conversation(
    agent_name="", conversation_name=None, limit=100, page=1, user=DEFAULT_USER
):
    session = get_session()
    user_data = session.query(User).filter(User.email == user).first()
    user_id = user_data.id
    if not conversation_name:
        conversation_name = f"{str(datetime.now())} Conversation"
    conversation = (
        session.query(Conversation)
        .filter(
            Conversation.name == conversation_name,
            Conversation.user_id == user_id,
        )
        .first()
    )
    if not conversation:
        # Create the conversation
        conversation = Conversation(name=conversation_name, user_id=user_id)
        session.add(conversation)
        session.commit()
    offset = (page - 1) * limit
    messages = (
        session.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.timestamp.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    if not messages:
        return {"interactions": []}
    return_messages = []
    for message in messages:
        msg = {
            "role": message.role,
            "message": message.content,
            "timestamp": message.timestamp,
        }
        return_messages.append(msg)
    return {"interactions": return_messages}


def new_conversation(
    agent_name, conversation_name, conversation_content=[], user=DEFAULT_USER
):
    session = get_session()
    user_data = session.query(User).filter(User.email == user).first()
    user_id = user_data.id
    # Check if the conversation already exists for the agent
    existing_conversation = (
        session.query(Conversation)
        .filter(
            Conversation.name == conversation_name,
            Conversation.user_id == user_id,
        )
        .first()
    )
    agent = (
        session.query(Agent)
        .filter(Agent.name == agent_name, Agent.user_id == user_id)
        .first()
    )
    if not agent:
        global_user = session.query(User).filter(User.email == DEFAULT_USER).first()
        agent = Agent(name=agent_name, user_id=global_user.id)
        if not agent:
            logging.info(f"Agent '{agent_name}' not found in the database.")
            return
    if not existing_conversation:
        # Create a new conversation
        conversation = Conversation(name=conversation_name, user_id=user_id)
        session.add(conversation)
        session.commit()
        if conversation_content != []:
            for interaction in conversation_content:
                new_message = Message(
                    role=interaction["role"],
                    content=interaction["message"],
                    timestamp=interaction["timestamp"],
                    conversation_id=conversation.id,
                )
                session.add(new_message)
        logging.info(
            f"Created a new conversation: '{conversation_name}' for agent '{agent_name}'."
        )
    else:
        conversation = existing_conversation
    return conversation


def log_interaction(agent_name, conversation_name, role, message, user=DEFAULT_USER):
    logging.info(
        f"Agent: {agent_name}, Conversation: {conversation_name}, Role: {role}, Message: {message}, User: {user}"
    )
    session = get_session()
    user_data = session.query(User).filter(User.email == user).first()
    user_id = user_data.id
    agent = (
        session.query(Agent)
        .filter(Agent.name == agent_name, Agent.user_id == user_id)
        .first()
    )
    if not agent:
        global_user = session.query(User).filter(User.email == DEFAULT_USER).first()
        agent = Agent(name=agent_name, user_id=global_user.id)
        if not agent:
            logging.info(f"Agent '{agent_name}' not found in the database.")
            return
    conversation = (
        session.query(Conversation)
        .filter(
            Conversation.name == conversation_name,
            Conversation.user_id == user_id,
        )
        .first()
    )

    if not conversation:
        # Create a new conversation if it doesn't exist
        conversation = new_conversation(
            agent_name=agent_name, conversation_name=conversation_name, user=user
        )
    timestamp = datetime.now().strftime("%B %d, %Y %I:%M %p")
    new_message = Message(
        role=role,
        content=message,
        timestamp=timestamp,
        conversation_id=conversation.id,
    )
    session.add(new_message)
    session.commit()
    logging.info(f"Logged interaction: [{timestamp}] {role}: {message}")


def delete_history(agent_name, conversation_name=None, user=DEFAULT_USER):
    session = get_session()
    user_data = session.query(User).filter(User.email == user).first()
    user_id = user_data.id
    if not conversation_name:
        conversation_name = f"{str(datetime.now())} Conversation"
    conversation = (
        session.query(Conversation)
        .filter(
            Conversation.name == conversation_name,
            Conversation.user_id == user_id,
        )
        .first()
    )
    if not conversation:
        logging.info(f"No conversation found for agent '{agent_name}'.")
        return

    session.query(Message).filter(Message.conversation_id == conversation.id).delete()
    session.query(Conversation).filter(
        Conversation.id == conversation.id, Conversation.user_id == user_id
    ).delete()
    session.commit()

    logging.info(f"Deleted conversation '{conversation_name}' for agent '{agent_name}'.")


def delete_message(message, conversation_name=None, agent_name=None, user=DEFAULT_USER):
    session = get_session()
    user_data = session.query(User).filter(User.email == user).first()
    user_id = user_data.id

    conversation = (
        session.query(Conversation)
        .filter(
            Conversation.name == conversation_name,
            Conversation.user_id == user_id,
        )
        .first()
    )

    if not conversation:
        logging.info(f"No conversation found for agent '{agent_name}'.")
        return
    message_id = (
        session.query(Message)
        .filter(
            Message.conversation_id == conversation.id,
            Message.content == message,
        )
        .first()
    ).id

    message = (
        session.query(Message)
        .filter(
            Message.conversation_id == conversation.id,
            Message.id == message_id,
        )
        .first()
    )

    if not message:
        logging.info(
            f"No message found with ID '{message_id}' in conversation '{conversation_name}'."
        )
        return

    session.delete(message)
    session.commit()

    logging.info(
        f"Deleted message with ID '{message_id}' from conversation '{conversation_name}'."
    )


def update_message(
    message, new_message, conversation_name=None, agent_name=None, user=DEFAULT_USER
):
    session = get_session()
    user_data = session.query(User).filter(User.email == user).first()
    user_id = user_data.id

    conversation = (
        session.query(Conversation)
        .filter(
            Conversation.name == conversation_name,
            Conversation.user_id == user_id,
        )
        .first()
    )

    if not conversation:
        logging.info(f"No conversation found for agent '{agent_name}'.")
        return
    message_id = (
        session.query(Message)
        .filter(
            Message.conversation_id == conversation.id,
            Message.content == message,
        )
        .first()
    ).id

    message = (
        session.query(Message)
        .filter(
            Message.conversation_id == conversation.id,
            Message.id == message_id,
        )
        .first()
    )

    if not message:
        logging.info(
            f"No message found with ID '{message_id}' in conversation '{conversation_name}'."
        )
        return

    message.content = new_message
    session.commit()

    logging.info(
        f"Updated message with ID '{message_id}' from conversation '{conversation_name}'."
    )
