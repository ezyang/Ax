# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import annotations

from typing import Any, Optional

from ax.benchmark.metrics.base import BenchmarkMetricBase, GroundTruthMetricMixin
from ax.benchmark.metrics.utils import _fetch_trial_data
from ax.core.base_trial import BaseTrial
from ax.core.metric import MetricFetchResult


class BenchmarkMetric(BenchmarkMetricBase):
    """A generic metric used for observed values produced by Ax Benchmarks.

    Compatible e.g. with results generated by `BotorchTestProblemRunner` and
    `SurrogateRunner`.

    Attributes:
        has_ground_truth: Whether or not there exists a ground truth for this
            metric, i.e. whether each observation has an associated ground
            truth value. This is trivially true for deterministic metrics, and
            is also true for metrics where synthetic observation noise is added
            to its (deterministic) values. This is not true for metrics that
            are inherently noisy.
    """

    has_ground_truth: bool = True

    def __init__(
        self,
        name: str,
        lower_is_better: bool,  # TODO: Do we need to define this here?
        observe_noise_sd: bool = True,
        outcome_index: Optional[int] = None,
    ) -> None:
        """
        Args:
            name: Name of the metric.
            lower_is_better: If `True`, lower metric values are considered better.
            observe_noise_sd: If `True`, the standard deviation of the observation
                noise is included in the `sem` column of the the returned data.
                If `False`, `sem` is set to `None` (meaning that the model will
                have to infer the noise level).
            outcome_index: The index of the output. This is applicable in settings
                where the underlying test problem is evaluated in a vectorized fashion
                across multiple outputs, without providing a name for each output.
                In such cases, `outcome_index` is used in `fetch_trial_data` to extract
                `Ys` and `Yvars`, and `name` is the name of the metric.
        """
        super().__init__(name=name, lower_is_better=lower_is_better)
        # Declare `lower_is_better` as bool (rather than optional as in the base class)
        self.lower_is_better: bool = lower_is_better
        self.observe_noise_sd = observe_noise_sd
        self.outcome_index = outcome_index

    def fetch_trial_data(self, trial: BaseTrial, **kwargs: Any) -> MetricFetchResult:
        if len(kwargs) > 0:
            raise NotImplementedError(
                f"Arguments {set(kwargs)} are not supported in "
                f"{self.__class__.__name__}.fetch_trial_data."
            )
        return _fetch_trial_data(
            trial=trial,
            metric_name=self.name,
            outcome_index=self.outcome_index,
            include_noise_sd=self.observe_noise_sd,
            ground_truth=False,
        )

    def make_ground_truth_metric(self) -> BenchmarkMetricBase:
        """Create a ground truth version of this metric."""
        return GroundTruthBenchmarkMetric(original_metric=self)


class GroundTruthBenchmarkMetric(BenchmarkMetric, GroundTruthMetricMixin):
    def __init__(self, original_metric: BenchmarkMetric) -> None:
        """
        Args:
            original_metric: The original BenchmarkMetric to which this metric
                corresponds.
        """
        super().__init__(
            name=self.get_ground_truth_name(original_metric),
            lower_is_better=original_metric.lower_is_better,
            observe_noise_sd=False,
            outcome_index=original_metric.outcome_index,
        )
        self.original_metric = original_metric

    def fetch_trial_data(self, trial: BaseTrial, **kwargs: Any) -> MetricFetchResult:
        if len(kwargs) > 0:
            raise NotImplementedError(
                f"Arguments {set(kwargs)} are not supported in "
                f"{self.__class__.__name__}.fetch_trial_data."
            )
        return _fetch_trial_data(
            trial=trial,
            metric_name=self.name,
            outcome_index=self.outcome_index,
            include_noise_sd=False,
            ground_truth=True,
        )

    def make_ground_truth_metric(self) -> BenchmarkMetricBase:
        """Create a ground truth version of this metric."""
        return self
