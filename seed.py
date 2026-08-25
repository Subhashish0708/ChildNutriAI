"""
Database Seeding Script for ChildNutri AI.
Inserts development and demonstration records into database/childnutri.db
including users (Parent, Health Worker), children, assessments, AI predictions,
medical history, nutrition plans, appointments, and notifications.
"""

import os
import sys
from datetime import date, datetime, timedelta

# Ensure backend package can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, engine, Base
from backend.models import (
    User, Child, Assessment, Prediction, ChildPhoto,
    MedicalHistory, NutritionPlan, Appointment, Notification
)
from backend.services.auth_service import hash_password

def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "priya.sharma@email.com").first():
            print("Database already contains seed data. Skipping to prevent duplicate records.")
            return

        print("Seeding Users...")
        # 1. Health Worker
        hw = User(
            full_name="Dr. Subha",
            email="dr.subha@childnutri.org",
            phone="+91 98765 11223",
            password_hash=hash_password("Doctor@123"),
            role="health_worker"
        )
        db.add(hw)

        # 2. Pediatrician
        hw2 = User(
            full_name="Dr. Meena Rao",
            email="dr.meena@childnutri.org",
            phone="+91 98765 99887",
            password_hash=hash_password("Doctor@123"),
            role="health_worker"
        )
        db.add(hw2)

        # 3. Parent User
        parent = User(
            full_name="Priya Sharma",
            email="priya.sharma@email.com",
            phone="+91 98765 43210",
            password_hash=hash_password("Parent@123"),
            role="parent"
        )
        db.add(parent)
        db.commit()
        db.refresh(hw)
        db.refresh(hw2)
        db.refresh(parent)

        print("Seeding Children...")
        # Main featured child for parent dashboard
        aarav = Child(
            health_id="CHN-2024-00814",
            parent_id=parent.id,
            name="Aarav Sharma",
            date_of_birth=date(2024, 6, 10),
            gender="Male",
            birth_weight=2.8,
            birth_length=48.0
        )
        db.add(aarav)

        # Other children for health worker dashboard
        c2 = Child(health_id="CHN-2024-00815", parent_id=None, name="Priya Patel", date_of_birth=date(2024, 12, 5), gender="Female", birth_weight=3.1, birth_length=50.0)
        c3 = Child(health_id="CHN-2024-00816", parent_id=None, name="Rahul Verma", date_of_birth=date(2023, 10, 15), gender="Male", birth_weight=2.5, birth_length=47.0)
        c4 = Child(health_id="CHN-2024-00817", parent_id=None, name="Meena Devi", date_of_birth=date(2024, 9, 20), gender="Female", birth_weight=2.7, birth_length=48.5)
        c5 = Child(health_id="CHN-2024-00818", parent_id=None, name="Kabir Singh", date_of_birth=date(2025, 2, 10), gender="Male", birth_weight=3.3, birth_length=51.0)
        
        db.add_all([c2, c3, c4, c5])
        db.commit()
        db.refresh(aarav)

        print("Seeding Assessments & AI Predictions...")
        # Aarav's 5 chronological assessments for Growth Tracker
        aarav_growth = [
            (date(2025, 4, 10), 10.0, 6.2, 63.0, 13.0, 43.0, "Initial assessment at Anganwadi", "Normal", 15.0, 0.94),
            (date(2025, 5, 12), 11.0, 6.5, 64.0, 12.6, 43.5, "Weight tracking slightly slow", "Underweight", 45.0, 0.88),
            (date(2025, 6, 15), 12.0, 6.7, 65.5, 12.2, 44.1, "Signs of wasting observed", "Wasted", 60.0, 0.89),
            (date(2025, 7, 18), 13.0, 7.0, 67.0, 12.0, 44.8, "Height lagging WHO median", "Stunted", 75.0, 0.90),
            (date(2025, 8, 21), 14.0, 7.2, 68.0, 11.5, 45.2, "Stunting confirmed, MUAC critical at 11.5cm", "Stunted", 82.0, 0.92)
        ]

        for adate, age, wt, ht, mu, hc, notes, pred_label, risk, conf in aarav_growth:
            a = Assessment(
                child_id=aarav.id,
                health_worker_id=hw2.id,
                assessment_date=adate,
                age_months=age,
                weight=wt,
                height=ht,
                muac=mu,
                head_circumference=hc,
                notes=notes
            )
            db.add(a)
            db.commit()
            db.refresh(a)

            p = Prediction(
                assessment_id=a.id,
                model_name="ChildNutri Anthropometric Model v1",
                prediction=pred_label,
                risk_score=risk,
                confidence=conf
            )
            db.add(p)

        # Other children assessments
        other_assessments = [
            (c2.id, date(2025, 8, 21), 8.0, 8.1, 70.0, 13.8, 43.5, "Healthy growth", "Normal", 12.0),
            (c3.id, date(2025, 8, 20), 22.0, 8.5, 78.0, 11.0, 46.0, "Severe acute malnutrition detected", "Severe (SAM)", 92.0),
            (c4.id, date(2025, 8, 19), 11.0, 6.4, 69.0, 12.1, 43.8, "Moderate wasting", "Wasted", 68.0),
            (c5.id, date(2025, 8, 18), 6.0, 5.8, 63.0, 12.2, 41.0, "Borderline underweight", "Underweight", 54.0),
        ]
        for cid, adate, age, wt, ht, mu, hc, notes, pred_label, risk in other_assessments:
            a = Assessment(child_id=cid, health_worker_id=hw.id, assessment_date=adate, age_months=age, weight=wt, height=ht, muac=mu, head_circumference=hc, notes=notes)
            db.add(a)
            db.commit()
            db.refresh(a)
            p = Prediction(assessment_id=a.id, model_name="ChildNutri Anthropometric Model v1", prediction=pred_label, risk_score=risk, confidence=0.91)
            db.add(p)

        print("Seeding Medical History...")
        meds = [
            MedicalHistory(child_id=aarav.id, doctor_name="Dr. Meena Rao", visit_date=date(2025, 8, 21), diagnosis="Stunting & Low MUAC", treatment="RUTF Therapy started", notes="MUAC critically low at 11.5 cm. Referral ready."),
            MedicalHistory(child_id=aarav.id, doctor_name="Dr. Meena Rao", visit_date=date(2025, 7, 14), diagnosis="Underweight", treatment="Iron and Vitamin D supplements", notes="Height tracking below WHO median."),
            MedicalHistory(child_id=aarav.id, doctor_name="Dr. Anil Kumar", visit_date=date(2025, 6, 12), diagnosis="Moderate Wasting", treatment="Diet counseling for mother", notes="Protein-rich foods recommended."),
            MedicalHistory(child_id=aarav.id, doctor_name="Dr. Meena Rao", visit_date=date(2025, 4, 10), diagnosis="Initial Registration", treatment="Vaccinations up to date", notes="Parameters within normal range at registration.")
        ]
        db.add_all(meds)

        print("Seeding Nutrition Plans...")
        nutr = NutritionPlan(
            child_id=aarav.id,
            created_by=hw2.id,
            plan_title="RUTF Therapeutic Feeding Plan",
            description="5 daily feeding sessions + 1 sachet RUTF + Iron and Vitamin D supplements.",
            start_date=date(2025, 8, 21),
            end_date=date(2025, 9, 21)
        )
        db.add(nutr)

        print("Seeding Appointments...")
        appts = [
            Appointment(child_id=aarav.id, health_worker_id=hw2.id, appointment_date=date(2025, 8, 28), appointment_time="10:00 AM", purpose="Monthly Follow-Up Assessment", status="upcoming", notes="Bring previous weight records."),
            Appointment(child_id=aarav.id, health_worker_id=hw2.id, appointment_date=date(2025, 9, 5), appointment_time="11:30 AM", purpose="RUTF Progress Review", status="upcoming", notes="Therapeutic food review & MUAC recheck."),
            Appointment(child_id=aarav.id, health_worker_id=hw2.id, appointment_date=date(2025, 8, 21), appointment_time="09:30 AM", purpose="Monthly Assessment", status="completed", notes="Stunting confirmed. RUTF initiated."),
            Appointment(child_id=aarav.id, health_worker_id=hw2.id, appointment_date=date(2025, 7, 14), appointment_time="10:00 AM", purpose="Monthly Assessment", status="completed", notes="Supplements prescribed.")
        ]
        db.add_all(appts)

        print("Seeding Notifications...")
        notifs = [
            Notification(user_id=parent.id, title="Urgent AI Alert", message="Aarav's MUAC dropped below safe range (11.5 cm). Visit health center.", type="alert", is_read=False),
            Notification(user_id=parent.id, title="Follow-up Reminder", message="Follow-up appointment scheduled with Dr. Meena Rao on 28 Aug 2025 at 10:00 AM.", type="appointment", is_read=False),
            Notification(user_id=parent.id, title="New Diet Plan", message="New therapeutic diet plan added by Dr. Meena Rao.", type="info", is_read=True),
            Notification(user_id=hw.id, title="High Risk Flag: Rahul Verma", message="Rahul Verma flagged as SAM — immediate attention required.", type="alert", is_read=False),
            Notification(user_id=hw.id, title="Follow-Up Due", message="Follow-up due for Aarav Sharma.", type="info", is_read=False)
        ]
        db.add_all(notifs)

        db.commit()
        print("Database seeding completed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
