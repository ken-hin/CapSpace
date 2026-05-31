"""Prediction-model interface.

Defines :class:`BasePredictionModel`, the abstract contract every concrete
prediction model must implement (train/predict/evaluate/save/load). Training and
prediction code depends only on this interface so model implementations can be
swapped without changing the surrounding pipeline.
"""

from abc import ABC, abstractmethod
import pandas as pd

class BasePredictionModel(ABC):
    """Abstract base class for all prediction models.

    Establishes a uniform lifecycle (fit, score, evaluate, persist, restore) so
    the training and serving pipelines can treat any model interchangeably.
    """

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Fit the model on a feature matrix and target.

        Args:
            X: Feature matrix (one row per example).
            y: Target values aligned with ``X``.
        """
        ...
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Produce predictions for a feature matrix.

        Args:
            X: Feature matrix to score.

        Returns:
            pd.Series: Predicted values aligned with ``X``.
        """
        ...
    @abstractmethod
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Evaluate the model against known targets.

        Args:
            X: Feature matrix to score.
            y: Ground-truth target values aligned with ``X``.

        Returns:
            dict: Mapping of metric name to value (e.g. log loss, AUC, RMSE).
        """
        ...
    @abstractmethod
    def save(self, path: str) -> None:
        """Persist the trained model to disk.

        Args:
            path: Destination file path for the serialized model.
        """
        ...
    @abstractmethod
    def load(self, path: str) -> None:
        """Restore a previously saved model from disk.

        Args:
            path: Source file path of the serialized model.
        """
        ...
