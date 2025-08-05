"""Add dataset and dataset_image tables

This migration adds the dataset and dataset_image tables to support
multi-image dataset creation and management.
"""

from sqlalchemy import text
from app.core.database import engine

def upgrade():
    """Add dataset tables."""
    with engine.connect() as conn:
        # Create datasets table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                trigger_word VARCHAR NOT NULL,
                caption_template TEXT,
                auto_caption BOOLEAN DEFAULT 1,
                resize_images BOOLEAN DEFAULT 1,
                crop_images BOOLEAN DEFAULT 1,
                flip_images BOOLEAN DEFAULT 0,
                quality_filter VARCHAR DEFAULT 'basic',
                image_count INTEGER DEFAULT 0,
                status VARCHAR DEFAULT 'created',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create dataset_images table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dataset_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                filename VARCHAR NOT NULL,
                original_filename VARCHAR NOT NULL,
                caption TEXT,
                processed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            )
        """))
        
        conn.commit()
        print("Dataset tables created successfully!")

def downgrade():
    """Remove dataset tables."""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS dataset_images"))
        conn.execute(text("DROP TABLE IF EXISTS datasets"))
        conn.commit()
        print("Dataset tables removed successfully!")

if __name__ == "__main__":
    upgrade()
