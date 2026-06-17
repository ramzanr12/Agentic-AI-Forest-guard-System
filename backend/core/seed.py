"""Seed database with initial demo data."""
import asyncio
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from core.database import AsyncSessionLocal
from core.security import hash_password, verify_password
from models.models import User, Ranger, Visitor, Volunteer, Alert, AnimalSighting, UserRole

# Default passwords for seed users
_SEED_PASSWORDS = {
    "admin":        "admin123",
    "ranger_arjun": "ranger123",
    "ranger_priya": "ranger123",
    "ranger_deepak":"ranger123",
    "ranger_meena": "ranger123",
    "ranger_rajan": "ranger123",
    "visitor_01":   "visitor123",
    "visitor_02":   "visitor123",
    "volunteer_01": "vol123",
    "volunteer_02": "vol123",
}


async def seed_database():
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(User).limit(1))
        existing = result.scalars().first()

        if existing:
            # Already seeded — but re-hash passwords in case previous bcrypt run was broken
            all_users = (await session.execute(select(User))).scalars().all()
            fixed = False
            for u in all_users:
                pwd = _SEED_PASSWORDS.get(u.username)
                if not pwd:
                    continue
                try:
                    # If verify raises or returns False, the hash is broken — re-hash
                    ok = verify_password(pwd, u.hashed_password)
                except Exception:
                    ok = False
                if not ok:
                    u.hashed_password = hash_password(pwd)
                    fixed = True
            if fixed:
                await session.commit()
                print("Seed passwords re-hashed successfully.")
            else:
                print("Seeding skipped (already seeded, passwords OK).")
            return

        # ── Default Users ──
        users_data = [
            ("admin",        "admin@forest.gov",    "Admin Forest",  "admin123",   UserRole.ADMIN),
            ("ranger_arjun", "arjun@forest.gov",    "Arjun Kumar",   "ranger123",  UserRole.RANGER),
            ("ranger_priya", "priya@forest.gov",    "Priya Singh",   "ranger123",  UserRole.RANGER),
            ("ranger_deepak","deepak@forest.gov",   "Deepak Rao",    "ranger123",  UserRole.RANGER),
            ("ranger_meena", "meena@forest.gov",    "Meena Devi",    "ranger123",  UserRole.RANGER),
            ("ranger_rajan", "rajan@forest.gov",    "Rajan Pillai",  "ranger123",  UserRole.RANGER),
            ("visitor_01",   "visitor01@email.com", "Rahul Sharma",  "visitor123", UserRole.VISITOR),
            ("visitor_02",   "visitor02@email.com", "Anita Nair",    "visitor123", UserRole.VISITOR),
            ("volunteer_01", "vol01@email.com",     "Karthik Raj",   "vol123",     UserRole.VOLUNTEER),
            ("volunteer_02", "vol02@email.com",     "Sunita Patel",  "vol123",     UserRole.VOLUNTEER),
        ]
        users = []
        for uname, email, fname, pwd, role in users_data:
            u = User(
                username=uname, email=email, full_name=fname,
                hashed_password=hash_password(pwd), role=role
            )
            session.add(u)
            users.append(u)
        await session.flush()

        # ── Rangers ──
        ranger_data = [
            (users[1], "R001", "Zone-A",    11.4750, 76.9100),
            (users[2], "R002", "Zone-B",    11.5200, 76.9400),
            (users[3], "R003", "Zone-C",    11.5300, 76.9700),
            (users[4], "R004", "Zone-D",    11.4600, 76.9600),
            (users[5], "R005", "Core-Zone", 11.4916, 76.9294),
        ]
        for u, badge, sector, lat, lon in ranger_data:
            r = Ranger(
                user_id=u.id, badge_number=badge, sector=sector,
                current_lat=lat, current_lon=lon,
                is_on_duty=True, status="patrolling",
                phone=f"+91-{random.randint(9000000000, 9999999999)}"
            )
            session.add(r)

        # ── Visitors ──
        for i, u in enumerate(users[6:8], 1):
            v = Visitor(
                user_id=u.id,
                permit_type=random.choice(["day_pass", "research", "eco_tour"]),
                vehicle_number=f"KA{random.randint(10,99)}M{random.randint(1000,9999)}",
                group_size=random.randint(1, 4),
                is_inside=i == 1
            )
            session.add(v)

        # ── Volunteers ──
        for u in users[8:10]:
            vol = Volunteer(
                user_id=u.id,
                skills=random.sample(["photography", "botany", "first_aid", "tracking"], 2),
                points=random.randint(50, 300),
                is_verified=True,
                zone_assigned=random.choice(["Zone-A", "Zone-B"])
            )
            session.add(vol)

        # ── Sample Alerts ──
        alert_types = [
            ("fire_risk",      "high",     11.480, 76.920, "Zone-A", "Elevated fire risk detected in Zone-A"),
            ("poaching",       "critical", 11.510, 76.960, "Zone-B", "Suspected poacher movement detected"),
            ("intrusion",      "medium",   11.465, 76.935, "Zone-D", "Unauthorized vehicle entry"),
            ("animal_movement","low",      11.500, 76.945, "Zone-C", "Elephant herd moving towards water source"),
        ]
        for atype, sev, lat, lon, zone, desc in alert_types:
            a = Alert(
                alert_type=atype, severity=sev, lat=lat, lon=lon,
                zone=zone, description=desc, status="active",
                confidence=round(random.uniform(0.70, 0.95), 2)
            )
            session.add(a)

        # ── Animal Sightings ──
        animals = ["elephant", "tiger", "deer", "leopard", "bear"]
        for _ in range(20):
            sp = random.choice(animals)
            s = AnimalSighting(
                animal_id=f"{sp[:3].upper()}-{random.randint(100,999)}",
                species=sp,
                lat=11.4916 + random.uniform(-0.08, 0.08),
                lon=76.9294 + random.uniform(-0.08, 0.08),
                confidence=round(random.uniform(0.75, 0.97), 2),
                zone=random.choice(["Zone-A", "Zone-B", "Zone-C", "Zone-D"]),
                seen_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48))
            )
            session.add(s)

        await session.commit()
        print("Database seeded successfully.")
