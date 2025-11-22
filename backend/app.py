import os
import io
import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify, render_template, send_file

# --- FIX: USE ABSOLUTE PATHS ---
# 1. Get the folder where this app.py file lives (e.g., /opt/render/.../backend)
base_dir = os.path.abspath(os.path.dirname(__file__))

# 2. Calculate the exact paths to frontend folders
template_dir = os.path.join(base_dir, '../frontend')
static_dir = os.path.join(base_dir, '../frontend/static')

# 3. Initialize Flask with these absolute paths
app = Flask(__name__,
            template_folder=template_dir,
            static_folder=static_dir)

# 4. Load model using absolute path
model_path = os.path.join(base_dir, 'model_linear.pkl')
model = joblib.load(model_path)

# Constants for Moore's Law
MOORES_BASE_YEAR = 1971
MOORES_BASE_COUNT = 2300


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json

        year = float(data['year'])
        node_size = float(data['node_size'])
        area = float(data['area'])
        trans_density = float(data['trans_density'])
        power_density = float(data['power_density'])

        log_node = np.log10(node_size) if node_size > 0 else 0
        log_area = np.log10(area) if area > 0 else 0
        log_density = np.log10(trans_density) if trans_density > 0 else 0

        input_data = pd.DataFrame([[year, log_node, log_area, log_density, power_density]],
                                  columns=['Year', 'Log_Node', 'Log_Area', 'Log_Density', 'Power Density (W/cm²)'])

        pred_log = model.predict(input_data)[0]
        pred_count = 10 ** pred_log

        lower_bound = int(pred_count * (1 - 0.20))
        upper_bound = int(pred_count * (1 + 0.20))

        years_passed = year - MOORES_BASE_YEAR
        moores_projection = MOORES_BASE_COUNT * (2 ** (years_passed / 2))

        deviation = ((pred_count - moores_projection) / moores_projection) * 100
        comparison_text = f"{abs(deviation):.1f}% {'Above' if deviation > 0 else 'Below'} Moore's Law"

        return jsonify({
            'status': 'success',
            'prediction_log': round(pred_log, 4),
            'prediction_count': int(pred_count),
            'formatted_count': f"{int(pred_count):,}",
            'lower_bound': f"{lower_bound:,}",
            'upper_bound': f"{upper_bound:,}",
            'moores_comp': comparison_text,
            'moores_val': int(moores_projection)
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)