"""Simple classifier placeholder using scikit-learn."""

from sklearn.base import BaseEstimator


class CardClassifier(BaseEstimator):
    """Dummy classifier for cards."""

    def fit(self, X, y):
        return self

    def predict(self, X):
        return ["unknown" for _ in X]
