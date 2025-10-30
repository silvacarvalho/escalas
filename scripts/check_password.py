#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from database import SessionLocal
from models import Usuario
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def check_user(username, password):
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.nome_usuario == username).first()
        if not user:
            print(f"User not found: {username}")
            return 2
        print(f"Found user: {user.nome_usuario} (id={user.id})")
        print(f"Stored hash: {user.senha_hash}")
        try:
            ok = pwd_context.verify(password, user.senha_hash)
        except Exception as e:
            print(f"Error verifying password: {e}")
            return 3
        print(f"verify('{password}', stored_hash) -> {ok}")
        return 0 if ok else 1
    finally:
        db.close()

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('username')
    p.add_argument('password')
    args = p.parse_args()
    exit_code = check_user(args.username, args.password)
    sys.exit(exit_code)
