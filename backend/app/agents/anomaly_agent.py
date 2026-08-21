import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionType
from app.models.vendor import Vendor
from app.models.department import Department
from app.models.category import Category
from app.models.future_ai import Anomaly

logger = logging.getLogger(__name__)


class AnomalyDetectionAgent:
    """
    Specialized agent employing Scikit-learn Isolation Forest and heuristic deviation
    scoring to detect suspicious, fraudulent, or high-variance enterprise financial transactions.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def scan_transactions(self, contamination: float = 0.08) -> List[Dict[str, Any]]:
        """
        Train Isolation Forest model on historical company expenses and flag statistical outliers.
        """
        txs = self.db.query(Transaction).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type == TransactionType.EXPENSE
        ).all()

        if len(txs) < 5:
            return []

        # Prepare feature matrix
        data = []
        for t in txs:
            t_date = pd.to_datetime(t.transaction_date)
            data.append({
                "id": t.id,
                "amount": float(t.amount),
                "vendor_id": t.vendor_id or 0,
                "department_id": t.department_id or 0,
                "category_id": t.category_id or 0,
                "day_of_week": t_date.dayofweek,
                "day_of_month": t_date.day,
                "is_weekend": 1 if t_date.dayofweek >= 5 else 0,
                "description": t.description,
                "date_str": str(t.transaction_date),
            })
        df = pd.DataFrame(data)

        # Compute vendor and category average deviations
        vendor_means = df.groupby("vendor_id")["amount"].transform("mean")
        vendor_stds = df.groupby("vendor_id")["amount"].transform("std").fillna(1.0)
        df["vendor_deviation_ratio"] = (df["amount"] - vendor_means) / (vendor_stds + 1e-5)

        category_means = df.groupby("category_id")["amount"].transform("mean")
        category_stds = df.groupby("category_id")["amount"].transform("std").fillna(1.0)
        df["category_deviation_ratio"] = (df["amount"] - category_means) / (category_stds + 1e-5)

        # Feature matrix for IsolationForest
        feature_cols = [
            "amount",
            "vendor_id",
            "department_id",
            "category_id",
            "day_of_week",
            "day_of_month",
            "is_weekend",
            "vendor_deviation_ratio",
            "category_deviation_ratio",
        ]
        X = df[feature_cols].fillna(0).values

        # Fit Isolation Forest
        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        model.fit(X)

        # -1 = anomaly, 1 = normal
        predictions = model.predict(X)
        raw_scores = model.decision_function(X)  # lower = more abnormal

        # Normalize scores to 0-100 anomaly severity scale
        min_s, max_s = raw_scores.min(), raw_scores.max()
        if max_s > min_s:
            norm_scores = 100 * (1.0 - (raw_scores - min_s) / (max_s - min_s))
        else:
            norm_scores = np.zeros_like(raw_scores)

        df["is_anomaly"] = predictions == -1
        df["anomaly_score"] = norm_scores

        # Metadata lookups
        vend_map = {v.id: v.name for v in self.db.query(Vendor).filter(Vendor.company_id == self.company_id).all()}
        dept_map = {d.id: d.name for d in self.db.query(Department).filter(Department.company_id == self.company_id).all()}
        cat_map = {c.id: c.name for c in self.db.query(Category).filter(Category.company_id == self.company_id).all()}

        anomalies_detected = []

        # Find anomalies (or highest 5 scores if strictly thresholded)
        anomaly_rows = df[df["anomaly_score"] >= 65].sort_values(by="anomaly_score", ascending=False)
        if anomaly_rows.empty:
            anomaly_rows = df.sort_values(by="anomaly_score", ascending=False).head(3)

        for _, row in anomaly_rows.iterrows():
            tx_id = int(row["id"])
            score = round(float(row["anomaly_score"]), 1)
            amt = float(row["amount"])
            v_name = vend_map.get(int(row["vendor_id"]), "Unknown Vendor")
            d_name = dept_map.get(int(row["department_id"]), "General Operations")
            c_name = cat_map.get(int(row["category_id"]), "General OPEX")

            # Determine severity
            if score >= 88 or amt > 25000:
                severity = "CRITICAL"
            elif score >= 75:
                severity = "HIGH"
            elif score >= 60:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            # Formulate explainable reasons
            reasons = []
            if float(row["vendor_deviation_ratio"]) > 2.0:
                reasons.append(f"Amount (${amt:,.2f}) is significantly higher than historical vendor average for {v_name}.")
            if float(row["category_deviation_ratio"]) > 2.5:
                reasons.append(f"Transaction exceeds typical spending range for {c_name}.")
            if row["is_weekend"] == 1:
                reasons.append("Payment occurred on a weekend/off-cycle schedule.")
            if amt > 10000 and "Subscription" in c_name:
                reasons.append("Unusually high SaaS charge detected.")
            if not reasons:
                reasons.append(f"Multi-feature vector variance indicates statistical outlier pattern (Score: {score}/100).")

            explanation = " | ".join(reasons)

            # Persist or update anomaly in database
            existing = self.db.query(Anomaly).filter(
                Anomaly.company_id == self.company_id,
                Anomaly.transaction_id == tx_id
            ).first()

            if not existing:
                new_anom = Anomaly(
                    company_id=self.company_id,
                    transaction_id=tx_id,
                    anomaly_score=score,
                    severity=severity,
                    explanation=explanation,
                    reasons=reasons,
                    features_snapshot={
                        "amount": amt,
                        "vendor": v_name,
                        "department": d_name,
                        "category": c_name,
                        "deviation_ratio": round(float(row["vendor_deviation_ratio"]), 2),
                    },
                    status="DETECTED",
                    detected_at=datetime.now(timezone.utc)
                )
                self.db.add(new_anom)
                self.db.commit()
                self.db.refresh(new_anom)
                anom_id = new_anom.id
            else:
                existing.anomaly_score = score
                existing.severity = severity
                existing.explanation = explanation
                existing.reasons = reasons
                self.db.commit()
                anom_id = existing.id

            anomalies_detected.append({
                "id": anom_id,
                "transaction_id": tx_id,
                "transaction_date": row["date_str"],
                "transaction_description": row["description"],
                "transaction_amount": amt,
                "vendor_name": v_name,
                "department_name": d_name,
                "anomaly_score": score,
                "severity": severity,
                "explanation": explanation,
                "reasons": reasons,
                "status": "DETECTED",
                "detected_at": datetime.now(timezone.utc).isoformat(),
            })

        return anomalies_detected
