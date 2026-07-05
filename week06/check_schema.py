import sqlite3


def main():
    connection = sqlite3.connect("data/app.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'documents'
        """
    )

    row = cursor.fetchone()

    print(row[0])

    connection.close()


if __name__ == "__main__":
    main()