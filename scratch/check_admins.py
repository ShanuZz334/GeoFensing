import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from flask import Flask
from backend.app import create_app
from backend.app.models.admin import Admin

app = create_app()
with app.app_context():
    admins = Admin.query.all()
    for admin in admins:
        print(f"ID: {admin.id}, RegNo: {admin.reg_no}, Name: {admin.name}, IsHead: {admin.is_head_admin}")
