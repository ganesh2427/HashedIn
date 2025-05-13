from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(_name_)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Task model definition
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_str_id = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    estimated_time_minutes = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'internal_db_id': self.id,
            'task_str_id': self.task_str_id,
            'description': self.description,
            'estimated_time_minutes': self.estimated_time_minutes,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat()
        }

# Initialize the database
@app.before_first_request
def create_tables():
    db.create_all()

# API Endpoints
@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()

    # Validate inputs
    task_str_id = data.get('task_str_id')
    description = data.get('description')
    estimated_time_minutes = data.get('estimated_time_minutes')

    if not task_str_id or not description or not estimated_time_minutes or estimated_time_minutes <= 0:
        return jsonify({"error": "Invalid input"}), 400

    # Check if task_str_id is unique
    if Task.query.filter_by(task_str_id=task_str_id).first():
        return jsonify({"error": "Task ID already exists"}), 400

    # Create and add the task to the database
    new_task = Task(task_str_id=task_str_id, description=description, estimated_time_minutes=estimated_time_minutes)
    db.session.add(new_task)
    db.session.commit()

    return jsonify(new_task.to_dict()), 201

@app.route('/tasks/<task_str_id>', methods=['GET'])
def get_task(task_str_id):
    task = Task.query.filter_by(task_str_id=task_str_id).first()

    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(task.to_dict())

@app.route('/tasks/<task_str_id>/status', methods=['PUT'])
def update_task_status(task_str_id):
    data = request.get_json()
    new_status = data.get('new_status')

    if new_status not in ['pending', 'processing', 'completed']:
        return jsonify({"error": "Invalid status"}), 400

    task = Task.query.filter_by(task_str_id=task_str_id).first()

    if not task:
        return jsonify({"error": "Task not found"}), 404

    # Prevent invalid status transitions
    if task.status == 'completed' and new_status != 'completed':
        return jsonify({"error": "Completed task cannot go back to pending or processing"}), 400
    if task.status == 'processing' and new_status == 'pending':
        return jsonify({"error": "Processing task cannot go back to pending"}), 400

    task.status = new_status
    db.session.commit()

    return jsonify(task.to_dict())

@app.route('/tasks/next-to-process', methods=['GET'])
def get_next_task_to_process():
    task = Task.query.filter_by(status='pending').order_by(Task.estimated_time_minutes, Task.submitted_at).first()

    if not task:
        return jsonify({"error": "No pending tasks"}), 404

    return jsonify(task.to_dict())

@app.route('/tasks/pending', methods=['GET'])
def list_pending_tasks():
    sort_by = request.args.get('sort_by', 'time')
    order = request.args.get('order', 'asc')
    limit = int(request.args.get('limit', 10))

    query = Task.query.filter_by(status='pending')

    if sort_by == 'time':
        if order == 'asc':
            query = query.order_by(Task.estimated_time_minutes)
        else:
            query = query.order_by(Task.estimated_time_minutes.desc())
    elif sort_by == 'submitted_at':
        if order == 'asc':
            query = query.order_by(Task.submitted_at)
        else:
            query = query.order_by(Task.submitted_at.desc())

    tasks = query.limit(limit).all()
    return jsonify([task.to_dict() for task in tasks])

if _name_ == '_main_':
    app.run(debug=True)