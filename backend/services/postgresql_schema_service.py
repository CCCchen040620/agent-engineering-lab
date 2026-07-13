def initialize_postgresql_knowledge_schema(connection) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE EXTENSION IF NOT EXISTS vector
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL UNIQUE,
                file_type TEXT NOT NULL,
                chunk_count INTEGER NOT NULL,
                is_indexed BOOLEAN NOT NULL DEFAULT FALSE,
                source TEXT NOT NULL DEFAULT 'production',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        cursor.execute(
            """
            ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'production'
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                chunk_index INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chunk_embeddings (
                id SERIAL PRIMARY KEY,
                chunk_id INTEGER NOT NULL UNIQUE REFERENCES chunks(id) ON DELETE CASCADE,
                embedding vector(1024) NOT NULL,
                model TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

    connection.commit()

    return {
        "vector_extension_ready": True,
        "documents_table_ready": True,
        "documents_source_column_ready": True,
        "chunks_table_ready": True,
        "chunk_embeddings_table_ready": True,
    }
