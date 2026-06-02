"""ModelRegistry ORM model.

Defines :class:`ModelRegistry`, the catalog of every trained model version, its
training window, hyperparameters, evaluation metrics, and MLflow run link. The
prediction service consults this table (via ``is_active``) to choose the model
serving each sport/target.
"""

from datetime import date, datetime
from sqlalchemy import String, Integer, DateTime, Date, Boolean, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ModelRegistry(Base):
    """Tracks every trained model version deployed to or considered for production.

    Pairs with MLflow: ``mlflow_run_id`` links to the artifact store for weights and
    full metric history. This table is the source of truth for the prediction service
    when selecting which model is active for a given sport/target.

    Only one row per (name, version) is allowed — bump version on any retraining.
    ``is_active`` should be True for at most one row per (sport, target) at any time.

    Attributes:
        id: Surrogate primary key.
        name: Human-readable model identifier, e.g. ``"mlb_run_total_v1"``.
        sport: Sport code the model serves (indexed).
        version: Semver or short hash, e.g. ``"1.0.0"`` or ``"abc1234"``.
        model_type: Algorithm family (``"xgboost"`` | ``"lightgbm"`` |
            ``"logistic"`` | ``"pytorch"``).
        target: Prediction target, e.g. ``"win_prob"``, ``"run_total"``,
            ``"k_total"``, ``"nrfi_prob"``, ``"player_hits_over"``.
        trained_at: When training completed (tz-aware).
        training_window_start: First date of training data.
        training_window_end: Last date of training data.
        mlflow_run_id: MLflow run id linking to weights/metrics/artifacts (nullable).
        hyperparams: JSON dict of hyperparameters used for this run.
        metrics: JSON dict of eval metrics (log_loss, brier_score, roc_auc, mae, rmse).
        is_active: True if this model currently serves predictions for its sport/target.
    """
    __tablename__ = "model_registry"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_registry_name_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Human-readable model identifier, e.g. 'mlb_run_total_v1'
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sport: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Semver or short hash, e.g. '1.0.0' or 'abc1234'
    version: Mapped[str] = mapped_column(String(50), nullable=False)

    # 'xgboost' | 'lightgbm' | 'logistic' | 'pytorch'
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 'win_prob' | 'run_total' | 'k_total' | 'nrfi_prob' | 'player_hits_over'
    target: Mapped[str] = mapped_column(String(100), nullable=False)

    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    training_window_start: Mapped[date] = mapped_column(Date, nullable=False)
    training_window_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Links to the MLflow run for weights, full metric logs, and artifacts
    mlflow_run_id: Mapped[str | None] = mapped_column(String(100))

    # JSON; full hyperparameter dict used for this training run
    hyperparams: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # JSON; evaluation metrics: log_loss, brier_score, roc_auc, mae, rmse, etc.
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # True = this model is currently serving predictions for its sport/target
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        """Return a concise debug representation (name, version, active flag)."""
        return f"<ModelRegistry {self.name} v{self.version} active={self.is_active}>"
