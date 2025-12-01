from app.database import Base, engine


def clear_all() -> None:
    # Drop and recreate tables so schema stays in sync with models.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def main() -> None:
    clear_all()
    print("Database reset: tables dropped and recreated.")


if __name__ == "__main__":
    main()


