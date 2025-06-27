from app import db
from flask import url_for


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    details_model = db.Column(db.String, nullable=False)
    parent_category_id = db.Column(db.Integer, db.ForeignKey("category.id", ondelete="SET NULL"), nullable=True)

    def __repr__(self):
        return f'<Name {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'details_model': self.details_model,
            'parent_category': self.parent_category_id
        }
    

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    

    def __repr__(self):
        return f'<Inventory {self.name}'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address
        }
    

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    buy_price = db.Column(db.Float, nullable=False)
    desc = db.Column(db.String, nullable=True)
    sell_price = db.Column(db.Float, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id", ondelete="SET NULL"), nullable=True)
    category_details = db.Column(db.String, nullable=True)
    product_image = db.Column(db.String, nullable = True)

    def __repr__(self):
        return f'<Name {self.name}>'
    
    
    def to_dict(self):
        image_url = None
        if self.product_image:
            image_url = url_for('products.get_product_image', filename=self.product_image, _external=True)

        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'category_id': self.category_id,
            'category_details': self.category_details,
            'product_image': image_url
        }
    

class Stock(db.Model):
    __tablename__ = 'stock'

    id = db.Column(db.Integer, primary_key=True, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="SET NULL"), nullable=False)
    inventory_location_id = db.Column(db.Integer, db.ForeignKey("inventory.id", ondelete="SET NULL"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Units: {self.quantity}> <Product: {self.product_id}> <Inventory: {self.inventory_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'inventory_location_id': self.inventory_location_id,
            'quantity': self.quantity
        }