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
    try:
        employees = Employee.query.order_by(Employee.created_at.desc()).all()
        return render_template('employees/list.html', employees=employees)
    except Exception as e:
        flash(f'Database error: {str(e)}', 'danger')
        return render_template('employees/list.html', employees=[])


@employee_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        emp_id        = request.form.get('employee_id', '').strip()
        name          = request.form.get('name', '').strip()
        dept          = request.form.get('department', '').strip()
        email         = request.form.get('email', '').strip()
        mobile        = request.form.get('mobile', '').strip()
        joining_date_str = request.form.get('joining_date', '')

        if not all([emp_id, name, dept, email, mobile, joining_date_str]):
            flash('All fields are required.', 'danger')
            return redirect(request.url)

        try:
            joining_date = datetime.datetime.strptime(joining_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(request.url)

        try:
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
        except Exception as e:
            db.session.rollback()
            flash(f'Database error: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('employees/form.html', employee=None)


@employee_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    try:
        emp = Employee.query.get_or_404(id)
    except Exception as e:
        flash(f'Error loading employee: {str(e)}', 'danger')
        return redirect(url_for('employee.list_employees'))

    if request.method == 'POST':
        try:
            emp.name       = request.form.get('name', emp.name).strip()
            emp.department = request.form.get('department', emp.department).strip()
            emp.email      = request.form.get('email', emp.email).strip()
            emp.mobile     = request.form.get('mobile', emp.mobile).strip()
            db.session.commit()
            flash('Employee updated successfully.', 'success')
            return redirect(url_for('employee.list_employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Update failed: {str(e)}', 'danger')

    return render_template('employees/form.html', employee=emp)


@employee_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    try:
        emp = Employee.query.get_or_404(id)
        db.session.delete(emp)
        db.session.commit()
        flash('Employee deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Delete failed: {str(e)}', 'danger')
    return redirect(url_for('employee.list_employees'))


@employee_bp.route('/register_face/<int:emp_id>', methods=['GET', 'POST'])
@login_required
def register_face(emp_id):
    try:
        emp = Employee.query.get_or_404(emp_id)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Employee not found: {str(e)}'})

    if request.method == 'POST':
        try:
            data = request.json
            images_base64 = data.get('images', [])

            if not images_base64:
                return jsonify({'success': False, 'message': 'No images received.'})

            # Save images to dataset folder
            emp_dir = os.path.join(Config.DATASET_DIR, emp.employee_id)
            os.makedirs(emp_dir, exist_ok=True)

            saved_paths = []
            for i, img_b64 in enumerate(images_base64):
                if ',' in img_b64:
                    _, encoded = img_b64.split(',', 1)
                else:
                    encoded = img_b64
                img_data = base64.b64decode(encoded)
                path = os.path.join(emp_dir, f'{i}.jpg')
                with open(path, 'wb') as f:
                    f.write(img_data)
                saved_paths.append(path)

            # Generate face encoding from saved images
            encoding = generate_face_encoding(saved_paths)
            if encoding is not None:
                emp.set_encoding(encoding)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Face registered successfully!'})
            else:
                return jsonify({'success': False,
                                'message': 'No face detected in the images. Please ensure your face is clearly visible and try again.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})

    return render_template('employees/register_face.html', employee=emp)
