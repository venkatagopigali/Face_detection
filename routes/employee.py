from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db
from models.employee import Employee
import os
from config import Config
from face_engine.engine import generate_face_encoding
import base64
import datetime

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

@employee_bp.route('/')
@login_required
def list_employees():
    employees = Employee.query.all()
    return render_template('employees/list.html', employees=employees)

@employee_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        emp_id = request.form.get('employee_id')
        name = request.form.get('name')
        dept = request.form.get('department')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        joining_date_str = request.form.get('joining_date')
        
        try:
            joining_date = datetime.datetime.strptime(joining_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(request.url)

        if Employee.query.filter_by(employee_id=emp_id).first():
            flash('Employee ID already exists.', 'danger')
            return redirect(request.url)
            
        new_emp = Employee(
            employee_id=emp_id, name=name, department=dept,
            email=email, mobile=mobile, joining_date=joining_date
        )
        db.session.add(new_emp)
        db.session.commit()
        
        flash('Employee added successfully. Please register their face next.', 'success')
        return redirect(url_for('employee.register_face', emp_id=new_emp.id))
        
    return render_template('employees/form.html', employee=None)

@employee_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    emp = Employee.query.get_or_404(id)
    if request.method == 'POST':
        emp.name = request.form.get('name')
        emp.department = request.form.get('department')
        emp.email = request.form.get('email')
        emp.mobile = request.form.get('mobile')
        db.session.commit()
        flash('Employee updated.', 'success')
        return redirect(url_for('employee.list_employees'))
    return render_template('employees/form.html', employee=emp)

@employee_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    emp = Employee.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    flash('Employee deleted.', 'success')
    return redirect(url_for('employee.list_employees'))

@employee_bp.route('/register_face/<int:emp_id>', methods=['GET', 'POST'])
@login_required
def register_face(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    
    if request.method == 'POST':
        # Handle captured images via AJAX
        data = request.json
        images_base64 = data.get('images', [])
        
        if not images_base64:
            return jsonify({'success': False, 'message': 'No images received'})
            
        # Create temp dir for images
        emp_dir = os.path.join(Config.DATASET_DIR, emp.employee_id)
        os.makedirs(emp_dir, exist_ok=True)
        
        saved_paths = []
        for i, img_b64 in enumerate(images_base64):
            # Strip header "data:image/jpeg;base64,"
            if "," in img_b64:
                header, encoded = img_b64.split(",", 1)
            else:
                encoded = img_b64
            img_data = base64.b64decode(encoded)
            path = os.path.join(emp_dir, f"{i}.jpg")
            with open(path, "wb") as f:
                f.write(img_data)
            saved_paths.append(path)
            
        # Generate encoding
        encoding = generate_face_encoding(saved_paths)
        if encoding is not None:
            emp.set_encoding(encoding)
            db.session.commit()
            
            # Clean up images (optional, keeping them for dataset might be good)
            return jsonify({'success': True, 'message': 'Face registered successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Could not detect face in images. Please try again.'})
            
    return render_template('employees/register_face.html', employee=emp)
