import json
import os
from flask import Flask, request, jsonify
from utils.json_db import JsonDatabase
from auth import require_auth
from openai import OpenAI

app = Flask(__name__)
db = JsonDatabase('data/customers.json')

# Load configuration from config.json
config = {}
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: config.json not found at {config_path}")
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {config_path}")

# Now 'config' dictionary contains your configuration data
# You can access it like config['api_key'], config['model_name'], etc.

# Initialize OpenAI client
openai_client = None
if config.get('api_key') and config.get('base_url'):
    openai_client = OpenAI(
        api_key=config['api_key'],
        base_url=config['base_url']
    )
else:
    print("Warning: OpenAI API key or base URL not found in config.json. Chatbot functionality will be limited.")

# Chat endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    if not openai_client:
        return jsonify({"error": "OpenAI client not initialized."}), 500

    data = request.json
    user_message = data.get('message')
    # conversation_history = data.get('history', []) # Assuming history might be sent from frontend

    if not user_message:
        return jsonify({"error": "No message provided."}), 400

    # Basic API call using a general prompt for now
    # TODO: Implement more sophisticated prompt selection and history management based on dialogue state
    try:
        # Example API call (adjust parameters as needed)
        response = openai_client.chat.completions.create(
            model=config.get('model_name', 'gpt-3.5-turbo'), # Use model from config, default if not found
            messages=[
                {"role": "system", "content": config.get('c_prompt', 'You are a helpful assistant.')},
                # Add conversation history here if available
                {"role": "user", "content": user_message}
            ]
        )
        ai_response = response.choices[0].message.content
        return jsonify({"response": ai_response})

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return jsonify({"error": "Error processing chat message."}), 500

# 登录接口
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 简单验证 - 实际应用中应使用更安全的方式
    if username == 'admin' and password == '123456':
        token = create_token(username)
        return jsonify({
            'status': 'ok',
            'token': token
        })
    
    return jsonify({
        'status': 'error',
        'code': 401,
        'message': '用户名或密码错误'
    }), 401

# 获取所有客户
@app.route('/api/customers', methods=['GET'])
@token_required
def get_all_customers():
    customers = customers_db.get_all()
    return jsonify(customers)

# 搜索客户
@app.route('/api/customers/search', methods=['GET'])
@token_required
def search_customers():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    customers = customers_db.get_all()
    results = []
    
    for customer in customers:
        # 在名称、联系方式或需求中搜索
        if (query.lower() in customer['name'].lower() or
            query.lower() in customer.get('contact', '').lower() or
            query.lower() in customer.get('requirement', '').lower()):
            results.append(customer)
    
    return jsonify(results)

# 获取单个客户
@app.route('/api/customers/<id>', methods=['GET'])
@token_required
def get_customer(id):
    customer = customers_db.get_by_id(id)
    if not customer:
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': '客户不存在'
        }), 404
    
    return jsonify(customer)

# 新增客户
@app.route('/api/customers', methods=['POST'])
@token_required
def add_customer():
    data = request.get_json()
    
    # 验证必填字段
    if not data.get('name'):
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': '客户名称不能为空'
        }), 400
    
    # 验证字段长度
    if len(data.get('name', '')) > 50:
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': '客户名称不能超过50个字符'
        }), 400
    
    # 生成客户ID
    customer_id = f"cus{uuid.uuid4().hex[:6]}"
    
    # 创建客户记录
    customer = {
        'id': customer_id,
        'name': data.get('name'),
        'source': data.get('source', '官网'),
        'contact': data.get('contact', ''),
        'requirement': data.get('requirement', ''),
        'last_meeting': data.get('last_meeting', datetime.now().strftime('%Y-%m-%d')),
        'next_followup': data.get('next_followup', ''),
        'stage': data.get('stage', '需求沟通')
    }
    
    # 保存到JSON文件
    customers_db.add(customer)
    
    return jsonify({
        'status': 'ok',
        'message': '客户添加成功',
        'customer': customer
    })

# 更新客户
@app.route('/api/customers/<id>', methods=['PUT'])
@token_required
def update_customer(id):
    data = request.get_json()
    customer = customers_db.get_by_id(id)
    
    if not customer:
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': '客户不存在'
        }), 404
    
    # 更新字段
    for key, value in data.items():
        if key != 'id':  # 不允许修改ID
            customer[key] = value
    
    # 保存更新
    customers_db.update(customer)
    
    return jsonify({
        'status': 'ok',
        'message': '客户信息更新成功',
        'customer': customer
    })

# 删除客户（可选功能）
@app.route('/api/customers/<id>', methods=['DELETE'])
@token_required
def delete_customer(id):
    customer = customers_db.get_by_id(id)
    
    if not customer:
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': '客户不存在'
        }), 404
    
    # 删除客户
    customers_db.delete(id)
    
    return jsonify({
        'status': 'ok',
        'message': '客户删除成功'
    })

# AI Chatbot endpoint
@app.route('/api/chatbot', methods=['POST'])
@token_required
def chatbot():
    data = request.get_json()
    user_message = data.get('message', '')

    # Simple mock response based on user input
    if '你好' in user_message:
        bot_response = '你好！有什么可以帮您？'
    elif '客户' in user_message:
        bot_response = '您可以问我关于客户信息、销售记录等问题。'
    elif '谢谢' in user_message:
        bot_response = '不客气！'
    else:
        bot_response = '抱歉，我暂时无法回答这个问题。您可以问我关于客户相关的问题。'

    return jsonify({
        'status': 'ok',
        'response': bot_response
    })

if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs('data', exist_ok=True)
    
    # 如果客户数据文件不存在，创建初始数据
    if not os.path.exists('data/customers.json'):
        with open('data/customers.json', 'w', encoding='utf-8') as f:
            json.dump([
                {
                    "id": "cus002",
                    "name": "未来动力",
                    "source": "展会",
                    "contact": "contact@fd.com",
                    "requirement": "AI本地化",
                    "last_meeting": "2025-05-22",
                    "next_followup": "2025-05-26",
                    "stage": "方案演示"
                }
            ], f, ensure_ascii=False, indent=2)
    
    app.run(host='0.0.0.0', port=8000, debug=True)