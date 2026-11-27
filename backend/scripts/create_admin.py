import argparse
import getpass
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from database.db import check_db_health, get_db
from models.user_model import UserModel
from utils.decorators import record_audit_log
from utils.validators import validate_email, validate_password


def main():
    parser = argparse.ArgumentParser(description="Provision an administrator account.")
    parser.add_argument("--email", help="Administrator email")
    parser.add_argument("--password", help="Administrator password (min 16 chars)")
    parser.add_argument("--name", default="Platform Administrator", help="Full name")
    parser.add_argument("--phone", default="+10000000000", help="Phone number")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        ok, err = check_db_health(app)
        if not ok:
            print(f"Error: MongoDB is unavailable ({err}). Set MONGO_URI in backend/.env.")
            sys.exit(1)

        email = (args.email or input("Administrator email: ")).strip().lower()
        if not validate_email(email):
            print("Error: Invalid email address.")
            sys.exit(1)

        if UserModel.find_by_email(email):
            print(f"Error: An account with email '{email}' already exists.")
            sys.exit(1)

        password = args.password or getpass.getpass("Administrator password (min 16 characters): ")
        if not args.password:
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Error: Passwords do not match.")
                sys.exit(1)

        ok_pw, pw_err = validate_password(password, min_length=16)
        if not ok_pw:
            print(f"Error: {pw_err}")
            sys.exit(1)

        admin_doc = UserModel.create(
            full_name=args.name.strip() or "Platform Administrator",
            email=email,
            phone=args.phone.strip() or "+10000000000",
            password=password,
            role="admin",
            account_status="active",
        )
        record_audit_log(str(admin_doc["_id"]), "ADMIN_PROVISIONED", "user", str(admin_doc["_id"]))
        print(f"Administrator account created for {email} (id={admin_doc['_id']}).")


if __name__ == "__main__":
    main()
