from app import create_app, db, login, moment

app = create_app()

@app.shell_context_processor
def make_shell_context():
    from app.models import (
            User, Group, Comment, Category, Product, Option, Order, Item, Page, Setting, Information
        )
    return {
        'db': db, 
        'login': login,
        'moment': moment,
        'User': User,
        'Group': Group,
        'Comment': Comment,
        'Category': Category,
        'Product': Product,
        'Option': Option,
        'Order': Order,
        'Item': Item,
        'Page': Page,
        'Setting': Setting,
        'Information': Information,
    }
