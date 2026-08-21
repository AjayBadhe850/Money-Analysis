import logging
import re
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from app.models.future_ai import CategorizationRule
from app.models.category import Category
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class ExpenseCategorizerService:
    """
    4-Tier Hybrid Categorization Engine:
    Level 1: Deterministic regex/keyword rules
    Level 2: Historical user-corrected database rules
    Level 3: Scikit-learn TF-IDF + Naive Bayes Classifier
    Level 4: LLM semantic fallback
    """

    DEFAULT_KEYWORD_RULES = {
        r"aws|amazon web services|ec2|s3|azure|gcp|google cloud|snowflake|cloud": "Cloud Infrastructure",
        r"salesforce|hubspot|crm|pipedrive": "Software Subscriptions",
        r"github|gitlab|docker|datadog|sentry|jira|confluence|jetbrains": "Engineering Tools",
        r"google ads|facebook ads|meta|linkedin ads|adwords|campaign|marketing": "Marketing & Advertising",
        r"uber|lyft|airline|flight|hotel|airbnb|delta|united|travel": "Travel & Entertainment",
        r"zoom|slack|notion|office 365|microsoft 365|workspace|asana": "Software Subscriptions",
        r"consulting|legal|audit|accounting|advisory|deloitte|pwc|ey|kpmg": "Professional Services",
        r"weWork|rent|office lease|facilities|utilities|electric": "Office & Facilities",
        r"bonus|salary|payroll|contractor|stipend": "Payroll & Benefits",
    }

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
        self._ml_model = None
        self._vectorizer = None

    def categorize(self, description: str, vendor: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify transaction text into appropriate expense category using the 4-tier pipeline.
        """
        text = f"{description} {vendor or ''}".strip().lower()

        # Tier 1: Deterministic Keyword Rules
        for pattern, cat_name in self.DEFAULT_KEYWORD_RULES.items():
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "predicted_category": cat_name,
                    "confidence_score": 0.98,
                    "prediction_method": "RULE",
                }

        # Tier 2: Historical User Corrections from Database
        user_rules = self.db.query(CategorizationRule).filter(
            CategorizationRule.company_id == self.company_id
        ).all()
        for rule in user_rules:
            if rule.keyword.lower() in text:
                return {
                    "predicted_category": rule.category_name,
                    "confidence_score": float(rule.confidence),
                    "prediction_method": "USER_CORRECTION",
                }

        # Tier 3: ML Model (TF-IDF + Naive Bayes)
        ml_prediction = self._predict_ml(text)
        if ml_prediction and ml_prediction["confidence"] >= 0.70:
            return {
                "predicted_category": ml_prediction["category"],
                "confidence_score": round(ml_prediction["confidence"], 2),
                "prediction_method": "ML",
            }

        # Tier 4: Fallback
        return {
            "predicted_category": "General OPEX",
            "confidence_score": 0.50,
            "prediction_method": "FALLBACK",
        }

    def record_user_correction(self, keyword: str, correct_category: str) -> CategorizationRule:
        """
        Learn from user feedback to continuously improve categorization accuracy.
        """
        rule = self.db.query(CategorizationRule).filter(
            CategorizationRule.company_id == self.company_id,
            CategorizationRule.keyword.ilike(keyword)
        ).first()

        if rule:
            rule.category_name = correct_category
            rule.confidence = 1.0
            rule.source = "USER_CORRECTION"
        else:
            rule = CategorizationRule(
                company_id=self.company_id,
                keyword=keyword.strip().lower(),
                category_name=correct_category,
                confidence=1.0,
                source="USER_CORRECTION"
            )
            self.db.add(rule)

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def _predict_ml(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Train lightweight in-memory classifier if historical data exists.
        """
        try:
            txs = self.db.query(Transaction).filter(
                Transaction.company_id == self.company_id,
                Transaction.category_id.isnot(None)
            ).all()

            if len(txs) < 15:
                return None

            cats = {c.id: c.name for c in self.db.query(Category).filter(Category.company_id == self.company_id).all()}
            corpus = []
            labels = []

            for t in txs:
                if t.category_id in cats:
                    corpus.append(t.description)
                    labels.append(cats[t.category_id])

            if len(set(labels)) < 2:
                return None

            vectorizer = TfidfVectorizer(max_features=200, stop_words="english")
            X = vectorizer.fit_transform(corpus)
            clf = MultinomialNB()
            clf.fit(X, labels)

            test_vec = vectorizer.transform([text])
            probs = clf.predict_proba(test_vec)[0]
            best_idx = probs.argmax()
            confidence = float(probs[best_idx])
            best_cat = clf.classes_[best_idx]

            return {"category": best_cat, "confidence": confidence}
        except Exception as e:
            logger.debug(f"ML categorization skipped: {e}")
            return None
