from sales import db

class SaleOrder(db.Model):
    __tablename__ = 'saleorder'

    id = db.Column(db.Integer, primary_key=True, index=True)
    client_id = db.Column(db.Integer, nullable=False)
    employee_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Sale Order>\n<ID {self.id}>\n<Client ID {self.client_id}>\n<Employee ID {self.employee_id}>\n<Date {self.date}>\n<Payment Method {self.payment_method}>\n<Status {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'employee_id': self.employee_id,
            'date': self.date.isoformat() if self.date else None,
            'payment_method': self.payment_method,
            'status': self.status
        }
    
class SaleItem(db.Model):
    __tablename__ = 'saleitem'

    id = db.Column(db.Integer, primary_key=True, index=True)
    sale_order_id = db.Column(db.Integer, db.ForeignKey('saleorder.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<Sale Item>\n<ID {self.id}>\n<Product ID {self.product_id}>\n<Quantity {self.quantity}>\n<Price {self.price}>\n<Discount {self.discount}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'sale_order_id': self.sale_order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
            'discount': self.discount
        }