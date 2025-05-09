def reset_db(db):
    from app.models import Employee
    
    print("Resetando o banco de dados...")
    db.drop_all()
    db.create_all()
    print("Banco de dados resetado com sucesso.")

def init_db(db):
    print("Criando tabelas no banco de dados...")
    db.create_all()
    print("Tabelas criadas com sucesso.")