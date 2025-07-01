from hr import db
from datetime import datetime

class Employee(db.Model):
    __tablename__ = 'employee'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    hiredate = db.Column(db.DateTime, nullable=False, default=datetime.now)
    status = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<Name {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'role': self.role,
            'salary': self.salary,
            'hiredate': self.hiredate,
            'status': self.status
        }