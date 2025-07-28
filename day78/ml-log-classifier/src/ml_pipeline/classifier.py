import numpy as np
import pandas as pd
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LogClassifier:
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.ensemble_model = None
        self.is_trained = False
        
        # Initialize individual models
        self.models['naive_bayes'] = MultinomialNB(**config["models"]["naive_bayes"])
        self.models['random_forest'] = RandomForestClassifier(**config["models"]["random_forest"], random_state=42)
        self.models['gradient_boosting'] = GradientBoostingClassifier(**config["models"]["gradient_boosting"], random_state=42)
        
    def train(self, X, y_severity, y_category):
        """Train ensemble classifier for both severity and category"""
        logger.info("Training ML models...")
        
        # Split data
        X_train, X_test, y_sev_train, y_sev_test, y_cat_train, y_cat_test = train_test_split(
            X, y_severity, y_category, test_size=0.2, random_state=42, stratify=y_severity
        )
        
        # Train severity classifier
        estimators_severity = [
            ('nb', self.models['naive_bayes']),
            ('rf', self.models['random_forest']),
            ('gb', self.models['gradient_boosting'])
        ]
        
        self.severity_classifier = VotingClassifier(
            estimators=estimators_severity,
            voting=self.config["ensemble"]["voting"],
            weights=self.config["ensemble"]["weights"]
        )
        
        self.severity_classifier.fit(X_train, y_sev_train)
        
        # Train category classifier
        estimators_category = [
            ('nb', MultinomialNB(**self.config["models"]["naive_bayes"])),
            ('rf', RandomForestClassifier(**self.config["models"]["random_forest"], random_state=42)),
            ('gb', GradientBoostingClassifier(**self.config["models"]["gradient_boosting"], random_state=42))
        ]
        
        self.category_classifier = VotingClassifier(
            estimators=estimators_category,
            voting=self.config["ensemble"]["voting"],
            weights=self.config["ensemble"]["weights"]
        )
        
        self.category_classifier.fit(X_train, y_cat_train)
        
        # Evaluate models
        sev_score = self.severity_classifier.score(X_test, y_sev_test)
        cat_score = self.category_classifier.score(X_test, y_cat_test)
        
        logger.info(f"Severity classification accuracy: {sev_score:.3f}")
        logger.info(f"Category classification accuracy: {cat_score:.3f}")
        
        # Detailed evaluation
        sev_pred = self.severity_classifier.predict(X_test)
        cat_pred = self.category_classifier.predict(X_test)
        
        logger.info("Severity Classification Report:")
        logger.info(f"\n{classification_report(y_sev_test, sev_pred)}")
        
        logger.info("Category Classification Report:")
        logger.info(f"\n{classification_report(y_cat_test, cat_pred)}")
        
        self.is_trained = True
        
        return {
            'severity_accuracy': sev_score,
            'category_accuracy': cat_score,
            'severity_report': classification_report(y_sev_test, sev_pred, output_dict=True),
            'category_report': classification_report(y_cat_test, cat_pred, output_dict=True)
        }
        
    def predict(self, X):
        """Predict severity and category for new logs"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")
            
        severity_pred = self.severity_classifier.predict(X)
        category_pred = self.category_classifier.predict(X)
        
        # Get prediction probabilities for confidence scores
        severity_proba = self.severity_classifier.predict_proba(X)
        category_proba = self.category_classifier.predict_proba(X)
        
        return {
            'severity': severity_pred,
            'category': category_pred,
            'severity_confidence': severity_proba.max(axis=1),
            'category_confidence': category_proba.max(axis=1)
        }
        
    def save_models(self, models_dir):
        """Save trained models to disk"""
        models_dir = Path(models_dir)
        models_dir.mkdir(exist_ok=True)
        
        if self.is_trained:
            joblib.dump(self.severity_classifier, models_dir / 'severity_classifier.pkl')
            joblib.dump(self.category_classifier, models_dir / 'category_classifier.pkl')
            logger.info(f"Models saved to {models_dir}")
        else:
            logger.warning("No trained models to save")
            
    def load_models(self, models_dir):
        """Load trained models from disk"""
        models_dir = Path(models_dir)
        
        try:
            self.severity_classifier = joblib.load(models_dir / 'severity_classifier.pkl')
            self.category_classifier = joblib.load(models_dir / 'category_classifier.pkl')
            self.is_trained = True
            logger.info(f"Models loaded from {models_dir}")
        except FileNotFoundError:
            logger.warning(f"No saved models found in {models_dir}") 