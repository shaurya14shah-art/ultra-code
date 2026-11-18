import json
import os
import math

STATE_FILE = os.path.expanduser("~/.ultra_quant_engine_state.json")

class Neurons:
    @staticmethod
    def simple_moving_average(data):
        if not data: return 0.0
        return sum(data) / len(data)
        
    @staticmethod
    def weighted_moving_average(data):
        if not data: return 0.0
        n = len(data)
        weights = [i + 1 for i in range(n)]
        total_weight = sum(weights)
        return sum(data[i] * (weights[i] / total_weight) for i in range(n))
        
    @staticmethod
    def exponential_moving_average(data):
        if not data: return 0.0
        alpha = 2 / (len(data) + 1)
        ema = data[0]
        for value in data[1:]:
            ema = (value - ema) * alpha + ema
        return ema
        
    @staticmethod
    def linear_trend(data):
        n = len(data)
        if n < 2:
            return data[-1] if data else 0.0
        
        x_mean = (n - 1) / 2
        y_mean = sum(data) / n
        
        numerator = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return data[-1]
            
        m = numerator / denominator
        b = y_mean - m * x_mean
        
        return m * n + b
        
    @staticmethod
    def momentum(data):
        if len(data) < 2:
            return data[-1] if data else 0.0
        roc = data[-1] - data[-2]
        return data[-1] + roc

def get_neurons():
    return {
        "sma": Neurons.simple_moving_average,
        "wma": Neurons.weighted_moving_average,
        "ema": Neurons.exponential_moving_average,
        "trend": Neurons.linear_trend,
        "momentum": Neurons.momentum
    }

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    else:
        neurons = get_neurons()
        initial_weight = 1.0 / len(neurons)
        return {
            "weights": {name: initial_weight for name in neurons.keys()},
            "last_predictions": {}
        }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def internal_predict(data_sequence):
    state = load_state()
    neurons = get_neurons()
    
    predictions = {}
    weighted_sum = 0.0
    total_weight = sum(state["weights"].values())
    
    for name, func in neurons.items():
        pred = func(data_sequence)
        predictions[name] = pred
        weight = state["weights"].get(name, 1.0 / len(neurons))
        weighted_sum += pred * (weight / total_weight)
        
    state["last_predictions"] = predictions
    save_state(state)
    
    return weighted_sum, predictions, state["weights"]

def internal_update(actual_value, learning_rate=0.2, alpha=1.0):
    state = load_state()
    last_preds = state.get("last_predictions", {})
    
    if not last_preds:
        return state["weights"], "No previous predictions to update against."
        
    weights = state["weights"]
    
    for name, pred in last_preds.items():
        error = abs(pred - actual_value)
        scaled_error = error / (abs(actual_value) + 1e-6)
        penalty = math.exp(-alpha * (scaled_error ** 2))
        
        current_weight = weights.get(name, 1.0 / len(last_preds))
        new_weight = (1 - learning_rate) * current_weight + learning_rate * current_weight * penalty
        weights[name] = new_weight
        
    total_new_weight = sum(weights.values())
    if total_new_weight > 0:
        for name in weights:
            weights[name] /= total_new_weight
            
    state["weights"] = weights
    save_state(state)
    
    return weights, "Weights successfully updated."

# ---------------------------------------------------------
# EXPOSED AGENT TOOLS
# ---------------------------------------------------------

def quant_predict(sequence: str) -> str:
    """Make a quantitative ensemble prediction for the next value in a sequence.
    
    Args:
        sequence: A comma-separated list of historical numbers (e.g., '10.5, 11.2, 12.0').
    """
    try:
        data = [float(x.strip()) for x in sequence.split(",") if x.strip()]
    except ValueError:
        return "ERROR: Input must be a comma-separated list of numbers."
        
    if not data:
        return "ERROR: Empty sequence provided."
        
    weighted_prediction, predictions, weights = internal_predict(data)
    
    result = [f"Sequence: {data}", "\n--- NEURON PREDICTIONS ---"]
    for name, pred in predictions.items():
        weight = weights.get(name, 0.0)
        result.append(f"[{name}] (weight: {weight:.4f}) => {pred:.4f}")
        
    result.append(f"\n=> FINAL ENSEMBLE PREDICTION: {weighted_prediction:.4f}")
    return "\n".join(result)

def quant_update(actual_value: str) -> str:
    """Update the quantitative prediction engine with the actual observed value to learn from errors.
    
    Args:
        actual_value: The true number that occurred after the last prediction (e.g., '12.5').
    """
    try:
        actual = float(actual_value.strip())
    except ValueError:
        return "ERROR: Actual value must be a number."
        
    new_weights, msg = internal_update(actual)
    
    if "No previous predictions" in msg:
        return msg
        
    result = [f"Actual Value Observed: {actual}", "\n--- NEW NEURON WEIGHTS ---"]
    for name, weight in new_weights.items():
        result.append(f"[{name}]: {weight:.4f}")
        
    return "\n".join(result)
