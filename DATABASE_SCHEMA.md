# Society Bank - Database Schema (ER Diagram)

## Entities and Relationships

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SOCIETY BANK DATABASE                          │
└─────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════╗
║         MEMBER            ║
╠═══════════════════════════╣
║ 🔑 id (PK)                ║
║ • name                    ║
║ • username (UNIQUE)       ║
║ • password_hash           ║
║ • account_no (UNIQUE)     ║
║ • dob                     ║
║ • designation             ║
║ • mobile                  ║
║ • bank_account            ║
║ • aadhaar                 ║
║ • pan                     ║
║ • application_date        ║
║ • is_approved             ║
║ • created_at              ║
╚═══════════════════════════╝
         │
         │ 1:N
         ├──────────────────────────────────┐
         │                                  │
         ▼                                  ▼
╔═══════════════════════════╗    ╔═══════════════════════════╗
║        ACCOUNT            ║    ║         LOAN              ║
╠═══════════════════════════╣    ╠═══════════════════════════╣
║ 🔑 id (PK)                ║    ║ 🔑 id (PK)                ║
║ 🔗 member_id (FK)         ║    ║ 🔗 member_id (FK)         ║
║ • account_number          ║    ║ • amount                  ║
║ • balance                 ║    ║ • interest_rate           ║
║ • account_type            ║    ║ • tenure_months           ║
║ • created_at              ║    ║ • status                  ║
╚═══════════════════════════╝    ║ • repayment_status        ║
         │                        ║ • office_approved         ║
         │ 1:N                    ║ • office_note             ║
         │                        ║ • approved_at             ║
         ▼                        ║ • created_at              ║
╔═══════════════════════════╗    ╚═══════════════════════════╝
║      TRANSACTION          ║              │
╠═══════════════════════════╣              │ 1:N
║ 🔑 id (PK)                ║              │
║ 🔗 account_id (FK)        ║              ▼
║ • type                    ║    ╔═══════════════════════════╗
║ • amount                  ║    ║    LOAN_REPAYMENT         ║
║ • description             ║    ╠═══════════════════════════╣
║ • created_at              ║    ║ 🔑 id (PK)                ║
╚═══════════════════════════╝    ║ 🔗 loan_id (FK)           ║
                                 ║ • principal_paid          ║
         ┌─────────────────────┐ ║ • interest_paid           ║
         │                     │ ║ • payment_method          ║
         ▼                     ▼ ║ • payment_date            ║
╔═══════════════════════════╗ ╔═══════════════════════════╗
║        DEPOSIT            ║ ║         SHARE             ║
║     (Fixed Deposit)       ║ ║                           ║
╠═══════════════════════════╣ ╠═══════════════════════════╣
║ 🔑 id (PK)                ║ ║ 🔑 id (PK)                ║
║ 🔗 member_id (FK)         ║ ║ 🔗 member_id (FK)         ║
║ • amount                  ║ ║ • quantity                ║
║ • type                    ║ ║ • amount_per_share        ║
║ • maturity_date           ║ ║ • total_amount            ║
║ • tenure_months           ║ ║ • status                  ║
║ • interest_mode           ║ ║ • office_approved         ║
║ • nominee_name            ║ ║ • office_note             ║
║ • nominee_relationship    ║ ║ • approved_at             ║
║ • nominee_dob             ║ ║ • created_at              ║
║ • status                  ║ ╚═══════════════════════════╝
║ • office_approved         ║
║ • office_note             ║
║ • approved_at             ║           ╔═══════════════════════════╗
║ • created_at              ║           ║     ANNOUNCEMENT          ║
╚═══════════════════════════╝           ╠═══════════════════════════╣
                                        ║ 🔑 id (PK)                ║
                                        ║ • message                 ║
                                        ║ • created_at              ║
                                        ╚═══════════════════════════╝

Legend:
🔑 = Primary Key
🔗 = Foreign Key
• = Regular Attribute
1:N = One-to-Many Relationship
```

## Relationships

### 1. MEMBER → ACCOUNT (One-to-Many)
- One member can have multiple accounts
- Foreign Key: `account.member_id → member.id`

### 2. MEMBER → LOAN (One-to-Many)
- One member can have multiple loans
- Foreign Key: `loan.member_id → member.id`

### 3. MEMBER → DEPOSIT (One-to-Many)
- One member can have multiple fixed deposits
- Foreign Key: `deposit.member_id → member.id`

### 4. MEMBER → SHARE (One-to-Many)
- One member can have multiple share investments
- Foreign Key: `share.member_id → member.id`

### 5. ACCOUNT → TRANSACTION (One-to-Many)
- One account can have multiple transactions
- Foreign Key: `transaction.account_id → account.id`

### 6. LOAN → LOAN_REPAYMENT (One-to-Many)
- One loan can have multiple repayment records
- Foreign Key: `loan_repayment.loan_id → loan.id`

### 7. ANNOUNCEMENT (Independent)
- No foreign key relationships
- Standalone entity for system-wide announcements

## Field Types Summary

### Member
- `id`: Integer, Auto-increment
- `name`: String(100)
- `username`: String(50), Unique
- `password_hash`: String(200)
- `account_no`: String(20), Unique
- `is_approved`: Boolean, Default False
- `created_at`: DateTime

### Account
- `balance`: Decimal(15,2), Default 0.00
- `account_type`: String(50), e.g., "Savings"

### Loan
- `amount`: Decimal(15,2)
- `interest_rate`: Decimal(5,2)
- `tenure_months`: Integer
- `status`: String(20), e.g., "Pending", "Approved", "Rejected"
- `repayment_status`: String(20), e.g., "Active", "Completed"

### Deposit (Fixed Deposit)
- `amount`: Decimal(15,2)
- `type`: String(20), e.g., "Fixed", "Recurring"
- `interest_mode`: String(20), e.g., "Monthly", "Cumulative"
- `maturity_date`: Date
- `nominee_*`: Optional nominee details

### Share
- `quantity`: Integer
- `amount_per_share`: Decimal(10,2)
- `total_amount`: Decimal(15,2)

### Transaction
- `type`: String(20), e.g., "Credit", "Debit"
- `amount`: Decimal(15,2)
- `description`: Text

### Loan_Repayment
- `principal_paid`: Decimal(15,2)
- `interest_paid`: Decimal(15,2)
- `payment_method`: String(50)
- `payment_date`: DateTime

## Indexes
- `member.username` (UNIQUE)
- `member.account_no` (UNIQUE)
- `account.member_id` (Foreign Key Index)
- `loan.member_id` (Foreign Key Index)
- `deposit.member_id` (Foreign Key Index)
- `share.member_id` (Foreign Key Index)
- `transaction.account_id` (Foreign Key Index)
- `loan_repayment.loan_id` (Foreign Key Index)
