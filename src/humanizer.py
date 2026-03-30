"""
CarTuning Humanization Engine
Applies probabilistic variance to raw recoil compensation values
to simulate realistic human hand movement.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class HumanizationConfig:
    """Configuration for humanization parameters."""
    delay_variance_ms: float = 10.0
    pull_variance_px: float = 1.0
    x_variance_px: float = 0.5
    skip_probability: float = 0.03
    overcorrect_probability: float = 0.02
    overcorrect_magnitude: float = 1.2
    falloff_stages: List[dict] = field(default_factory=list)
    # Special variance for weapons like Custom SMG
    special_variance: Optional[dict] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'HumanizationConfig':
        """Create config from weapon JSON humanization dict."""
        return cls(
            delay_variance_ms=data.get('delay_variance_ms', 10.0),
            pull_variance_px=data.get('pull_variance_px', 1.0),
            x_variance_px=data.get('x_variance_px', 0.5),
            skip_probability=data.get('skip_probability', 0.03),
            overcorrect_probability=data.get('overcorrect_probability', 0.02),
            overcorrect_magnitude=data.get('overcorrect_magnitude', 1.2),
            falloff_stages=data.get('falloff_stages', []),
            special_variance=data.get('special_variance', None)
        )


@dataclass
class ShotData:
    """Represents a single shot's compensation data."""
    shot_number: int
    delay_ms: float
    pull_y: float
    drift_x: float
    is_skipped: bool = False
    is_overcorrected: bool = False
    falloff_multiplier: float = 1.0


class Humanizer:
    """
    Applies humanization to raw macro sequences.

    Takes perfect compensation values and adds:
    - Delay variance (Gaussian)
    - Pull variance (Uniform)
    - X-axis variance (Uniform)
    - Random skip events
    - Over-correction with recovery
    - Staged falloff (fatigue)
    """

    def __init__(self, config: HumanizationConfig, seed: Optional[int] = None):
        """
        Initialize humanizer with config.

        Args:
            config: HumanizationConfig with variance parameters
            seed: Optional random seed for reproducibility (testing)
        """
        self.config = config
        self.rng = random.Random(seed)

    def apply_delay_variance(self, base_delay: float) -> float:
        """
        Apply Gaussian delay variance to base timing.
        Clamps to [base - max_var, base + max_var].
        """
        variance = self.config.delay_variance_ms
        offset = self.rng.gauss(0, variance / 2)
        result = base_delay + offset
        # Clamp
        return max(base_delay - variance, min(base_delay + variance, result))

    def apply_pull_variance(self, base_pull: float) -> float:
        """Apply uniform random variance to Y-axis pull."""
        variance = self.config.pull_variance_px
        offset = self.rng.uniform(-variance, variance)
        return base_pull + offset

    def apply_x_variance(self, base_x: float) -> float:
        """Apply uniform random variance to X-axis drift."""
        variance = self.config.x_variance_px
        offset = self.rng.uniform(-variance, variance)
        return base_x + offset

    def should_skip(self) -> bool:
        """Roll for skip event — momentary lapse in compensation."""
        return self.rng.random() < self.config.skip_probability

    def should_overcorrect(self) -> bool:
        """Roll for over-correction event."""
        return self.rng.random() < self.config.overcorrect_probability

    def get_falloff_multiplier(self, shot_number: int) -> float:
        """
        Get the falloff multiplier for a given shot number.
        Simulates human fatigue over sustained fire.
        """
        for stage in self.config.falloff_stages:
            if shot_number <= stage['end_shot']:
                return stage['multiplier']
        # If beyond all stages, use last stage's multiplier
        if self.config.falloff_stages:
            return self.config.falloff_stages[-1]['multiplier']
        return 1.0

    def apply_special_variance(self, shot: ShotData) -> ShotData:
        """
        Apply weapon-specific special variance rules.
        E.g., Custom SMG's Y-spike probability.
        """
        if not self.config.special_variance:
            return shot

        sv = self.config.special_variance

        # Y-axis spike (Custom SMG style)
        if 'y_spike_probability' in sv and 'y_spike_magnitude' in sv:
            if self.rng.random() < sv['y_spike_probability']:
                shot.pull_y += sv['y_spike_magnitude']

        return shot

    def humanize_shot(self, shot_number: int, base_delay: float,
                      base_pull_y: float, base_drift_x: float,
                      next_shot_modifier: float = 1.0) -> Tuple[ShotData, float]:
        """
        Humanize a single shot's compensation values.

        Args:
            shot_number: Current shot (1-indexed)
            base_delay: Base delay in ms
            base_pull_y: Base Y-axis pull in px
            base_drift_x: Base X-axis drift in px
            next_shot_modifier: Modifier from previous shot's overcorrection

        Returns:
            Tuple of (humanized ShotData, next_shot_modifier for next shot)
        """
        falloff = self.get_falloff_multiplier(shot_number)
        new_next_modifier = 1.0

        # Check for skip
        if self.should_skip():
            return ShotData(
                shot_number=shot_number,
                delay_ms=self.apply_delay_variance(base_delay),
                pull_y=0.0,
                drift_x=0.0,
                is_skipped=True,
                falloff_multiplier=falloff
            ), 1.0

        # Apply base humanization
        delay = self.apply_delay_variance(base_delay)
        pull_y = self.apply_pull_variance(base_pull_y) * falloff * next_shot_modifier
        drift_x = self.apply_x_variance(base_drift_x) * falloff * next_shot_modifier

        # Check for overcorrection
        is_overcorrected = False
        if self.should_overcorrect():
            pull_y *= self.config.overcorrect_magnitude
            drift_x *= self.config.overcorrect_magnitude
            is_overcorrected = True
            # Next shot compensates back
            new_next_modifier = 2.0 - self.config.overcorrect_magnitude  # e.g., 0.8

        shot = ShotData(
            shot_number=shot_number,
            delay_ms=round(delay, 1),
            pull_y=round(pull_y, 2),
            drift_x=round(drift_x, 2),
            is_overcorrected=is_overcorrected,
            falloff_multiplier=falloff
        )

        # Apply special variance (weapon-specific)
        shot = self.apply_special_variance(shot)

        return shot, new_next_modifier

    def humanize_sequence(self, base_shots: List[dict]) -> List[ShotData]:
        """
        Humanize an entire sequence of shots.

        Args:
            base_shots: List of dicts with keys: shot_number, delay_ms, pull_y, drift_x

        Returns:
            List of humanized ShotData objects
        """
        result = []
        next_modifier = 1.0

        for shot_data in base_shots:
            humanized, next_modifier = self.humanize_shot(
                shot_number=shot_data['shot_number'],
                base_delay=shot_data['delay_ms'],
                base_pull_y=shot_data['pull_y'],
                base_drift_x=shot_data['drift_x'],
                next_shot_modifier=next_modifier
            )
            result.append(humanized)

        return result
