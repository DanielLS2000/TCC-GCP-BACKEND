from auth.models import User #

def test_new_user(new_user_payload):
    """
    Test User model creation and password setting/checking.
    """
    user = User(
        username=new_user_payload["username"],
        email=new_user_payload["email"],
        role=new_user_payload["role"]
    )
    user.set_password(new_user_payload["password"]) #

    assert user.username == new_user_payload["username"]
    assert user.email == new_user_payload["email"]
    assert user.role == new_user_payload["role"]
    assert user.password_hash is not None
    assert user.password_hash != new_user_payload["password"] # Ensure it's hashed
    assert user.check_password(new_user_payload["password"]) #
    assert not user.check_password("wrongpassword")

def test_user_to_dict(new_user_payload):
    """
    Test the to_dict method of the User model.
    """
    user = User(
        id=1, # Simulate an ID as it's normally DB-generated
        username=new_user_payload["username"],
        email=new_user_payload["email"],
        role=new_user_payload["role"]
    )
    user_dict = user.to_dict() #

    expected_dict = {
        'id': 1,
        'username': new_user_payload["username"],
        'email': new_user_payload["email"],
        'role': new_user_payload["role"]
    }
    assert user_dict == expected_dict
    assert "password_hash" not in user_dict # Ensure password hash is not exposed

def test_user_repr(new_user_payload):
    """
    Test the __repr__ method of the User model.
    """
    user = User(username=new_user_payload["username"])
    assert repr(user) == f'<User {new_user_payload["username"]}>' #