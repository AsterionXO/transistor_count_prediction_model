import os
import io
import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify, render_template, send_file

app = Flask(__name__,
            template_folder='../frontend',
            static_folder='../frontend/static')

# Load model
model_path = os.path.join(os.path.dirname(__file__), 'model_linear.pkl')
model = joblib.load(model_path)

# Constants for Moore's Law (Base: Intel 4004 in 1971)
MOORES_BASE_YEAR = 1971
MOORES_BASE_COUNT = 2300


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json

        # 1. Parse Inputs
        year = float(data['year'])
        node_size = float(data['node_size'])
        area = float(data['area'])
        trans_density = float(data['trans_density'])
        power_density = float(data['power_density'])

        # 2. Log Transforms (Matches training)
        # Features: ['Year', 'Log_Node', 'Log_Area', 'Log_Density', 'Power Density']
        log_node = np.log10(node_size) if node_size > 0 else 0
        log_area = np.log10(area) if area > 0 else 0
        log_density = np.log10(trans_density) if trans_density > 0 else 0

        input_data = pd.DataFrame([[year, log_node, log_area, log_density, power_density]],
                                  columns=['Year', 'Log_Node', 'Log_Area', 'Log_Density', 'Power Density (W/cm²)'])

        # 3. Predict
        pred_log = model.predict(input_data)[0]
        pred_count = 10 ** pred_log

        # 4. Confidence Interval (Based on your Mean Residual Error ~0.16)
        # We'll use +/- 20% as a safe margin for the "Likely Range"
        lower_bound = int(pred_count * (1 - 0.20))
        upper_bound = int(pred_count * (1 + 0.20))

        # 5. Moore's Law Comparison (Doubles every 2 years)
        # Formula: Base * 2^((Year - 1971) / 2)
        years_passed = year - MOORES_BASE_YEAR
        moores_projection = MOORES_BASE_COUNT * (2 ** (years_passed / 2))

        # Calculate deviation percentage
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


@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    try:
        if 'file' not in request.files:
            return "No file uploaded", 400

        file = request.files['file']
        if file.filename == '':
            return "No file selected", 400

        # Read CSV
        df = pd.read_csv(file)

        # Ensure required columns exist
        required_cols = ['Year', 'Node Size (nm)', 'Area (mm²)', 'Transistor Density (tr/mm²)', 'Power Density (W/cm²)']
        if not all(col in df.columns for col in required_cols):
            return f"CSV must contain columns: {', '.join(required_cols)}", 400

        # Prepare features
        features = pd.DataFrame()
        features['Year'] = df['Year']
        features['Log_Node'] = np.log10(df['Node Size (nm)'])
        features['Log_Area'] = np.log10(df['Area (mm²)'])
        features['Log_Density'] = np.log10(df['Transistor Density (tr/mm²)'])
        features['Power Density (W/cm²)'] = df['Power Density (W/cm²)']

        # Predict
        pred_logs = model.predict(features)
        df['Predicted Count'] = 10 ** pred_logs
        df['Predicted Count'] = df['Predicted Count'].astype(int)

        # Return CSV
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='predictions.csv')

    except Exception as e:
        return str(e), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)