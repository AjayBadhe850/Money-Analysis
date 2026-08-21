from datetime import date, datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, Base, engine
from app.models.company import Company
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.category import Category
from app.models.vendor import Vendor
from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.alert import CostAlert, AlertSeverity, AlertStatus, CostRecommendation
from app.models.audit import AuditLog
from app.models.future_ai import ApprovalRequest, Anomaly
from app.auth.hashing import hash_password
from app.services.budget_service import sync_budget_spent


def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        existing_company = db.query(Company).first()
        if existing_company:
            print("[INFO] Database already contains data. Ensuring seed consistency...")
            company = existing_company
        else:
            # 1. Create Company
            company = Company(
                name="Acme Global Technologies Inc.",
                industry="Software & AI Enterprise",
                currency="USD",
                fiscal_year_start="January"
            )
            db.add(company)
            db.commit()
            db.refresh(company)
            print(f"[OK] Company created: {company.name}")

        # 2. Create Users with different roles
        default_pwd = hash_password("Password123!")
        users_data = [
            {"name": "Eleanor Vance (Admin)", "email": "admin@moneyanalysis.ai", "role": UserRole.ADMIN},
            {"name": "Marcus Sterling (Finance)", "email": "finance@moneyanalysis.ai", "role": UserRole.FINANCE_MANAGER},
            {"name": "Dr. Sarah Chen (Eng Lead)", "email": "engineering.lead@moneyanalysis.ai", "role": UserRole.DEPARTMENT_MANAGER},
            {"name": "Jordan Rivera (Employee)", "email": "employee@moneyanalysis.ai", "role": UserRole.EMPLOYEE},
            {"name": "Arthur Pendelton (Auditor)", "email": "auditor@moneyanalysis.ai", "role": UserRole.AUDITOR},
        ]
        
        users_map = {}
        for u in users_data:
            user = db.query(User).filter(User.email == u["email"]).first()
            if not user:
                user = User(
                    name=u["name"],
                    email=u["email"],
                    password_hash=default_pwd,
                    role=u["role"],
                    company_id=company.id
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            users_map[u["role"]] = user
        print(f"[OK] {len(users_data)} Users ensured with password 'Password123!'")

        # 3. Create 6 Departments
        departments_data = [
            "Engineering & Product",
            "Sales & Revenue",
            "Growth & Marketing",
            "People & HR",
            "Finance & Operations",
            "Legal & Compliance"
        ]
        depts_map = {}
        for d_name in departments_data:
            dept = db.query(Department).filter(Department.name == d_name, Department.company_id == company.id).first()
            if not dept:
                dept = Department(
                    name=d_name,
                    company_id=company.id,
                    manager_id=users_map[UserRole.DEPARTMENT_MANAGER].id if d_name == "Engineering & Product" else None
                )
                db.add(dept)
                db.commit()
                db.refresh(dept)
            depts_map[d_name] = dept
        print(f"[OK] {len(departments_data)} Departments ensured")

        # 4. Create 12 Categories
        categories_data = [
            ("Cloud Infrastructure", "#6366F1"),
            ("SaaS Software", "#8B5CF6"),
            ("Payroll & Benefits", "#10B981"),
            ("Digital Marketing", "#F59E0B"),
            ("Facilities & Rent", "#EC4899"),
            ("Travel & Entertainment", "#3B82F6"),
            ("Procurement & Hardware", "#14B8A6"),
            ("Legal & Compliance", "#64748B"),
            ("Professional Services", "#06B6D4"),
            ("Office Utilities", "#84CC16"),
            ("Logistics & Shipping", "#D97706"),
            ("Hardware Maintenance", "#E11D48"),
        ]
        cats_map = {}
        for cat_name, color in categories_data:
            cat = db.query(Category).filter(Category.name == cat_name, Category.company_id == company.id).first()
            if not cat:
                cat = Category(
                    name=cat_name,
                    color_code=color,
                    company_id=company.id
                )
                db.add(cat)
                db.commit()
                db.refresh(cat)
            cats_map[cat_name] = cat
        print(f"[OK] {len(categories_data)} Categories ensured")

        # 5. Create 20 Vendors
        vendors_data = [
            {"name": "Amazon Web Services (AWS)", "email": "billing@aws.amazon.com", "cat": "Cloud Infrastructure", "rel": 96, "qual": 94, "days": 1},
            {"name": "Google Cloud Platform", "email": "accounts@google.com", "cat": "Cloud Infrastructure", "rel": 95, "qual": 95, "days": 1},
            {"name": "Microsoft Azure & 365", "email": "billing@microsoft.com", "cat": "Cloud Infrastructure", "rel": 92, "qual": 90, "days": 2},
            {"name": "Salesforce Inc.", "email": "invoicing@salesforce.com", "cat": "SaaS Software", "rel": 88, "qual": 91, "days": 3},
            {"name": "HubSpot", "email": "billing@hubspot.com", "cat": "Digital Marketing", "rel": 90, "qual": 89, "days": 2},
            {"name": "Snowflake Inc.", "email": "accounts@snowflake.com", "cat": "Cloud Infrastructure", "rel": 94, "qual": 93, "days": 1},
            {"name": "Datadog Inc.", "email": "billing@datadoghq.com", "cat": "Cloud Infrastructure", "rel": 97, "qual": 95, "days": 1},
            {"name": "Slack Technologies", "email": "billing@slack.com", "cat": "SaaS Software", "rel": 99, "qual": 98, "days": 1},
            {"name": "Zoom Video Communications", "email": "billing@zoom.us", "cat": "SaaS Software", "rel": 93, "qual": 91, "days": 1},
            {"name": "WeWork Global", "email": "leasing@wework.com", "cat": "Facilities & Rent", "rel": 84, "qual": 82, "days": 5},
            {"name": "Stripe Payments", "email": "merchant@stripe.com", "cat": "Professional Services", "rel": 99, "qual": 99, "days": 1},
            {"name": "Delta Airlines Corporate", "email": "business@delta.com", "cat": "Travel & Entertainment", "rel": 86, "qual": 85, "days": 4},
            {"name": "GitHub Inc.", "email": "billing@github.com", "cat": "SaaS Software", "rel": 98, "qual": 97, "days": 1},
            {"name": "OpenAI", "email": "enterprise@openai.com", "cat": "SaaS Software", "rel": 94, "qual": 96, "days": 1},
            {"name": "Figma Inc.", "email": "billing@figma.com", "cat": "SaaS Software", "rel": 97, "qual": 96, "days": 1},
            {"name": "Notion Labs", "email": "sales@notion.so", "cat": "SaaS Software", "rel": 95, "qual": 94, "days": 1},
            {"name": "Workday Inc.", "email": "invoicing@workday.com", "cat": "Payroll & Benefits", "rel": 91, "qual": 90, "days": 3},
            {"name": "Asana Inc.", "email": "accounts@asana.com", "cat": "SaaS Software", "rel": 92, "qual": 91, "days": 1},
            {"name": "MongoDB Atlas", "email": "cloud@mongodb.com", "cat": "Cloud Infrastructure", "rel": 96, "qual": 95, "days": 1},
            {"name": "Cloudflare Inc.", "email": "billing@cloudflare.com", "cat": "Cloud Infrastructure", "rel": 99, "qual": 98, "days": 1},
        ]
        vendors_map = {}
        for v in vendors_data:
            vend = db.query(Vendor).filter(Vendor.name == v["name"], Vendor.company_id == company.id).first()
            if not vend:
                vend = Vendor(
                    name=v["name"],
                    contact_email=v["email"],
                    category=v["cat"],
                    reliability_score=v["rel"],
                    quality_score=v["qual"],
                    average_delivery_days=v["days"],
                    company_id=company.id
                )
                db.add(vend)
                db.commit()
                db.refresh(vend)
            vendors_map[v["name"]] = vend
        print(f"[OK] {len(vendors_data)} Vendors ensured")

        # 6. Create 20 Subscriptions with license wastage
        subscriptions_data = [
            {"service": "AWS Enterprise Cloud Support", "vendor": "Amazon Web Services (AWS)", "dept": "Engineering & Product", "cost": 18500.0, "tot_lic": 80, "act_lic": 68, "ren_days": 45},
            {"service": "Google Cloud BigQuery & Vertex AI", "vendor": "Google Cloud Platform", "dept": "Engineering & Product", "cost": 12400.0, "tot_lic": 50, "act_lic": 42, "ren_days": 90},
            {"service": "Salesforce Sales Cloud Unlimited", "vendor": "Salesforce Inc.", "dept": "Sales & Revenue", "cost": 9200.0, "tot_lic": 45, "act_lic": 27, "ren_days": 15},  # 18 wasted seats!
            {"service": "HubSpot Marketing Hub Enterprise", "vendor": "HubSpot", "dept": "Growth & Marketing", "cost": 4500.0, "tot_lic": 25, "act_lic": 19, "ren_days": 60},
            {"service": "Datadog Infrastructure Monitoring", "vendor": "Datadog Inc.", "dept": "Engineering & Product", "cost": 3800.0, "tot_lic": 120, "act_lic": 115, "ren_days": 120},
            {"service": "Snowflake Data Cloud Capacity", "vendor": "Snowflake Inc.", "dept": "Engineering & Product", "cost": 6200.0, "tot_lic": 30, "act_lic": 25, "ren_days": 180},
            {"service": "Microsoft 365 E5 Suite", "vendor": "Microsoft Azure & 365", "dept": "People & HR", "cost": 4200.0, "tot_lic": 150, "act_lic": 138, "ren_days": 30},
            {"service": "Slack Enterprise Grid", "vendor": "Slack Technologies", "dept": "People & HR", "cost": 2800.0, "tot_lic": 150, "act_lic": 145, "ren_days": 75},
            {"service": "Zoom Workplace Pro", "vendor": "Zoom Video Communications", "dept": "People & HR", "cost": 1950.0, "tot_lic": 110, "act_lic": 72, "ren_days": 20},   # 38 wasted seats!
            {"service": "GitHub Enterprise Cloud", "vendor": "GitHub Inc.", "dept": "Engineering & Product", "cost": 2100.0, "tot_lic": 90, "act_lic": 86, "ren_days": 110},
            {"service": "OpenAI ChatGPT Team & API Tier 4", "vendor": "OpenAI", "dept": "Engineering & Product", "cost": 3500.0, "tot_lic": 60, "act_lic": 54, "ren_days": 15},
            {"service": "Figma Enterprise Design", "vendor": "Figma Inc.", "dept": "Engineering & Product", "cost": 1800.0, "tot_lic": 40, "act_lic": 28, "ren_days": 140},
            {"service": "Notion Business Workspace", "vendor": "Notion Labs", "dept": "People & HR", "cost": 1200.0, "tot_lic": 120, "act_lic": 110, "ren_days": 200},
            {"service": "Workday HCM & Payroll", "vendor": "Workday Inc.", "dept": "People & HR", "cost": 7800.0, "tot_lic": 150, "act_lic": 150, "ren_days": 250},
            {"service": "Asana Enterprise Work Management", "vendor": "Asana Inc.", "dept": "Finance & Operations", "cost": 1600.0, "tot_lic": 60, "act_lic": 41, "ren_days": 85},
            {"service": "MongoDB Atlas Dedicated Cluster", "vendor": "MongoDB Atlas", "dept": "Engineering & Product", "cost": 2900.0, "tot_lic": 20, "act_lic": 19, "ren_days": 95},
            {"service": "Cloudflare Enterprise Security & CDN", "vendor": "Cloudflare Inc.", "dept": "Engineering & Product", "cost": 2400.0, "tot_lic": 30, "act_lic": 29, "ren_days": 160},
            {"service": "WeWork 12-Desk Dedicated Studio", "vendor": "WeWork Global", "dept": "Finance & Operations", "cost": 14000.0, "tot_lic": 12, "act_lic": 9, "ren_days": 35},
            {"service": "Atlassian Jira Software Enterprise", "vendor": "Slack Technologies", "dept": "Engineering & Product", "cost": 3100.0, "tot_lic": 100, "act_lic": 88, "ren_days": 55},
            {"service": "Adobe Creative Cloud All Apps", "vendor": "Figma Inc.", "dept": "Growth & Marketing", "cost": 1500.0, "tot_lic": 20, "act_lic": 13, "ren_days": 40},
        ]

        if db.query(Subscription).filter(Subscription.company_id == company.id).count() < 15:
            today = date.today()
            for s in subscriptions_data:
                v_obj = vendors_map.get(s["vendor"])
                d_obj = depts_map.get(s["dept"])
                sub = Subscription(
                    company_id=company.id,
                    department_id=d_obj.id if d_obj else None,
                    vendor_id=v_obj.id if v_obj else None,
                    vendor=s["vendor"],
                    service_name=s["service"],
                    monthly_cost=s["cost"],
                    total_licenses=s["tot_lic"],
                    active_licenses=s["act_lic"],
                    renewal_date=today + timedelta(days=s["ren_days"]),
                    status=SubscriptionStatus.ACTIVE
                )
                db.add(sub)
            db.commit()
            print(f"[OK] {len(subscriptions_data)} Subscriptions created with license wastage parameters")

        # 7. Create 12 Budgets (Department & Category allocations)
        budget_specs = [
            {"dept": "Engineering & Product", "cat": None, "year": 2026, "month": None, "alloc": 650000.0, "notes": "Core tech, cloud & tools"},
            {"dept": "Sales & Revenue", "cat": None, "year": 2026, "month": None, "alloc": 350000.0, "notes": "Sales commission & tools"},
            {"dept": "Growth & Marketing", "cat": None, "year": 2026, "month": None, "alloc": 420000.0, "notes": "Digital ad spend & brand"},
            {"dept": "People & HR", "cat": None, "year": 2026, "month": None, "alloc": 1250000.0, "notes": "Salaries, benefits & recruiting"},
            {"dept": "Finance & Operations", "cat": None, "year": 2026, "month": None, "alloc": 300000.0, "notes": "Offices, legal, banking"},
            {"dept": "Legal & Compliance", "cat": None, "year": 2026, "month": None, "alloc": 150000.0, "notes": "Auditing & regulatory counsel"},
            {"dept": None, "cat": "Cloud Infrastructure", "year": 2026, "month": None, "alloc": 480000.0, "notes": "AWS, GCP, Snowflake"},
            {"dept": None, "cat": "SaaS Software", "year": 2026, "month": None, "alloc": 260000.0, "notes": "Enterprise SaaS licenses"},
            {"dept": None, "cat": "Digital Marketing", "year": 2026, "month": None, "alloc": 320000.0, "notes": "Google Ads, LinkedIn, SEO"},
            {"dept": None, "cat": "Travel & Entertainment", "year": 2026, "month": None, "alloc": 120000.0, "notes": "Client on-site & QBR travels"},
            {"dept": None, "cat": "Facilities & Rent", "year": 2026, "month": None, "alloc": 200000.0, "notes": "Office leases & co-working"},
            {"dept": None, "cat": "Legal & Compliance", "year": 2026, "month": None, "alloc": 95000.0, "notes": "Audits, IP and counsel"},
        ]

        if db.query(Budget).filter(Budget.company_id == company.id).count() < 5:
            for b in budget_specs:
                dept_obj = depts_map.get(b["dept"]) if b["dept"] else None
                cat_obj = cats_map.get(b["cat"]) if b["cat"] else None
                bg = Budget(
                    company_id=company.id,
                    department_id=dept_obj.id if dept_obj else None,
                    category_id=cat_obj.id if cat_obj else None,
                    year=b["year"],
                    month=b["month"],
                    allocated_amount=b["alloc"],
                    spent_amount=0.0,
                    notes=b["notes"]
                )
                db.add(bg)
            db.commit()
            print(f"[OK] {len(budget_specs)} Budgets created")

        # 8. Create 500+ Realistic Transactions spanning 12 Months
        if db.query(Transaction).filter(Transaction.company_id == company.id).count() < 300:
            print("[INFO] Generating 500+ realistic multi-month financial transactions...")
            
            revenue_sources = [
                ("Enterprise SaaS Contract - Acme Tier 1 Client", 85000.0, "Sales & Revenue", "SaaS Software", "Stripe Payments"),
                ("Annual License Renewal - Global FinTech Partner", 145000.0, "Sales & Revenue", "SaaS Software", "Stripe Payments"),
                ("Multi-Year Platform License - Horizon Corp", 220000.0, "Sales & Revenue", "SaaS Software", "Stripe Payments"),
                ("Professional Services & Implementation Fee", 45000.0, "Sales & Revenue", "Miscellaneous", "Bank Transfer"),
                ("Enterprise Expansion Seats - Vertex Media", 68000.0, "Sales & Revenue", "SaaS Software", "Stripe Payments"),
                ("Custom AI Agent Integration Services", 95000.0, "Sales & Revenue", "SaaS Software", "Bank Transfer"),
                ("Strategic Partner Revenue Share", 32000.0, "Sales & Revenue", "Miscellaneous", "Bank Transfer"),
                ("Government Cloud Solution Milestone Payout", 180000.0, "Sales & Revenue", "SaaS Software", "Bank Transfer"),
                ("SaaS Subscription Monthly Billing Run", 125000.0, "Sales & Revenue", "SaaS Software", "Stripe Payments"),
            ]

            expense_templates = [
                ("AWS EC2 & RDS Multi-AZ Production Cluster", (16000, 24000), "Engineering & Product", "Cloud Infrastructure", "Amazon Web Services (AWS)"),
                ("Google Cloud AI Vertex & BigQuery Analytics", (9500, 15000), "Engineering & Product", "Cloud Infrastructure", "Google Cloud Platform"),
                ("Snowflake Data Warehousing Compute Nodes", (5500, 8500), "Engineering & Product", "Cloud Infrastructure", "Snowflake Inc."),
                ("Datadog Real-Time Telemetry & Log Management", (3400, 4800), "Engineering & Product", "Cloud Infrastructure", "Datadog Inc."),
                ("Salesforce CRM Enterprise Licenses", (9200, 9200), "Sales & Revenue", "SaaS Software", "Salesforce Inc."),
                ("HubSpot Inbound Marketing & Lead Automation", (4200, 5200), "Growth & Marketing", "Digital Marketing", "HubSpot"),
                ("Google Search & Performance Max Campaigns", (18000, 38000), "Growth & Marketing", "Digital Marketing", "Google Cloud Platform"),
                ("LinkedIn Sponsored InMail B2B Campaign", (8500, 16000), "Growth & Marketing", "Digital Marketing", "Microsoft Azure & 365"),
                ("WeWork Headquarters Studio Lease", (14000, 14000), "Finance & Operations", "Facilities & Rent", "WeWork Global"),
                ("Engineering Team MacBook Pro M3 Provisioning", (12000, 26000), "Engineering & Product", "Procurement & Hardware", "Stripe Payments"),
                ("Executive Team QBR Flight & Lodging", (4500, 9500), "Sales & Revenue", "Travel & Entertainment", "Delta Airlines Corporate"),
                ("Global Payroll & Health Benefits Run", (98000, 125000), "People & HR", "Payroll & Benefits", "Bank Transfer"),
                ("Legal IP Trademark & Privacy Compliance Counsel", (6500, 16000), "Legal & Compliance", "Legal & Compliance", "Bank Transfer"),
                ("Slack & Zoom Video Enterprise Communication", (4500, 5200), "People & HR", "SaaS Software", "Slack Technologies"),
                ("OpenAI Enterprise API Cluster Ingestion", (3200, 6800), "Engineering & Product", "SaaS Software", "OpenAI"),
                ("GitHub Actions CI/CD Build Runners", (1800, 2400), "Engineering & Product", "SaaS Software", "GitHub Inc."),
                ("Figma Design Organization Plan", (1600, 2000), "Engineering & Product", "SaaS Software", "Figma Inc."),
                ("MongoDB Atlas Production Tier M50 Cluster", (2600, 3400), "Engineering & Product", "Cloud Infrastructure", "MongoDB Atlas"),
                ("Cloudflare Magic Transit & DDoS Mitigation", (2200, 2600), "Engineering & Product", "Cloud Infrastructure", "Cloudflare Inc."),
                ("Workday HCM Monthly Cloud Fee", (7800, 7800), "People & HR", "Payroll & Benefits", "Workday Inc."),
            ]

            admin_user = users_map[UserRole.ADMIN]
            start_month = datetime(2025, 8, 1)
            tx_count = 0

            for m in range(13):  # 13 months
                current_m = start_month + timedelta(days=m * 30.5)
                year_val = current_m.year
                month_val = current_m.month
                
                # 6 Revenue transactions per month
                for _ in range(6):
                    desc, amt, dept_n, cat_n, vend_n = random.choice(revenue_sources)
                    day_val = random.randint(1, 28)
                    t_date = date(year_val, month_val, day_val)
                    
                    tx = Transaction(
                        company_id=company.id,
                        department_id=depts_map[dept_n].id,
                        category_id=cats_map.get(cat_n, list(cats_map.values())[0]).id,
                        vendor_id=vendors_map.get(vend_n, list(vendors_map.values())[0]).id,
                        transaction_date=t_date,
                        description=desc,
                        amount=round(amt * random.uniform(0.9, 1.15), 2),
                        transaction_type=TransactionType.REVENUE,
                        payment_method="Bank Transfer",
                        reference_number=f"REV-{year_val}-{month_val:02d}-{random.randint(1000, 9999)}",
                        created_by=admin_user.id
                    )
                    db.add(tx)
                    tx_count += 1

                # 35 Expense transactions per month -> ~455 expenses + 78 revenue = 533+ total!
                for _ in range(35):
                    desc, (min_a, max_a), dept_n, cat_n, vend_n = random.choice(expense_templates)
                    day_val = random.randint(1, 28)
                    t_date = date(year_val, month_val, day_val)
                    amt = round(random.uniform(min_a, max_a), 2)
                    
                    # Intentional anomaly injection on certain months
                    if m == 11 and "AWS" in desc:
                        amt = 48500.0  # Large AWS spike anomaly
                    elif m == 9 and "Google" in desc and random.random() < 0.2:
                        amt = 72000.0  # Search Ad surge anomaly

                    v_obj = vendors_map.get(vend_n)
                    tx = Transaction(
                        company_id=company.id,
                        department_id=depts_map[dept_n].id,
                        category_id=cats_map.get(cat_n, list(cats_map.values())[0]).id,
                        vendor_id=v_obj.id if v_obj else None,
                        transaction_date=t_date,
                        description=desc,
                        amount=amt,
                        transaction_type=TransactionType.EXPENSE,
                        payment_method="Corporate Card" if amt < 10000 else "Bank Transfer",
                        reference_number=f"EXP-{year_val}-{month_val:02d}-{random.randint(10000, 99999)}",
                        created_by=admin_user.id
                    )
                    db.add(tx)
                    tx_count += 1

            db.commit()
            print(f"[OK] {tx_count} Transactions seeded successfully across 13 months (500+ dataset requirement met)!")

        # 9. Recalculate Budgets spent amount from transactions
        all_budgets = db.query(Budget).filter(Budget.company_id == company.id).all()
        for bg in all_budgets:
            sync_budget_spent(db, bg)
        db.commit()
        print(f"[OK] Synchronized spent amounts for {len(all_budgets)} budgets")

        # 10. Pre-populate HITL Approval Requests
        if db.query(ApprovalRequest).filter(ApprovalRequest.company_id == company.id).count() < 4:
            approvals_data = [
                {
                    "type": "CANCEL_SUBSCRIPTION",
                    "title": "Revoke 18 Inactive Salesforce Enterprise Seats",
                    "details": "Deprovision 18 untouched seats across Sales & Revenue department yielding $2,700/mo savings.",
                    "savings": 2700.0,
                    "risk": "LOW",
                    "status": "PENDING"
                },
                {
                    "type": "RENEGOTIATE_VENDOR",
                    "title": "AWS Compute Savings Plan 1-Year Commitment",
                    "details": "Convert on-demand compute instances to 1-year committed use plan with 38% hourly reduction.",
                    "savings": 4850.0,
                    "risk": "LOW",
                    "status": "PENDING"
                },
                {
                    "type": "CANCEL_SUBSCRIPTION",
                    "title": "Downgrade 38 Inactive Zoom Pro Hosts",
                    "details": "Rebalance pooled video conference licenses to basic attendee accounts.",
                    "savings": 620.0,
                    "risk": "LOW",
                    "status": "APPROVED",
                    "notes": "Approved by Finance Controller."
                },
                {
                    "type": "BUDGET_OVERRIDE",
                    "title": "Moderate Growth & Marketing Paid Ad Spend by 12%",
                    "details": "Cap redundant Google Performance Max campaigns during off-peak conversion window.",
                    "savings": 3200.0,
                    "risk": "MEDIUM",
                    "status": "EXECUTED",
                    "notes": "Executed on live advertising campaign budget parameters."
                }
            ]
            for a in approvals_data:
                appr = ApprovalRequest(
                    company_id=company.id,
                    requester_id=users_map[UserRole.ADMIN].id,
                    request_type=a["type"],
                    title=a["title"],
                    details=a["details"],
                    impact_savings_monthly=a["savings"],
                    risk_level=a["risk"],
                    status=a["status"],
                    response_notes=a.get("notes")
                )
                db.add(appr)
            db.commit()
            print(f"[OK] {len(approvals_data)} Governance Approval requests initialized")

        print("\n========================================================")
        print("STAGE 3 ENTERPRISE SEED COMPLETED SUCCESSFULLY!")
        print("Demo Credentials (all share password: Password123!):")
        print(" - Admin:              admin@moneyanalysis.ai")
        print(" - Finance Manager:    finance@moneyanalysis.ai")
        print(" - Dept Manager (Eng): engineering.lead@moneyanalysis.ai")
        print(" - Employee:           employee@moneyanalysis.ai")
        print(" - Auditor:            auditor@moneyanalysis.ai")
        print("========================================================\n")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
