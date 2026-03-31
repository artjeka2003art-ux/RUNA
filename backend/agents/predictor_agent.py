"""Predictor Agent — deprecated.

Probability calculation is now done mathematically inside
backend/prediction/graph_math.py via PredictionEngine.

No LLM calls for prediction. Math only.

This file is kept as a marker. All prediction logic lives in:
- backend/prediction/graph_math.py — momentum, projection, probabilities
- backend/prediction/prediction_engine.py — orchestration
- backend/agents/scenario_agent.py — math + Claude narratives
"""
