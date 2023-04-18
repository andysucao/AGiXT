import os
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from babyagi import babyagi
from AgentLLM import AgentLLM
from Config import Config

CFG = Config()
app = Flask(__name__)
CORS(app)

babyagi_instance = babyagi()


@app.route('/api/add_agent/<string:agent_name>', methods=['POST'])
def add_agent(agent_name):
    memories_dir = "memories"
    if not os.path.exists(memories_dir):
        os.makedirs(memories_dir)
    i = 0
    agent_file = f"{agent_name}.yaml"
    while os.path.exists(os.path.join(memories_dir, agent_file)):
        i += 1
        agent_file = f"{agent_name}_{i}.yaml"
    with open(os.path.join(memories_dir, agent_file), "w") as f:
        f.write("")
    return {"message": "Agent added", "agent_file": agent_file}, 200


@app.route('/api/delete_agent/<string:agent_name>', methods=['DELETE'])
def delete_agent(agent_name):
    agent_file = f"memories/{agent_name}.yaml"
    agent_folder = f"memories/{agent_name}/"
    agent_file = os.path.abspath(agent_file)
    agent_folder = os.path.abspath(agent_folder)

    try:
        os.remove(agent_file)
    except FileNotFoundError:
        return jsonify({"message": f"Agent file {agent_file} not found."}), 404

    if os.path.exists(agent_folder):
        shutil.rmtree(agent_folder)

    return jsonify({"message": f"Agent {agent_name} deleted."}), 200


@app.route('/api/get_agents', methods=['GET'])
def get_agents():
    memories_dir = "memories"
    agents = []
    for file in os.listdir(memories_dir):
        if file.endswith(".yaml"):
            agents.append(file.replace(".yaml", ""))
    return jsonify({"agents": agents}), 200


@app.route('/api/get_chat_history/<string:agent_name>', methods=['GET'])
def get_chat_history(agent_name):
    agent = AgentLLM()
    agent.CFG.AGENT_NAME = agent_name
    with open(os.path.join("memories", f"{agent_name}.yaml"), "r") as f:
        chat_history = f.read()
    return jsonify({"chat_history": chat_history}), 200


@app.route('/api/instruct', methods=['POST'])
def instruct():
    objective = request.json.get("prompt")
    data = request.json.get("data")
    agent = AgentLLM()
    agent.CFG.AGENT_NAME = data["agent_name"]
    agent.CFG.COMMANDS_ENABLED = data["commands_enabled"]
    agent.CFG.AI_PROVIDER = data["ai_provider"]
    agent.CFG.OPENAI_API_KEY = data["openai_api_key"]
    response = agent.run(objective, max_context_tokens=500, long_term_access=False)
    return jsonify({"response": str(response)}), 200


@app.route('/api/set_objective', methods=['POST'])
def set_objective():
    objective = request.json.get("objective")
    babyagi_instance.set_objective(objective)
    return jsonify({"message": "Objective updated"}), 200


@app.route('/api/add_initial_task', methods=['POST'])
def add_initial_task():
    babyagi_instance.add_initial_task()
    return jsonify({"message": "Initial task added"}), 200


@app.route('/api/execute_next_task', methods=['GET'])
def execute_next_task():
    task = babyagi_instance.execute_next_task()
    task_list = list(babyagi_instance.task_list)
    if task:
        return jsonify({"task": task, "result": babyagi_instance.response, "task_list": task_list}), 200
    else:
        return jsonify({"message": "All tasks complete"}), 200


@app.route('/api/create_task', methods=['POST'])
def create_task():
    objective = request.json.get("objective")
    result = request.json.get("result")
    task_description = request.json.get("task_description")
    task_list = request.json.get("task_list")
    new_tasks = babyagi_instance.task_creation_agent(objective, result, task_description, task_list)
    return jsonify({"new_tasks": new_tasks}), 200


@app.route('/api/prioritize_tasks', methods=['POST'])
def prioritize_tasks():
    task_id = request.json.get("task_id")
    babyagi_instance.prioritization_agent(task_id)
    return jsonify({"task_list": babyagi_instance.task_list}), 200


@app.route('/api/execute_task', methods=['POST'])
def execute_task():
    objective = request.json.get("objective")
    task = request.json.get("task")
    result = babyagi_instance.execution_agent(objective, task)
    return jsonify({"result": result}), 200


if __name__ == '__main__':
    app.run(debug=True)