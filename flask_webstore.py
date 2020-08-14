from app import create_app, db, login, moment

app = create_app()

@app.shell_context_processor
def make_shell_context():
    from app.models import (
            User, Group, Comment, Product, 
        )
    return {
        'db': db, 
        'login': login,
        'moment': moment,
        'User': User,
        'Group': Group,
        'Comment': Comment,
        'Product': Product,
    }
