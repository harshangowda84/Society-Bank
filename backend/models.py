from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, Float, Date, ForeignKey
)
from sqlalchemy.orm import relationship
from db import Base
from werkzeug.security import generate_password_hash, check_password_hash

class Member(Base):
    __tablename__ = "member"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True)
    password = Column(String, nullable=True)
    dob = Column(String)
    designation = Column(String)
    mobile = Column(String)
    bank_account = Column(String)
    aadhaar = Column(String)
    pan = Column(String)
    is_approved = Column(Boolean, default=False)
    application_date = Column(String)

    accounts = relationship("Account", back_populates="member", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="member", cascade="all, delete-orphan")
    deposits = relationship("Deposit", back_populates="member", cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        if raw_password:
            self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        if not self.password:
            return False
        return check_password_hash(self.password, raw_password)

    def __repr__(self) -> str:
        return f"<Member id={self.id} name={self.name}>"

class Account(Base):
    __tablename__ = "account"
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., Savings, Current
    balance = Column(Float, default=0.0)
    status = Column(String(20), default='Active')
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

class Loan(Base):
    __tablename__ = "loan"
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False)
    amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    status = Column(String(20), default='Pending')
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", back_populates="loans")

class Deposit(Base):
    __tablename__ = "deposit"
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(50), nullable=False)  # e.g., Fixed, Recurring
    maturity_date = Column(Date)
    status = Column(String(20), default='Active')
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", back_populates="deposits")

class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    type = Column(String(20), nullable=False)  # Credit/Debit
    amount = Column(Float, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="transactions")

class Announcement(Base):
    __tablename__ = "announcement"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)