from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Task

task_bp = Blueprint('tasks', _name_)

@task_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    data = request.get_json()
    if data['estimated_time_minutes'] <= 0:
        return jsonify({'error': 'Time must be > 0'}), 400
    if Task.query.filter_by(task_str_id=data['task_str_id']).first():
        return jsonify({'error': 'Task ID already exists'}), 400

    task = Task(
        task_str_id=data['task_str_id'],
        description=data.get('description', ''),
        estimated_time_minutes=data['estimated_time_minutes'],
        priority=data.get('priority', 3),
        user_id=user_id
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'task_str_id': task.task_str_id, 'status': task.status}), 201

@task_bp.route('/<string:task_str_id>', methods=['GET'])
@jwt_required()
def get_task(task_str_id):
    user_id = get_jwt_identity()
    task = Task.query.filter_by(task_str_id=task_str_id, user_id=user_id).first()
    if not task:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(task_to_dict(task))

@task_bp.route('/<string:task_str_id>/status', methods=['PUT'])
@jwt_required()
def update_status(task_str_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    task = Task.query.filter_by(task_str_id=task_str_id, user_id=user_id).first()
    if not task:
        return jsonify({'error': 'Not found'}), 404

    allowed = ['pending', 'processing', 'completed']
    if data['new_status'] not in allowed:
        return jsonify({'error': 'Invalid status'}), 400

    if task.status == 'completed' and data['new_status'] != 'completed':
        return jsonify({'error': 'Cannot regress from completed'}), 400

    task.status = data['new_status']
    db.session.commit()
    return jsonify(task_to_dict(task))

@task_bp.route('/next-to-process', methods=['GET'])
@jwt_required()
def next_to_process():
    user_id = get_jwt_identity()
    task = Task.query.filter_by(status='pending', user_id=user_id)\
        .order_by(Task.priority, Task.estimated_time_minutes, Task.submitted_at).first()
    if not task:
        return jsonify({'error': 'No pending tasks'}), 404
    return jsonify(task_to_dict(task))

@task_bp.route('/pending', methods=['GET'])
@jwt_required()
def list_pending():
    user_id = get_jwt_identity()
    sort_by = request.args.get('sort_by', 'priority')
    order = request.args.get('order', 'asc')
    limit = int(request.args.get('limit', 10))

    query = Task.query.filter_by(status='pending', user_id=user_id)

    if sort_by == 'time':
        column = Task.estimated_time_minutes
    elif sort_by == 'submitted':
        column = Task.submitted_at
    else:
        column = Task.priority

    if order == 'desc':
        query = query.order_by(column.desc())
    else:
        query = query.order_by(column.asc())

    tasks = query.limit(limit).all()
    return jsonify([task_to_dict(t) for t in tasks])

def task_to_dict(task):
    return {
        'task_str_id': task.task_str_id,
        'description': task.description,
        'estimated_time_minutes': task.estimated_time_minutes,
        'status': task.status,
        'submitted_at': task.submitted_at.isoformat(),
        'priority': task.priority
    }
