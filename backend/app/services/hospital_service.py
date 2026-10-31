import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import HospitalImport, HospitalEntry

DEMO_HOSPITALS = [
    {
        "hospital_name": "Apollo Hospitals Bannerghatta Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560076",
        "network_type": "Cashless Network (Pre-auth required)",
        "tier_category": "Tier 1 Super-specialty",
        "notes": "SYNTHETIC DEMO DATA – Check live TPA desk for current empanelment."
    },
    {
        "hospital_name": "Manipal Hospital Old Airport Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560017",
        "network_type": "Cashless Network",
        "tier_category": "Tier 1 Super-specialty",
        "notes": "SYNTHETIC DEMO DATA – Not verified live."
    },
    {
        "hospital_name": "Fortis Hospital Mulund",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400078",
        "network_type": "Cashless Network",
        "tier_category": "Tier 1 Tertiary",
        "notes": "SYNTHETIC DEMO DATA – Valid for inter-state cashless demonstration."
    },
    {
        "hospital_name": "Lilavati Hospital and Research Centre",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400050",
        "network_type": "Cashless Network (Zonal Co-pay may apply)",
        "tier_category": "Tier 1",
        "notes": "SYNTHETIC DEMO DATA – Requires pre-authorisation 48h prior."
    },
    {
        "hospital_name": "Ruby Hall Clinic Sassoon Road",
        "city": "Pune",
        "state": "Maharashtra",
        "pincode": "411001",
        "network_type": "Cashless Network",
        "tier_category": "Tier 2 Regional",
        "notes": "SYNTHETIC DEMO DATA – Not verified live."
    },
    {
        "hospital_name": "City Care Nursing Home (Non-Network)",
        "city": "Pune",
        "state": "Maharashtra",
        "pincode": "411038",
        "network_type": "Non-Network (Reimbursement Only)",
        "tier_category": "Community Clinic",
        "notes": "SYNTHETIC DEMO DATA – Registered 15-bed clinic; requires reimbursement route."
    }
]

class HospitalService:
    @staticmethod
    def ensure_demo_dataset(db: Session, user_id: str) -> None:
        """Seeds initial synthetic demo hospital dataset if not already present"""
        existing = db.query(HospitalImport).filter(HospitalImport.user_id == user_id).first()
        if not existing:
            imp = HospitalImport(
                user_id=user_id,
                source_filename="demo_tpa_network_synthetic.csv",
                provider_name="National TPA Network (Sample Feed)",
                verified_date="2026-10-15 (SYNTHETIC DEMO DATA)",
                entry_count=len(DEMO_HOSPITALS),
                is_synthetic=True
            )
            db.add(imp)
            db.commit()
            db.refresh(imp)

            for h in DEMO_HOSPITALS:
                entry = HospitalEntry(
                    import_id=imp.id,
                    hospital_name=h["hospital_name"],
                    city=h["city"],
                    state=h["state"],
                    pincode=h["pincode"],
                    network_type=h["network_type"],
                    tier_category=h["tier_category"],
                    notes=h["notes"]
                )
                db.add(entry)
            db.commit()

    @staticmethod
    def import_csv(
        db: Session,
        user_id: str,
        filename: str,
        file_content: str,
        provider_name: str = "Imported TPA Network List",
        verified_date: str = "Imported Date"
    ) -> Dict[str, Any]:
        """Imports local CSV of hospital network data"""
        reader = csv.DictReader(file_content.splitlines())
        entries_to_add = []

        imp = HospitalImport(
            user_id=user_id,
            source_filename=filename,
            provider_name=provider_name,
            verified_date=verified_date,
            is_synthetic=False
        )
        db.add(imp)
        db.commit()
        db.refresh(imp)

        count = 0
        for row in reader:
            h_name = row.get("hospital_name") or row.get("Hospital") or row.get("Name") or ""
            if not h_name.strip():
                continue
            entry = HospitalEntry(
                import_id=imp.id,
                hospital_name=h_name.strip(),
                city=(row.get("city") or row.get("City") or "").strip(),
                state=(row.get("state") or row.get("State") or "").strip(),
                pincode=(row.get("pincode") or row.get("Pin") or "").strip(),
                network_type=(row.get("network_type") or row.get("Type") or "Cashless").strip(),
                tier_category=(row.get("tier") or row.get("Tier") or "Standard").strip(),
                notes=(row.get("notes") or "").strip()
            )
            entries_to_add.append(entry)
            count += 1

        db.add_all(entries_to_add)
        imp.entry_count = count
        db.commit()

        return {
            "import_id": imp.id,
            "filename": filename,
            "entry_count": count,
            "provider_name": provider_name,
            "verified_date": verified_date
        }

    @staticmethod
    def search_hospitals(
        db: Session,
        user_id: str,
        city: Optional[str] = None,
        hospital_name: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """Searches local imported hospital records only. Never fabricates live network status."""
        HospitalService.ensure_demo_dataset(db, user_id)

        # Query all imports belonging to user
        query = db.query(HospitalEntry, HospitalImport).join(
            HospitalImport, HospitalEntry.import_id == HospitalImport.id
        ).filter(HospitalImport.user_id == user_id)

        if city and city.strip():
            query = query.filter(HospitalEntry.city.ilike(f"%{city.strip()}%"))
        if state and state.strip():
            query = query.filter(HospitalEntry.state.ilike(f"%{state.strip()}%"))
        if hospital_name and hospital_name.strip():
            query = query.filter(HospitalEntry.hospital_name.ilike(f"%{hospital_name.strip()}%"))

        records = query.limit(20).all()

        results = []
        source_provider = "No dataset loaded"
        last_verified = "Not verified live"
        is_synthetic = True

        for entry, imp in records:
            source_provider = imp.provider_name
            last_verified = imp.verified_date
            is_synthetic = imp.is_synthetic
            results.append({
                "id": entry.id,
                "hospital_name": entry.hospital_name,
                "city": entry.city,
                "state": entry.state,
                "pincode": entry.pincode,
                "network_type": entry.network_type,
                "tier_category": entry.tier_category,
                "notes": entry.notes,
                "provider_name": imp.provider_name,
                "verified_date": imp.verified_date,
                "is_synthetic": imp.is_synthetic
            })

        return {
            "query_city": city,
            "query_name": hospital_name,
            "total_found": len(results),
            "data_source_provider": source_provider,
            "last_verified_date": last_verified,
            "is_synthetic": is_synthetic,
            "results": results
        }

hospital_service = HospitalService()
