def reset_db(db):
    from sales.models import SaleOrder, SaleItem
    
    print("Resetando o banco de dados...")
    db.drop_all()
    db.create_all()
    print("Banco de dados resetado com sucesso.")

def init_db(db):
    print("Criando tabelas no banco de dados...")
    db.create_all()
    print("Tabelas criadas com sucesso.")