# Calibration and Thresholds

LinearSVC was compared uncalibrated and with training-fold-only sigmoid/isotonic calibration. Sigmoid validation log loss was 0.2920, Brier 0.0887 and ECE 0.0516. Thresholds were evaluated only on validation: maximum-F1 threshold 0.325 yielded precision 0.6713, recall 0.9643 and F1 0.7915; a recall-focused point at 0.575 yielded precision 0.7764, recall 0.7579 and F1 0.7671. These are operating-point examples, not production policy.
