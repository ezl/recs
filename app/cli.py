import click
from flask.cli import with_appcontext
from app.database import db
from app.database.models import User, Post

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    db.drop_all()
    db.create_all()
    click.echo('Initialized the database.')

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Seed the database with sample data."""
    # Create a sample user
    user = User(
        email='admin@example.com',
        name='Admin User',
        password='password'  # In a real app, this would be hashed
    )
    db.session.add(user)
    db.session.commit()
    
    # Create sample posts
    posts = [
        Post(
            title='Welcome to Flask Starter',
            content='This is the first post in our Flask Starter App.',
            published=True,
            author_id=user.id
        ),
        Post(
            title='Using SQLAlchemy with Flask',
            content='SQLAlchemy provides a nice abstraction for database operations.',
            published=True,
            author_id=user.id
        ),
        Post(
            title='Draft Post',
            content='This is a draft post that is not published.',
            published=False,
            author_id=user.id
        )
    ]
    
    db.session.add_all(posts)
    db.session.commit()
    
    click.echo(f'Added user: {user.email}')
    click.echo(f'Added {len(posts)} posts')

def init_app(app):
    """Register database commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command) 