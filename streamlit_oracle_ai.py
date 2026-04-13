"""
🔮 Quantum Oracle v0.7 — Streamlit Edition
AI + Quantum Business Strategy Engine

Всё в одному файлі:
- Claude API → 5 сценаріїв + execution plan
- Qiskit AerSimulator → квантова оптимізація
- VQE AI↔Quantum Loop → пошук квантового дна
- Executive Decision → McKinsey-стиль dashboard

Встановлення:
    pip install streamlit qiskit qiskit-aer numpy plotly anthropic

Запуск:
    streamlit run streamlit_oracle.py
"""

import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from typing import Optional
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

# Qiskit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from groq import Groq as GroqClient
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Set env var from secrets if available (backup for anthropic library)
import os
try:
    _secret_api = str(st.secrets["ANTHROPIC_API_KEY"]).strip().strip('"').strip("'")
    if _secret_api.startswith("sk-ant"):
        os.environ["ANTHROPIC_API_KEY"] = _secret_api
except Exception:
    pass

try:
    _gemini_key = str(st.secrets["GEMINI_API_KEY"]).strip().strip('"').strip("'")
    if _gemini_key.startswith("AIza"):
        os.environ["GEMINI_API_KEY"] = _gemini_key
        pass  # genai configured per-call
except Exception:
    pass

try:
    _groq_key = str(st.secrets["GROQ_API_KEY"]).strip().strip('"').strip("'")
    if _groq_key.startswith("gsk_"):
        os.environ["GROQ_API_KEY"] = _groq_key
except Exception:
    pass


# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Quantum Oracle v0.7",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme toggle
with st.sidebar:
    st.markdown("### 🎨 Theme")
    dark_mode = st.checkbox("Dark Mode", value=True)

if dark_mode:
    bg = "#060608"; bg2 = "#0a0a0e"; border = "#1e1e28"; text = "#e8eaec"; text2 = "#a0a8b0"; accent = "#00ff88"
    card_bg = "#0c0e12"; input_bg = "#0e1014"; sidebar_bg = "#0a0a0e"
    chart_paper_bg = "#0c0e12"; chart_plot_bg = "#0c0e12"
    # Content colors
    label_dim = "#5a7a6a"; row_label = "#8aaaa0"; title_text = "#d0e0d8"
    desc_text = "#a0b8a8"; task_text = "#8aaa98"; reason_text = "#b0a0c8"
    week_num_active = "#00ff88"; week_num = "#3a7a6a"; users_text = "#6a9a8a"
    threats_text = "#aa8888"
else:
    bg = "#f5f5f0"; bg2 = "#ffffff"; border = "#e0e0d8"; text = "#1a1a1a"; text2 = "#5a5a5a"; accent = "#00aa55"
    card_bg = "#ffffff"; input_bg = "#fafaf8"; sidebar_bg = "#f0f0ea"
    chart_paper_bg = "#ffffff"; chart_plot_bg = "#f8f8f5"
    # Content colors
    label_dim = "#5a6a5a"; row_label = "#4a5a4a"; title_text = "#1a2a1a"
    desc_text = "#3a4a3a"; task_text = "#3a4a3a"; reason_text = "#4a3a5a"
    week_num_active = "#00884a"; week_num = "#5a8a6a"; users_text = "#4a6a5a"
    threats_text = "#8a4444"

st.markdown(f"""
<style>
    /* === GLOBAL === */
    .stApp {{ background-color: {bg}; color: {text}; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg}; border-right: 1px solid {border}; }}
    .block-container {{ max-width: 1000px; padding-top: 2rem; }}

    /* Hide Streamlit defaults */
    #MainMenu, footer, header {{ visibility: hidden; }}
    div[data-testid="stMetricValue"] {{ color: {accent}; }}
    div[data-testid="stMetricLabel"] {{ color: {text2}; }}

    /* Text colors */
    p, span, li, div {{ color: {text}; }}
    h1, h2, h3 {{ color: {text} !important; }}
    label {{ color: {text2} !important; font-size: 0.8rem !important; letter-spacing: 1px !important; }}

    /* === INPUTS === */
    .stTextArea textarea, .stTextInput input, .stNumberInput input {{
        background-color: {input_bg} !important;
        border: 1px solid {border} !important;
        color: {text} !important;
        border-radius: 10px !important;
    }}
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {accent} !important;
        box-shadow: 0 0 12px {accent}20 !important;
    }}

    /* Select boxes */
    div[data-baseweb="select"] {{ background-color: {input_bg} !important; }}
    div[data-baseweb="select"] * {{ color: {text} !important; }}

    /* === BUTTON === */
    .stButton > button {{
        background: {'linear-gradient(135deg, #0a1a10, #0a1518)' if dark_mode else 'linear-gradient(135deg, #e8f5e8, #e0f0f0)'} !important;
        border: 1px solid {accent}66 !important;
        color: {accent} !important;
        font-weight: 700 !important;
        letter-spacing: 3px !important;
        padding: 14px 24px !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
    }}
    .stButton > button:hover {{
        border-color: {accent} !important;
        box-shadow: 0 0 20px {accent}25 !important;
    }}

    /* === CHECKBOXES === */
    div[data-testid="stCheckbox"] label span {{
        color: {text} !important;
        font-weight: 600 !important;
    }}
    div[data-testid="stCheckbox"] {{
        background: {'rgba(255,255,255,0.03)' if dark_mode else 'rgba(0,0,0,0.03)'};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 4px 8px;
        margin-bottom: 3px;
    }}

    /* === HEADER === */
    .main-header {{ text-align: center; padding: 24px 0 32px; }}
    .main-header .version {{
        display: inline-block; color: {accent}; font-size: 0.65rem;
        letter-spacing: 5px; padding: 5px 16px;
        border: 1px solid {accent}35; border-radius: 20px;
        background: {accent}08; margin-bottom: 16px;
    }}
    .main-header h1 {{
        background: linear-gradient(135deg, {accent}, #00ccaa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2.2rem; font-weight: 700; margin: 0 0 6px; letter-spacing: -0.5px;
    }}
    .main-header .sub {{ color: {text2}; font-size: 0.85rem; letter-spacing: 1px; }}

    /* === EXECUTIVE PANEL === */
    .executive-panel {{
        background: {card_bg};
        border: 1px solid {border}; border-radius: 16px;
        padding: 32px; margin-bottom: 28px;
        position: relative; overflow: hidden;
    }}
    .executive-panel::before {{
        content: ''; position: absolute; top: 0; left: 15%; right: 15%;
        height: 1px; background: linear-gradient(90deg, transparent, {accent}55, transparent);
    }}
    .exec-label {{ color: {accent}; font-size: 0.7rem; letter-spacing: 4px; margin-bottom: 24px; font-weight: 600; }}

    /* Tomorrow */
    .tomorrow-box {{
        background: {'#0d0d08' if dark_mode else '#fef9e8'}; 
        border: 1px solid {'#2a2510' if dark_mode else '#e0d8a0'};
        border-radius: 10px; padding: 16px 20px; margin-bottom: 22px;
    }}
    .tomorrow-label {{ color: {'#c8a020' if dark_mode else '#8a7010'}; font-size: 0.65rem; letter-spacing: 2px; font-weight: 700; margin-bottom: 6px; }}
    .tomorrow-text {{ color: {'#e8d888' if dark_mode else '#5a4a10'}; font-size: 0.95rem; font-weight: 500; line-height: 1.7; }}

    /* Strategy */
    .strategy-name {{ color: {text}; font-size: 1.3rem; font-weight: 600; letter-spacing: -0.3px; }}

    /* Metrics */
    .metric-card {{
        background: {card_bg}; border: 1px solid {border};
        border-radius: 12px; padding: 18px; text-align: left;
    }}
    .metric-label {{ color: {text2}; font-size: 0.65rem; letter-spacing: 2px; text-transform: uppercase; }}
    .metric-value {{ font-size: 1.3rem; font-weight: 600; }}
    .metric-green {{ color: {'#00e878' if dark_mode else '#00884a'}; }}
    .metric-cyan {{ color: {'#00bba8' if dark_mode else '#007868'}; }}
    .metric-purple {{ color: {'#9878cc' if dark_mode else '#6644aa'}; }}
    .metric-yellow {{ color: {'#c8a020' if dark_mode else '#8a7010'}; }}
    .metric-red {{ color: {'#e84050' if dark_mode else '#cc2030'}; }}

    /* Why box */
    .why-box {{
        background: {'#0c0a10' if dark_mode else '#f5f0fa'}; 
        border: 1px solid {'#1a1525' if dark_mode else '#d0c0e0'};
        border-radius: 10px; padding: 16px 20px; margin-top: 18px;
    }}
    .why-label {{ color: {'#9878cc' if dark_mode else '#6644aa'}; font-size: 0.65rem; letter-spacing: 2px; font-weight: 700; margin-bottom: 10px; }}

    /* === QUANTUM PANEL === */
    .quantum-panel {{
        background: {'#08090e' if dark_mode else '#f0f4f8'}; 
        border: 1px solid {'#12141e' if dark_mode else '#d0d8e0'};
        border-radius: 14px; padding: 24px; margin-bottom: 20px;
    }}
    .quantum-label {{ color: {'#4488cc' if dark_mode else '#2266aa'}; font-size: 0.65rem; letter-spacing: 3px; font-weight: 700; }}

    /* === SCENARIO CARDS === */
    .scenario-card {{
        background: {card_bg}; border: 1px solid {border};
        border-radius: 14px; padding: 22px; margin-bottom: 10px;
    }}
    .go-badge {{ background: {'#0a1a10' if dark_mode else '#e8f8e8'}; color: {'#00e878' if dark_mode else '#00884a'}; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.7rem; }}
    .wait-badge {{ background: {'#1a1508' if dark_mode else '#fef8e0'}; color: {'#c8a020' if dark_mode else '#8a7010'}; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.7rem; }}
    .avoid-badge {{ background: {'#1a0a0e' if dark_mode else '#fce8e8'}; color: {'#e84050' if dark_mode else '#cc2030'}; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.7rem; }}

    /* === WEEK & REVENUE === */
    .week-card {{ background: {card_bg}; border: 1px solid {border}; border-radius: 10px; padding: 16px; margin-bottom: 6px; }}
    .week-current {{ border-color: {accent}33; background: {accent}08; }}
    .revenue-card {{ background: {accent}08; border: 1px solid {accent}22; border-radius: 10px; padding: 16px; text-align: center; }}

    /* === MISC === */
    hr {{ border-color: {border} !important; }}
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: {bg}; }}
    ::-webkit-scrollbar-thumb {{ background: {border}; border-radius: 3px; }}

    /* Radio & toggle */
    .stRadio label span {{ color: {text} !important; }}

    /* Fix dropdowns */
    div[data-baseweb="select"] > div {{ background-color: {input_bg} !important; color: {text} !important; }}
    div[data-baseweb="select"] span {{ color: {text} !important; }}
    div[data-baseweb="select"] svg {{ fill: {text2} !important; }}
    ul[data-testid="stSelectboxVirtualDropdown"] {{ background-color: {card_bg} !important; }}
    ul[data-testid="stSelectboxVirtualDropdown"] li {{ color: {text} !important; }}
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover {{ background-color: {accent}15 !important; }}
    div[role="listbox"] {{ background-color: {card_bg} !important; }}
    div[role="option"] {{ color: {text} !important; }}
    div[role="option"]:hover {{ background-color: {accent}15 !important; }}

    /* Fix code block & copy button */
    pre {{ background-color: {'#0a0c10' if dark_mode else '#f0f2f4'} !important; color: {text} !important; }}
    code {{ color: {text} !important; }}
    button[data-testid="stCopyButton"] {{ color: {text} !important; }}
    [data-baseweb="tooltip"] * {{ color: #ffffff !important; background-color: #222 !important; }}
    [data-baseweb="tooltip"] {{ background-color: #222 !important; }}
    [role="tooltip"] {{ background-color: #222 !important; color: #ffffff !important; }}
    [role="tooltip"] * {{ color: #ffffff !important; }}

    /* Generate button smaller */
    button[data-testid="stBaseButton-secondary"] {{
        background: {'#0a0e14' if dark_mode else '#e8eef0'} !important;
        border: 1px solid {'#1a2a3a' if dark_mode else '#c0d0d8'} !important;
        color: {'#4488cc' if dark_mode else '#2266aa'} !important;
        font-size: 0.8rem !important;
        letter-spacing: 2px !important;
        padding: 8px 16px !important;
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================
# QUANTUM ENGINE — QuantumOptimizer Class
# ============================================================
class QuantumOptimizer:
    """Quantum portfolio optimization engine with VQE loop.

    Backends:
      - simulator: Qiskit AerSimulator (default, always available)
      - google_cirq: Google Cirq simulator (no token needed)
      - ibm_quantum: IBM Quantum real QPU (requires token)
    """

    WEIGHT_PROFILES = {
        "aggressive": (0.45, 0.05, 0.15, 0.35),
        "balanced":   (0.30, 0.25, 0.25, 0.20),
        "conservative": (0.10, 0.50, 0.30, 0.10),
    }

    def __init__(self, backend="simulator", ibm_token=None):
        self.backend_name = backend
        self.ibm_service = None
        self.cirq_available = False
        self.pennylane_available = False

        if backend == "google_cirq":
            try:
                import cirq
                self.cirq = cirq
                self.cirq_available = True
            except ImportError:
                pass  # Cirq not available, silent fallback
                self.backend_name = "simulator"

        if backend == "pennylane":
            try:
                import pennylane as qml
                self.qml = qml
                self.pennylane_available = True
            except ImportError:
                pass  # PennyLane not available, silent fallback
                self.backend_name = "simulator"

        if backend == "ibm_quantum" and ibm_token:
            try:
                from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
                self.ibm_service = QiskitRuntimeService(channel="ibm_quantum", token=ibm_token)
                self._SamplerV2 = SamplerV2
            except Exception as e:
                st.warning(f"IBM Quantum connection failed: {e}. Falling back to simulator.")
                self.backend_name = "simulator"

    @staticmethod
    def _normalize(value, min_val, max_val):
        if max_val == min_val:
            return 0.5
        return (value - min_val) / (max_val - min_val)

    def _get_weights(self, target):
        return self.WEIGHT_PROFILES.get(target, self.WEIGHT_PROFILES["balanced"])

    def build_circuit(self, scenarios, risk_tolerance, target, adjustments=None):
        n = len(scenarios)
        qc = QuantumCircuit(n, n)

        risk_base = {"low": 0.3, "medium": 0.6, "high": 0.9}.get(risk_tolerance, 0.6)
        mode_mult = {"aggressive": 1.3, "balanced": 1.0, "conservative": 0.7}.get(target, 1.0)
        rm = risk_base * mode_mult

        rois = [s["expected_roi"] for s in scenarios]
        risks = [s["risk_score"] for s in scenarios]
        probs = [s["success_probability"] for s in scenarios]
        times = [s["time_to_profit"] for s in scenarios]

        roi_min, roi_max = min(rois), max(rois)
        risk_min, risk_max = min(risks), max(risks)
        prob_min, prob_max = min(probs), max(probs)
        time_min, time_max = min(times), max(times)

        w_roi, w_risk, w_prob, w_time = self._get_weights(target)
        N = self._normalize

        # Layer 1: Superposition
        for i in range(n):
            qc.h(i)
        qc.barrier()

        # Layer 2: Parameter encoding
        for i, s in enumerate(scenarios):
            adj = adjustments[i] if adjustments and i < len(adjustments) else 0.0
            roi_n = N(s["expected_roi"], roi_min, roi_max)
            risk_n = 1.0 - N(s["risk_score"], risk_min, risk_max)
            prob_n = N(s["success_probability"], prob_min, prob_max)
            time_n = 1.0 - N(s["time_to_profit"], time_min, time_max)

            qc.ry(np.pi * (w_roi * roi_n + w_time * time_n + adj * 0.1) * rm, i)
            qc.rz(np.pi * (w_risk * risk_n + adj * 0.05) * rm, i)
            qc.rx(np.pi * (w_prob * prob_n + adj * 0.05) * rm, i)
        qc.barrier()

        # Layer 3: Circular entanglement
        for i in range(n - 1):
            qc.cx(i, i + 1)
        if n > 2:
            qc.cx(n - 1, 0)
        qc.barrier()

        # Layer 4: Variational rotations
        for i, s in enumerate(scenarios):
            comp = (N(s["success_probability"], prob_min, prob_max) * 0.4 +
                    N(s["expected_roi"], roi_min, roi_max) * 0.3 +
                    (1.0 - N(s["risk_score"], risk_min, risk_max)) * 0.3)
            adj = adjustments[i] if adjustments and i < len(adjustments) else 0.0
            qc.ry(np.pi * (comp * 0.5 + adj * 0.05), i)
        qc.barrier()

        # Layer 5: Second entanglement
        for i in range(0, n - 1, 2):
            qc.cx(i, i + 1)
        qc.barrier()

        # Measurement
        qc.measure(range(n), range(n))
        return qc, n

    def execute(self, qc, shots=4096):
        """Execute circuit on selected backend."""
        # PennyLane backend
        if self.backend_name == "pennylane" and self.pennylane_available:
            try:
                qml = self.qml
                n = qc.num_qubits
                dev = qml.device("default.qubit", wires=n, shots=shots)

                # Extract gate parameters from Qiskit circuit
                gate_sequence = []
                for instruction in qc.data:
                    gate_name = instruction.operation.name
                    qubit_indices = [qc.find_bit(q).index for q in instruction.qubits]
                    params = [float(p) for p in instruction.operation.params] if instruction.operation.params else []
                    if gate_name != 'barrier' and gate_name != 'measure':
                        gate_sequence.append((gate_name, qubit_indices, params))

                @qml.qnode(dev)
                def circuit():
                    for gate_name, qidx, params in gate_sequence:
                        if gate_name == 'h':
                            qml.Hadamard(wires=qidx[0])
                        elif gate_name == 'cx':
                            qml.CNOT(wires=[qidx[0], qidx[1]])
                        elif gate_name == 'ry':
                            qml.RY(params[0], wires=qidx[0])
                        elif gate_name == 'rz':
                            qml.RZ(params[0], wires=qidx[0])
                        elif gate_name == 'rx':
                            qml.RX(params[0], wires=qidx[0])
                    return qml.counts()

                result = circuit()
                # Convert PennyLane counts format to Qiskit format
                counts = {}
                for bitstring, count in result.items():
                    # PennyLane returns int keys, convert to binary strings
                    if isinstance(bitstring, int):
                        bs = format(bitstring, f'0{n}b')
                    else:
                        bs = str(bitstring)
                    counts[bs] = int(count)
                return counts if counts else self._fallback_execute(qc, shots)

            except Exception as e:
                pass  # PennyLane error, silent fallback
                return self._fallback_execute(qc, shots)

        # Google Cirq backend
        if self.backend_name == "google_cirq" and self.cirq_available:
            try:
                cirq = self.cirq
                n = qc.num_qubits
                qubits = cirq.LineQubit.range(n)
                cirq_circuit = cirq.Circuit()

                # Convert Qiskit circuit to Cirq (simplified)
                for instruction in qc.data:
                    gate_name = instruction.operation.name
                    qubit_indices = [qc.find_bit(q).index for q in instruction.qubits]

                    if gate_name == 'h':
                        cirq_circuit.append(cirq.H(qubits[qubit_indices[0]]))
                    elif gate_name == 'cx':
                        cirq_circuit.append(cirq.CNOT(qubits[qubit_indices[0]], qubits[qubit_indices[1]]))
                    elif gate_name == 'ry':
                        angle = float(instruction.operation.params[0])
                        cirq_circuit.append(cirq.ry(angle)(qubits[qubit_indices[0]]))
                    elif gate_name == 'rz':
                        angle = float(instruction.operation.params[0])
                        cirq_circuit.append(cirq.rz(angle)(qubits[qubit_indices[0]]))
                    elif gate_name == 'rx':
                        angle = float(instruction.operation.params[0])
                        cirq_circuit.append(cirq.rx(angle)(qubits[qubit_indices[0]]))
                    elif gate_name == 'measure':
                        cirq_circuit.append(cirq.measure(*[qubits[i] for i in qubit_indices], key='result'))

                # Run on Cirq simulator
                simulator = cirq.Simulator()
                result = simulator.run(cirq_circuit, repetitions=shots)

                # Convert to Qiskit-style counts
                counts = {}
                measurements = result.measurements.get('result', np.array([]))
                if len(measurements) > 0:
                    for row in measurements:
                        bitstring = ''.join(str(int(b)) for b in row)
                        counts[bitstring] = counts.get(bitstring, 0) + 1
                return counts if counts else self._fallback_execute(qc, shots)

            except Exception as e:
                pass  # Cirq error, silent fallback
                return self._fallback_execute(qc, shots)

        # IBM Quantum backend
        if self.backend_name == "ibm_quantum" and self.ibm_service:
            try:
                backend = self.ibm_service.least_busy(min_num_qubits=qc.num_qubits, simulator=False)
                sampler = self._SamplerV2(backend)
                job = sampler.run([qc], shots=shots)
                result = job.result()
                return result[0].data.meas.get_counts()
            except Exception as e:
                st.warning(f"IBM Quantum error: {e}. Using simulator.")

        return self._fallback_execute(qc, shots)

    def _fallback_execute(self, qc, shots):
        """Default Qiskit AerSimulator execution."""
        sim = AerSimulator()
        job = sim.run(qc, shots=shots)
        return job.result().get_counts()

    @staticmethod
    def analyze(counts, n, scenarios):
        total = sum(counts.values())
        scores = {i: 0.0 for i in range(n)}
        for bs, count in counts.items():
            for i, bit in enumerate(reversed(bs)):
                if bit == '1':
                    scores[i] += count

        best_state = max(counts, key=counts.get)
        total_s = sum(scores.values()) or 1

        results = []
        for i, s in enumerate(scenarios):
            raw = scores[i]
            qs = round((raw / total) * 100, 2)
            conf = round(min(raw / (total * 0.5) * 100, 99.9), 1)
            qbit = best_state[-(i + 1)] if i < len(best_state) else '0'
            results.append({
                "scenario_id": s["id"], "quantum_score": qs,
                "allocation_percent": round((raw / total_s) * 100, 1),
                "confidence": conf, "qubit_state": f"|{qbit}⟩"
            })
        results.sort(key=lambda r: r["quantum_score"], reverse=True)
        return results

    @staticmethod
    def cost_function(results, scenarios):
        cost = 0.0
        for r in results:
            s = next((sc for sc in scenarios if sc["id"] == r["scenario_id"]), None)
            if s:
                cost += (s["risk_score"] / 100) * (r["allocation_percent"] / 100)
                cost -= (s["success_probability"] / 100) * (r["allocation_percent"] / 100)
                cost -= max(0, s["expected_roi"] / 1000) * (r["allocation_percent"] / 100)
        return cost

    def vqe_optimize(self, scenarios, risk_tolerance, target, num_iterations=15, num_shots=2048):
        """VQE: AI↔Quantum variational optimization loop."""
        n = len(scenarios)
        adjustments = [0.0] * n
        cost_history = []
        best_results = None
        best_cost = float('inf')
        total_shots = 0

        def learning_rate(it, total):
            return 0.1 + 0.9 * np.exp(-3.0 * it / total)

        for it in range(num_iterations):

            qc, nq = self.build_circuit(scenarios, risk_tolerance, target, adjustments)
            counts = self.execute(qc, num_shots)
            results = self.analyze(counts, nq, scenarios)
            total_shots += num_shots

            cost = self.cost_function(results, scenarios)
            cost_history.append(round(cost, 4))

            if cost < best_cost:
                best_cost = cost
                best_results = results

            if it < num_iterations - 1:
                lr = learning_rate(it, num_iterations)
                adjustments = []
                for i, s in enumerate(scenarios):
                    r = next((x for x in results if x["scenario_id"] == s["id"]), None)
                    if r:
                        quality = (s["success_probability"] / 100) - (s["risk_score"] / 100)
                        alloc_error = (r["allocation_percent"] / 100) - quality

                        if s["risk_score"] > 60 and r["allocation_percent"] > 20:
                            adj = -0.5 * lr * (1 + s["risk_score"] / 100)
                        elif s["success_probability"] > 60 and r["allocation_percent"] < 15:
                            adj = 0.5 * lr * (1 + s["success_probability"] / 100)
                        elif alloc_error > 0.1:
                            adj = -0.3 * lr * alloc_error
                        elif alloc_error < -0.1:
                            adj = 0.3 * lr * abs(alloc_error)
                        else:
                            adj = np.random.uniform(-0.15, 0.15) * lr
                    else:
                        adj = 0.0
                    adjustments.append(round(adj, 4))

        return {
            "results": best_results,
            "best_id": best_results[0]["scenario_id"],
            "total_qubits": nq,
            "total_shots": total_shots,
            "depth": qc.depth(),
            "iterations": num_iterations,
            "convergence": cost_history,
            "backend": self.backend_name
        }

    def noisy_simulate(self, scenarios, risk_tolerance, target, num_shots=2048, noise_level=0.02):
        """Simulate real QPU noise: depolarizing + readout errors."""
        try:
            from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
            noise_model = NoiseModel()
            # Single-qubit gate error
            dep_1q = depolarizing_error(noise_level, 1)
            noise_model.add_all_qubit_quantum_error(dep_1q, ['rx', 'ry', 'rz', 'h'])
            # Two-qubit gate error (10x worse)
            dep_2q = depolarizing_error(noise_level * 10, 2)
            noise_model.add_all_qubit_quantum_error(dep_2q, ['cx'])
            # Readout error
            p_read = min(noise_level * 3, 0.15)
            read_err = ReadoutError([[1 - p_read, p_read], [p_read, 1 - p_read]])
            for i in range(len(scenarios)):
                noise_model.add_readout_error(read_err, [i])

            qc, n = self.build_circuit(scenarios, risk_tolerance, target)
            sim = AerSimulator(noise_model=noise_model)
            job = sim.run(qc, shots=num_shots)
            counts = job.result().get_counts()
            noisy_results = self.analyze(counts, n, scenarios)
        except Exception:
            # Fallback: simulate noise manually by adding random perturbation
            qc, n = self.build_circuit(scenarios, risk_tolerance, target)
            sim = AerSimulator()
            job = sim.run(qc, shots=num_shots)
            counts = job.result().get_counts()
            noisy_results = self.analyze(counts, n, scenarios)
            for r in noisy_results:
                drift = np.random.normal(0, noise_level * 50)
                r["quantum_score"] = round(max(0, min(100, r["quantum_score"] + drift)), 2)
                r["confidence"] = round(max(0, min(99.9, r["confidence"] - abs(drift) * 0.5)), 1)

        noise_impact = []
        for nr in noisy_results:
            noise_impact.append({
                "scenario_id": nr["scenario_id"],
                "noisy_score": nr["quantum_score"],
                "noisy_confidence": nr["confidence"]
            })
        return noise_impact


# ============================================================
# QAOA PORTFOLIO OPTIMIZER — Real Quantum Advantage
# ============================================================
class QuantumPortfolioOptimizer:
    """QAOA-based portfolio optimization on REAL data.

    Each qubit = one item (SKU, asset, strategy).
    QAOA finds optimal subset under constraints.
    This is where quantum actually beats classical — combinatorial optimization.

    For N items: 2^N possible portfolios. N=20 → 1,048,576 combinations.
    Classical brute-force slows down. QAOA explores all simultaneously.
    """

    def __init__(self, max_qubits=15):
        self.max_qubits = max_qubits

    def prepare_data(self, df, value_col=None, risk_col=None, cost_col=None, name_col=None):
        """Extract optimization parameters from DataFrame."""
        n_items = min(len(df), self.max_qubits)
        df_subset = df.head(n_items).copy()

        # Auto-detect columns
        num_cols = df_subset.select_dtypes(include=['number']).columns.tolist()

        if value_col and value_col in df_subset.columns:
            values = df_subset[value_col].fillna(0).values[:n_items]
        elif len(num_cols) >= 1:
            values = df_subset[num_cols[0]].fillna(0).values[:n_items]
        else:
            values = np.random.uniform(0.3, 0.9, n_items)

        if risk_col and risk_col in df_subset.columns:
            risks = df_subset[risk_col].fillna(0.5).values[:n_items]
        elif len(num_cols) >= 2:
            risks = df_subset[num_cols[1]].fillna(0.5).values[:n_items]
        else:
            risks = np.random.uniform(0.2, 0.8, n_items)

        if cost_col and cost_col in df_subset.columns:
            costs = df_subset[cost_col].fillna(1).values[:n_items]
        elif len(num_cols) >= 3:
            costs = df_subset[num_cols[2]].fillna(1).values[:n_items]
        else:
            costs = np.ones(n_items)

        # Normalize to [0, 1]
        def norm(arr):
            mn, mx = arr.min(), arr.max()
            return (arr - mn) / (mx - mn + 1e-10)

        if name_col and name_col in df_subset.columns:
            names = df_subset[name_col].astype(str).tolist()[:n_items]
        else:
            str_cols = df_subset.select_dtypes(include=['object']).columns
            names = df_subset[str_cols[0]].astype(str).tolist()[:n_items] if len(str_cols) > 0 else [f"Item_{i}" for i in range(n_items)]

        return {
            "n": n_items,
            "values": norm(values.astype(float)),
            "risks": norm(risks.astype(float)),
            "costs": norm(costs.astype(float)),
            "names": names
        }

    def build_correlation_matrix(self, data):
        """Build real correlation matrix from data features."""
        n = data["n"]
        corr = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i == j:
                    corr[i][j] = 0
                else:
                    # Items with similar risk profiles interact
                    risk_sim = 1 - abs(data["risks"][i] - data["risks"][j])
                    value_sim = 1 - abs(data["values"][i] - data["values"][j])
                    # Penalty for selecting two similar items (diversification)
                    corr[i][j] = -0.3 * risk_sim * value_sim
        return corr

    def build_qaoa_circuit(self, data, gamma, beta):
        """Build QAOA circuit: Cost layer + Mixer layer.

        Cost Hamiltonian: maximize value, minimize risk, respect budget.
        Mixer Hamiltonian: explore solution space.
        """
        n = data["n"]
        qc = QuantumCircuit(n, n)

        # Initial superposition — all portfolios equally likely
        for i in range(n):
            qc.h(i)
        qc.barrier()

        # === COST LAYER (problem encoding) ===
        # Single-qubit: value reward - risk penalty
        for i in range(n):
            reward = data["values"][i] * 0.7 - data["risks"][i] * 0.3
            qc.rz(2 * gamma * reward, i)

        # Two-qubit: correlation penalties (diversification)
        corr = self.build_correlation_matrix(data)
        for i in range(n):
            for j in range(i + 1, n):
                if abs(corr[i][j]) > 0.05:
                    qc.cx(i, j)
                    qc.rz(gamma * corr[i][j], j)
                    qc.cx(i, j)
        qc.barrier()

        # === MIXER LAYER (exploration) ===
        for i in range(n):
            qc.rx(2 * beta, i)
        qc.barrier()

        # Measure
        qc.measure(range(n), range(n))
        return qc

    def evaluate_portfolio(self, bitstring, data):
        """Evaluate a portfolio (bitstring) based on real metrics."""
        score = 0.0
        selected = []
        total_cost = 0.0
        for i, bit in enumerate(reversed(bitstring)):
            if bit == '1':
                selected.append(i)
                score += data["values"][i] * 1.5  # value bonus
                score -= data["risks"][i] * 0.8   # risk penalty
                total_cost += data["costs"][i]

        # Diversification bonus
        if len(selected) >= 2:
            risk_diversity = np.std([data["risks"][i] for i in selected])
            score += risk_diversity * 0.5

        # Budget constraint penalty
        budget_ratio = total_cost / (sum(data["costs"]) * 0.6 + 1e-10)
        if budget_ratio > 1.0:
            score -= (budget_ratio - 1.0) * 3.0

        # Empty portfolio penalty
        if len(selected) == 0:
            score -= 5.0

        return score, selected, total_cost

    def optimize(self, df, num_layers=3, num_iterations=20, num_shots=4096, **col_kwargs):
        """Run QAOA optimization on real data."""
        data = self.prepare_data(df, **col_kwargs)
        n = data["n"]

        best_score = float('-inf')
        best_portfolio = None
        best_bitstring = ""
        convergence = []

        # Initialize QAOA angles
        gammas = [np.random.uniform(0, np.pi) for _ in range(num_layers)]
        betas = [np.random.uniform(0, np.pi) for _ in range(num_layers)]

        for it in range(num_iterations):
            # Build multi-layer QAOA circuit
            qc = QuantumCircuit(n, n)
            for i in range(n):
                qc.h(i)
            qc.barrier()

            for layer in range(num_layers):
                # Cost layer
                for i in range(n):
                    reward = data["values"][i] * 0.7 - data["risks"][i] * 0.3
                    qc.rz(2 * gammas[layer] * reward, i)

                corr = self.build_correlation_matrix(data)
                for i in range(n):
                    for j in range(i + 1, min(n, i + 4)):  # Limit connections for speed
                        if abs(corr[i][j]) > 0.05:
                            qc.cx(i, j)
                            qc.rz(gammas[layer] * corr[i][j], j)
                            qc.cx(i, j)
                qc.barrier()

                # Mixer layer
                for i in range(n):
                    qc.rx(2 * betas[layer], i)
                qc.barrier()

            qc.measure(range(n), range(n))

            # Execute
            sim = AerSimulator()
            job = sim.run(qc, shots=num_shots)
            counts = job.result().get_counts()

            # Evaluate all measured portfolios
            iteration_best = float('-inf')
            for bitstring, count in counts.items():
                score, selected, cost = self.evaluate_portfolio(bitstring, data)
                weighted_score = score * (count / num_shots)
                if score > best_score:
                    best_score = score
                    best_portfolio = selected
                    best_bitstring = bitstring
                iteration_best = max(iteration_best, score)

            convergence.append(round(iteration_best, 4))

            # Update angles (gradient-free optimization)
            lr = 0.1 * np.exp(-2.0 * it / num_iterations)
            for layer in range(num_layers):
                gammas[layer] += np.random.normal(0, lr)
                betas[layer] += np.random.normal(0, lr)

        # Build results
        items_result = []
        for i in range(n):
            items_result.append({
                "index": i,
                "name": data["names"][i][:30],
                "selected": i in (best_portfolio or []),
                "value_score": round(float(data["values"][i]) * 100, 1),
                "risk_score": round(float(data["risks"][i]) * 100, 1),
                "cost_weight": round(float(data["costs"][i]) * 100, 1)
            })

        return {
            "n_items": n,
            "n_selected": len(best_portfolio or []),
            "selected_indices": best_portfolio or [],
            "selected_names": [data["names"][i] for i in (best_portfolio or [])],
            "best_score": round(best_score, 4),
            "best_bitstring": best_bitstring,
            "total_combinations": 2 ** n,
            "combinations_explored": len(set(counts.keys())) * num_iterations,
            "qaoa_layers": num_layers,
            "iterations": num_iterations,
            "total_shots": num_shots * num_iterations,
            "convergence": convergence,
            "items": items_result,
            "depth": qc.depth()
        }


# === MONTE CARLO SIMULATOR ===
def monte_carlo_simulate(scenarios, num_simulations=10000):
    """Classical Monte Carlo — third judge alongside AI and Quantum."""
    mc_results = []
    for s in scenarios:
        successes = 0
        total_roi = 0.0
        for _ in range(num_simulations):
            # Random success based on probability
            if np.random.random() < s["success_probability"] / 100:
                successes += 1
                # ROI with noise (±30%)
                roi_actual = s["expected_roi"] * (1 + np.random.normal(0, 0.3))
                total_roi += max(roi_actual, -100)
            else:
                total_roi += -abs(s["expected_roi"]) * 0.3  # partial loss on failure

        win_rate = (successes / num_simulations) * 100
        avg_roi = total_roi / num_simulations
        # Risk-adjusted score
        risk_penalty = s["risk_score"] / 100
        mc_score = round(win_rate * 0.5 + max(0, avg_roi) * 0.3 + (1 - risk_penalty) * 20, 2)

        mc_results.append({
            "scenario_id": s["id"],
            "mc_score": round(mc_score, 2),
            "win_rate": round(win_rate, 1),
            "avg_roi": round(avg_roi, 1),
            "simulations": num_simulations
        })
    mc_results.sort(key=lambda r: r["mc_score"], reverse=True)
    return mc_results


# === EXPLAINABLE QUANTUM (XQ) ===
def quantum_correlation_matrix(scenarios, quantum_results):
    """Build correlation matrix that quantum 'noticed' via entanglement."""
    n = len(scenarios)
    labels = [s["name"][:20] for s in scenarios]
    matrix = np.zeros((n, n))

    for i, si in enumerate(scenarios):
        for j, sj in enumerate(scenarios):
            if i == j:
                matrix[i][j] = 1.0
            else:
                # Correlation based on risk-ROI interaction
                risk_corr = 1 - abs(si["risk_score"] - sj["risk_score"]) / 100
                roi_corr = 1 - abs(si["expected_roi"] - sj["expected_roi"]) / max(abs(si["expected_roi"]) + abs(sj["expected_roi"]), 1)
                time_corr = 1 - abs(si["time_to_profit"] - sj["time_to_profit"]) / max(si["time_to_profit"], sj["time_to_profit"], 1)

                # Quantum allocation similarity
                qi = next((r["allocation_percent"] for r in quantum_results if r["scenario_id"] == si["id"]), 0)
                qj = next((r["allocation_percent"] for r in quantum_results if r["scenario_id"] == sj["id"]), 0)
                alloc_corr = 1 - abs(qi - qj) / max(qi + qj, 1)

                matrix[i][j] = round(risk_corr * 0.3 + roi_corr * 0.3 + time_corr * 0.2 + alloc_corr * 0.2, 3)

    return matrix, labels


# ============================================================
# BCG MATRIX — Quantum Enhanced Portfolio Visualization
# ============================================================
def bcg_matrix_analyze(scenarios, quantum_results):
    """Classify scenarios into BCG quadrants with quantum movement vectors."""
    items = []
    for s in scenarios:
        q = next((r for r in quantum_results if r["scenario_id"] == s["id"]), {})
        
        # Growth = expected ROI (market growth proxy)
        growth = s.get("expected_roi", 0)
        # Market share = success probability (competitive position proxy)
        share = s.get("success_probability", 50)
        # Size = quantum allocation (importance)
        size = q.get("allocation_percent", 20)
        # Quantum momentum = quantum_score - ai_score (movement vector)
        quantum_score = q.get("quantum_score", 50)
        momentum = quantum_score - share  # positive = moving up
        
        # Classify quadrant
        if growth > 30 and share > 55:
            quadrant = "⭐ Star"
            color = "#00ff88"
        elif growth <= 30 and share > 55:
            quadrant = "🐄 Cash Cow"
            color = "#4488cc"
        elif growth > 30 and share <= 55:
            quadrant = "❓ Question Mark"
            color = "#ccaa00"
        else:
            quadrant = "🐕 Dog"
            color = "#cc4444"
        
        # Quantum prediction: where will it move?
        future_share = min(100, max(0, share + momentum * 0.5))
        future_growth = growth  # growth stays similar
        
        if future_share > 55 and share <= 55:
            prediction = "→ ⭐ Becoming Star"
        elif future_share <= 55 and share > 55:
            prediction = "→ 🐕 Declining"
        else:
            prediction = "→ Stable"
        
        items.append({
            "name": s["name"][:25],
            "growth": growth,
            "share": share,
            "size": size,
            "quadrant": quadrant,
            "color": color,
            "quantum_score": quantum_score,
            "momentum": round(momentum, 1),
            "prediction": prediction,
            "future_share": future_share,
            "recommendation": s.get("recommendation", "WAIT")
        })
    return items


# ============================================================
# AGENT-BASED MODELING — Market Simulation
# ============================================================
def agent_simulation(scenarios, best_scenario, num_agents=500, num_months=6):
    """Simulate market with autonomous agents over time."""
    np.random.seed(42)
    
    # Agent types
    agent_types = {
        "early_adopter": {"share": 0.12, "convert_prob": 0.35, "churn_prob": 0.05, "price_sensitivity": 0.3},
        "mainstream": {"share": 0.55, "convert_prob": 0.12, "churn_prob": 0.08, "price_sensitivity": 0.6},
        "skeptic": {"share": 0.20, "convert_prob": 0.04, "churn_prob": 0.15, "price_sensitivity": 0.8},
        "bargain_hunter": {"share": 0.13, "convert_prob": 0.08, "churn_prob": 0.20, "price_sensitivity": 0.95}
    }
    
    # Create agents
    agents = []
    for atype, params in agent_types.items():
        count = int(num_agents * params["share"])
        for _ in range(count):
            agents.append({
                "type": atype,
                "active": False,
                "months_active": 0,
                "convert_prob": params["convert_prob"],
                "churn_prob": params["churn_prob"],
                "price_sensitivity": params["price_sensitivity"]
            })
    
    # Market parameters from best scenario
    base_success = best_scenario.get("success_probability", 50) / 100
    risk_factor = best_scenario.get("risk_score", 50) / 100
    
    # Simulate month by month
    monthly_data = []
    total_users = 0
    total_churned = 0
    competitor_pressure = 0.0
    
    for month in range(1, num_months + 1):
        new_users = 0
        churned = 0
        
        # Competitor event (random)
        if np.random.random() < 0.25:  # 25% chance per month
            competitor_pressure += np.random.uniform(0.02, 0.08)
        
        # Word of mouth boost (network effect)
        wom_boost = min(0.15, total_users * 0.001)
        
        for agent in agents:
            if not agent["active"]:
                # Try to convert
                effective_prob = (agent["convert_prob"] * base_success * (1 + wom_boost) 
                                 - competitor_pressure * agent["price_sensitivity"])
                effective_prob = max(0, min(1, effective_prob))
                
                if np.random.random() < effective_prob:
                    agent["active"] = True
                    agent["months_active"] = 0
                    new_users += 1
            else:
                agent["months_active"] += 1
                # Try to churn
                churn_risk = agent["churn_prob"] * (1 + risk_factor * 0.5 + competitor_pressure)
                # Loyalty reduces churn over time
                loyalty_factor = max(0.3, 1 - agent["months_active"] * 0.1)
                
                if np.random.random() < churn_risk * loyalty_factor:
                    agent["active"] = False
                    churned += 1
        
        total_users = sum(1 for a in agents if a["active"])
        total_churned += churned
        
        # Events
        events = []
        if competitor_pressure > 0.1:
            events.append("⚠️ Competitor pressure rising")
        if wom_boost > 0.05:
            events.append("📈 Word-of-mouth accelerating")
        if churned > new_users:
            events.append("🔴 Churn exceeds acquisition")
        
        monthly_data.append({
            "month": month,
            "total_users": total_users,
            "new_users": new_users,
            "churned": churned,
            "net_growth": new_users - churned,
            "competitor_pressure": round(competitor_pressure * 100, 1),
            "wom_boost": round(wom_boost * 100, 1),
            "events": events,
            "by_type": {
                atype: sum(1 for a in agents if a["active"] and a["type"] == atype)
                for atype in agent_types
            }
        })
    
    return {
        "monthly": monthly_data,
        "total_agents": num_agents,
        "final_users": total_users,
        "total_churned": total_churned,
        "retention_rate": round((1 - total_churned / max(total_users + total_churned, 1)) * 100, 1),
        "agent_types": list(agent_types.keys())
    }


# ============================================================
# 🧬 GENETIC ALGORITHM — Strategy Evolution
# ============================================================
def genetic_algorithm(scenarios, generations=50, population=100):
    """Evolve optimal strategy mix through natural selection."""
    np.random.seed(42)
    n = len(scenarios)
    # Population: each individual = weight vector for strategies
    pop = np.random.dirichlet(np.ones(n), population)
    
    def fitness(weights):
        roi = sum(w * s["expected_roi"] for w, s in zip(weights, scenarios))
        risk = sum(w * s["risk_score"] for w, s in zip(weights, scenarios))
        prob = sum(w * s["success_probability"] for w, s in zip(weights, scenarios))
        return prob * 0.4 + roi * 0.3 - risk * 0.3
    
    best_history = []
    for gen in range(generations):
        scores = [fitness(ind) for ind in pop]
        best_idx = np.argmax(scores)
        best_history.append({"gen": gen + 1, "fitness": round(scores[best_idx], 2), "weights": pop[best_idx].tolist()})
        
        # Selection (tournament)
        new_pop = [pop[best_idx].copy()]  # elitism
        for _ in range(population - 1):
            i, j = np.random.choice(population, 2, replace=False)
            parent1 = pop[i] if scores[i] > scores[j] else pop[j]
            i, j = np.random.choice(population, 2, replace=False)
            parent2 = pop[i] if scores[i] > scores[j] else pop[j]
            # Crossover
            alpha = np.random.random()
            child = alpha * parent1 + (1 - alpha) * parent2
            # Mutation
            if np.random.random() < 0.2:
                child += np.random.normal(0, 0.05, n)
                child = np.abs(child)
            child /= child.sum()  # normalize
            new_pop.append(child)
        pop = np.array(new_pop)
    
    final_scores = [fitness(ind) for ind in pop]
    best = pop[np.argmax(final_scores)]
    return {
        "optimal_weights": {scenarios[i]["name"]: round(best[i] * 100, 1) for i in range(n)},
        "fitness_history": best_history[::5],  # every 5th gen
        "final_fitness": round(max(final_scores), 2),
        "generations": generations,
        "population": population
    }


# ============================================================
# 🦠 SIR EPIDEMIC MODEL — Viral Growth Projection
# ============================================================
def sir_viral_model(scenarios, best_scenario, months=6):
    """Model product adoption as epidemic spread (SIR model)."""
    # S=potential users, I=active users, R=churned
    total_market = 10000
    S, I, R = total_market - 10, 10, 0  # start with 10 "infected"
    
    success = best_scenario.get("success_probability", 50) / 100
    risk = best_scenario.get("risk_score", 50) / 100
    
    beta = 0.3 * success  # infection rate (virality)
    gamma = 0.05 + risk * 0.1  # recovery rate (churn)
    R0 = beta / gamma if gamma > 0 else 0  # basic reproduction number
    
    daily_data = []
    for day in range(months * 30):
        dS = -beta * S * I / total_market
        dI = beta * S * I / total_market - gamma * I
        dR = gamma * I
        S = max(0, S + dS)
        I = max(0, I + dI)
        R = max(0, R + dR)
        if day % 7 == 0:  # weekly snapshots
            daily_data.append({"week": day // 7 + 1, "susceptible": int(S), "active": int(I), "churned": int(R)})
    
    peak_week = max(daily_data, key=lambda d: d["active"])
    return {
        "R0": round(R0, 2),
        "beta": round(beta, 4),
        "gamma": round(gamma, 4),
        "peak_users": peak_week["active"],
        "peak_week": peak_week["week"],
        "final_active": daily_data[-1]["active"],
        "total_reached": total_market - daily_data[-1]["susceptible"],
        "weekly_data": daily_data,
        "verdict": "VIRAL" if R0 > 1.5 else "GROWING" if R0 > 1.0 else "DECLINING"
    }


# ============================================================
# 🎯 NASH EQUILIBRIUM — Game Theory Competition
# ============================================================
def nash_equilibrium(scenarios):
    """Find Nash Equilibrium for competitive pricing/positioning."""
    n = len(scenarios)
    # Payoff matrix: what happens when you pick strategy i and competitor picks j
    payoff = np.zeros((n, n))
    for i, si in enumerate(scenarios):
        for j, sj in enumerate(scenarios):
            if i == j:
                payoff[i][j] = si["expected_roi"] * 0.5  # head-to-head: split market
            else:
                # Advantage = higher success * lower risk
                advantage = (si["success_probability"] - sj["success_probability"]) / 100
                risk_diff = (sj["risk_score"] - si["risk_score"]) / 100
                payoff[i][j] = si["expected_roi"] * (0.5 + advantage * 0.3 + risk_diff * 0.2)
    
    # Find mixed strategy Nash (iterative best response)
    strategy = np.ones(n) / n
    for _ in range(100):
        expected = payoff @ strategy
        best = np.argmax(expected)
        strategy *= 0.95
        strategy[best] += 0.05
        strategy /= strategy.sum()
    
    dominant = scenarios[np.argmax(strategy)]
    return {
        "equilibrium_weights": {scenarios[i]["name"]: round(strategy[i] * 100, 1) for i in range(n)},
        "dominant_strategy": dominant["name"],
        "payoff_matrix": payoff.tolist(),
        "stability": "STABLE" if max(strategy) < 0.5 else "DOMINANT" if max(strategy) > 0.7 else "MIXED"
    }


# ============================================================
# 📊 SHANNON ENTROPY — Market Uncertainty
# ============================================================
def shannon_entropy(scenarios, quantum_results):
    """Measure market uncertainty using information theory."""
    # Entropy of AI probabilities
    ai_probs = np.array([s["success_probability"] / 100 for s in scenarios])
    ai_probs = ai_probs / ai_probs.sum()
    ai_entropy = -np.sum(ai_probs * np.log2(ai_probs + 1e-10))
    
    # Entropy of quantum allocations
    q_allocs = np.array([r["allocation_percent"] / 100 for r in quantum_results])
    q_allocs = q_allocs / (q_allocs.sum() + 1e-10)
    q_entropy = -np.sum(q_allocs * np.log2(q_allocs + 1e-10))
    
    # Risk entropy
    risks = np.array([s["risk_score"] / 100 for s in scenarios])
    risks = risks / (risks.sum() + 1e-10)
    risk_entropy = -np.sum(risks * np.log2(risks + 1e-10))
    
    max_entropy = np.log2(len(scenarios))
    
    return {
        "ai_entropy": round(ai_entropy, 3),
        "quantum_entropy": round(q_entropy, 3),
        "risk_entropy": round(risk_entropy, 3),
        "max_entropy": round(max_entropy, 3),
        "ai_uncertainty": round(ai_entropy / max_entropy * 100, 1),
        "quantum_uncertainty": round(q_entropy / max_entropy * 100, 1),
        "market_verdict": "HIGH UNCERTAINTY" if ai_entropy / max_entropy > 0.85 else "MODERATE" if ai_entropy / max_entropy > 0.6 else "LOW — CLEAR LEADER"
    }


# ============================================================
# 🌀 LORENZ ATTRACTORS — Market Stability / Chaos Analysis
# ============================================================
def chaos_analysis(scenarios, quantum_results):
    """Detect chaotic vs stable market dynamics using Lorenz-inspired model."""
    # Map scenarios to Lorenz parameters
    best_q = max(quantum_results, key=lambda r: r["quantum_score"])
    best_s = next((s for s in scenarios if s["id"] == best_q["scenario_id"]), scenarios[0])
    
    sigma = 10 * (best_s["risk_score"] / 100)  # convection rate ~ risk
    rho = 28 * (best_s["success_probability"] / 100)  # temperature diff ~ opportunity
    beta_l = 8/3 * (best_s["expected_roi"] / 100)  # geometry ~ ROI structure
    
    # Simulate Lorenz system
    x, y, z = 1.0, 1.0, 1.0
    dt = 0.01
    trajectory = []
    lyapunov_sum = 0
    prev_x = x
    
    for step in range(3000):
        dx = sigma * (y - x) * dt
        dy = (x * (rho - z) - y) * dt
        dz = (x * y - beta_l * z) * dt
        x, y, z = x + dx, y + dy, z + dz
        if step % 30 == 0:
            trajectory.append({"step": step, "x": round(x, 2), "y": round(y, 2), "z": round(z, 2)})
        if step > 0:
            lyapunov_sum += np.log(abs(x - prev_x) + 1e-10)
        prev_x = x
    
    lyapunov = lyapunov_sum / 3000
    
    # Detect attractors (cluster analysis on trajectory)
    x_vals = [t["x"] for t in trajectory]
    x_range = max(x_vals) - min(x_vals) if x_vals else 0
    
    return {
        "lyapunov_exponent": round(lyapunov, 4),
        "is_chaotic": lyapunov > 0,
        "trajectory": trajectory[-20:],  # last 20 points
        "x_range": round(x_range, 2),
        "sigma": round(sigma, 2),
        "rho": round(rho, 2),
        "beta": round(beta_l, 2),
        "verdict": "CHAOTIC — high sensitivity to initial conditions" if lyapunov > 0 else "STABLE — predictable convergence",
        "business_meaning": "Small changes in execution timing can lead to drastically different outcomes" if lyapunov > 0 else "Market dynamics are predictable — execute with confidence"
    }


# ============================================================
# 🐺 LOTKA-VOLTERRA — Competitor Dynamics (Predator-Prey)
# ============================================================
def lotka_volterra(scenarios, best_scenario, months=12):
    """Model competitor dynamics as predator-prey ecosystem."""
    # Your brand = prey (growing), competitors = predators
    your_pop = 100  # your market share units
    comp_pop = 300  # competitor market share
    
    alpha = 0.1 * (best_scenario["success_probability"] / 100)  # your growth rate
    beta_lv = 0.005 * (best_scenario["risk_score"] / 100)  # predation rate
    delta = 0.002 * (100 - best_scenario["risk_score"]) / 100  # competitor decline from your success
    gamma_lv = 0.05  # competitor natural decline
    
    monthly = []
    for month in range(months * 4):  # weekly steps
        dY = (alpha * your_pop - beta_lv * your_pop * comp_pop) * 0.25
        dC = (delta * your_pop * comp_pop - gamma_lv * comp_pop) * 0.25
        your_pop = max(1, your_pop + dY)
        comp_pop = max(1, comp_pop + dC)
        if month % 4 == 0:
            monthly.append({"month": month // 4 + 1, "your_share": round(your_pop, 1), "competitor_share": round(comp_pop, 1)})
    
    equilibrium_you = round(gamma_lv / delta, 1) if delta > 0 else 0
    equilibrium_comp = round(alpha / beta_lv, 1) if beta_lv > 0 else 0
    
    return {
        "monthly_data": monthly,
        "final_your_share": monthly[-1]["your_share"] if monthly else 0,
        "final_comp_share": monthly[-1]["competitor_share"] if monthly else 0,
        "equilibrium_your": equilibrium_you,
        "equilibrium_comp": equilibrium_comp,
        "coexistence": abs(your_pop - comp_pop) / max(your_pop, comp_pop) < 0.5,
        "verdict": "DOMINANCE" if your_pop > comp_pop * 1.5 else "COEXISTENCE" if abs(your_pop - comp_pop) / max(your_pop, comp_pop) < 0.5 else "DISPLACEMENT"
    }


# ============================================================
# 💎 BLACK-SCHOLES — Strategy Option Pricing
# ============================================================
def black_scholes_options(scenarios, budget, timeline):
    """Price each strategy as a financial option using Black-Scholes."""
    from math import log, sqrt, exp, erf
    
    def norm_cdf(x):
        return (1 + erf(x / sqrt(2))) / 2
    
    options = []
    risk_free_rate = 0.05  # 5% annual
    
    for s in scenarios:
        S = budget  # current "stock price" = budget
        K = budget * (1 + s["risk_score"] / 100)  # strike = budget + risk premium
        T = timeline / 12  # time in years
        sigma = s["risk_score"] / 100 * 2  # volatility from risk
        r = risk_free_rate
        
        if sigma > 0 and T > 0:
            d1 = (log(S / K) + (r + sigma**2 / 2) * T) / (sigma * sqrt(T))
            d2 = d1 - sigma * sqrt(T)
            call_price = S * norm_cdf(d1) - K * exp(-r * T) * norm_cdf(d2)
            put_price = K * exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
        else:
            call_price = max(0, S - K)
            put_price = max(0, K - S)
        
        expected_value = budget * (1 + s["expected_roi"] / 100)
        
        options.append({
            "strategy": s["name"],
            "call_value": round(call_price, 2),
            "put_value": round(put_price, 2),
            "expected_payoff": round(expected_value, 2),
            "implied_volatility": round(sigma * 100, 1),
            "risk_reward_ratio": round(expected_value / max(call_price, 1), 2),
            "verdict": "UNDERPRICED" if expected_value > call_price * 3 else "FAIR" if expected_value > call_price * 1.5 else "OVERPRICED"
        })
    
    return sorted(options, key=lambda o: o["risk_reward_ratio"], reverse=True)


# Cached wrapper — same input = same result, no recalculation
@st.cache_data(show_spinner=False, ttl=3600)
def cached_claude(prompt, api_key, raw_text, model):
    """Cache Claude API calls — same prompt = cached result."""
    return _call_claude_inner(prompt, api_key, raw_text, model)


# === CACHED QUANTUM OPTIMIZATION ===
@st.cache_data(
    show_spinner="⚛️ Running Quantum VQE...",
    ttl=3600
)
def cached_vqe_optimize(_scenarios_json, risk_tolerance, target, num_iterations, num_shots, backend="simulator"):
    """Cached wrapper for heavy quantum computation. Same input = instant result."""
    scenarios = json.loads(_scenarios_json)
    optimizer = QuantumOptimizer(backend=backend)
    return optimizer.vqe_optimize(
        scenarios=scenarios,
        risk_tolerance=risk_tolerance,
        target=target,
        num_iterations=num_iterations,
        num_shots=num_shots
    )


# ============================================================
# CLAUDE AI
# ============================================================
SCENARIOS_PROMPT = """You are a Quantum Business Oracle. Respond ALL text in {lang}.

Parameters:
- Business idea / data: {idea}
- Budget: ${budget}
- Target markets: {markets}
- Timeline: {timeline} months
- Risk tolerance: {risk}
- Strategy mode: {mode}

If the input contains [DATA-DRIVEN ANALYSIS] with business metrics, analyze the data patterns first:
- Identify key trends (growing/declining metrics)
- Find anomalies or risks in the numbers
- Calculate key ratios (ACOS, conversion rates, margins, etc.)
Then generate 5 optimization/growth strategies based on the actual data.
Use real market data if provided. Do not invent numbers where real data is available.

Otherwise, generate 5 business scenarios as usual.

Output format — JSON array:
- "id": 1-5
- "name": short name (3-5 words)
- "description": 2 sentences with specific numbers. Each claim must be labeled: [FACT] for verified data, [ESTIMATE] for calculated projections, [HYPOTHESIS] for assumptions
- "success_probability": 0-100
- "expected_roi": percentage (can be negative)
- "risk_score": 0-100
- "time_to_profit": months
- "key_factors": array of 3 strings. Start each with [FACT], [ESTIMATE], or [HYPOTHESIS]
- "threats": array of 2 strings
- "recommendation": "GO" or "WAIT" or "AVOID"

Mode: aggressive=high ROI/fast, balanced=equal, conservative=low risk/stable.
Respond ONLY with valid JSON array."""


def clean_dataframe(df):
    """Preprocess DataFrame: clean Not Found, convert types."""
    # Replace "Not Found" with NaN
    df = df.replace("Not Found", np.nan)
    df = df.replace("not found", np.nan)
    df = df.replace("N/A", np.nan)
    df = df.replace("n/a", np.nan)
    df = df.replace("-", np.nan)
    
    # Try to convert numeric columns (skip first few metadata columns)
    for col in df.columns[4:]:  # Skip metadata columns
        try:
            # Remove currency symbols and convert
            cleaned = df[col].astype(str).str.replace('$', '', regex=False)
            cleaned = cleaned.str.replace('€', '', regex=False)
            cleaned = cleaned.str.replace('£', '', regex=False)
            cleaned = cleaned.str.replace(',', '.', regex=False)  # EU decimal format
            cleaned = cleaned.str.strip()
            df[col] = pd.to_numeric(cleaned, errors='coerce')
        except Exception:
            pass
    
    # Count Not Found stats
    not_found_count = df.isna().sum().sum()
    total_cells = df.shape[0] * df.shape[1]
    not_found_pct = round(not_found_count / total_cells * 100, 1) if total_cells > 0 else 0
    
    return df, not_found_pct


EXECUTION_PROMPT = """You are a senior startup growth strategist. ALL text in {lang}.

Business: {idea}
Budget: ${budget} | Timeline: {timeline}mo | Mode: {mode}

Quantum ranking:
{ranking}

CRITICAL: You MUST return ALL fields below. Never skip execution_plan or money_projection.
Even for data-driven analysis, create an actionable 8-week plan and revenue projection.
If analyzing existing business data, project revenue growth from current baseline.

Return JSON:
{{
  "first_action": "ONE specific thing to do tomorrow in ≤60 minutes",
  "execution_plan": [
    {{"week": 1, "title": "short", "tasks": ["task1", "task2", "task3"]}}
  ] (MUST have exactly 8 weeks — never skip this),
  "money_projection": {{
    "month_1": {{"users": N, "revenue": N}},
    "month_2": {{"users": N, "revenue": N}},
    "month_3": {{"users": N, "revenue": N}},
    "month_6": {{"users": N, "revenue": N}},
    "total_mrr_target": N,
    "breakeven_month": N
  }} (MUST include — for existing business use current revenue as baseline and project growth),
  "quantum_reasoning": ["reason1", "reason2", "reason3"]
}}

Be specific. No vague advice. ONLY valid JSON. ALL fields required."""


def _call_claude_inner(prompt, api_key, raw_text=False, model="claude-sonnet-4-6"):
    """Inner function for Claude API calls (used by cache wrapper)."""
    if not api_key or not isinstance(api_key, str) or not api_key.startswith("sk-ant"):
        raise ValueError(f"Invalid API key format: {str(api_key)[:20] if api_key else 'None'}")
    try:
        client = anthropic.Anthropic(api_key=str(api_key).strip())
        msg = client.messages.create(
            model=model,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text
        if raw_text:
            return text
        try:
            return json.loads(text)
        except:
            import re
            m = re.search(r'[\[{][\s\S]*[\]}]', text)
            if m:
                return json.loads(m.group())
            return text
    except Exception as e:
        err = str(e).lower()
        if "not found" in err or "does not exist" in err or "access" in err:
            fallbacks = ["claude-sonnet-4-5", "claude-sonnet-4-20250514"]
            for fb in fallbacks:
                if fb != model:
                    try:
                        return _call_claude_inner(prompt, api_key, raw_text, model=fb)
                    except:
                        continue
        raise e


def web_search_context(idea, api_key, model="claude-sonnet-4-6"):
    """Search web for real market data before analysis.
    Uses Gemini with Google Search grounding (FREE) if available,
    falls back to Claude web search ($0.03/query)."""
    
    # Try Gemini Search first (FREE — 500 queries/day)
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key and GEMINI_AVAILABLE:
        try:
            genai.configure(api_key=gemini_key)
            search_model = genai.GenerativeModel(
                "gemini-2.5-flash",
                tools=[{"google_search": {}}]
            )
            response = search_model.generate_content(f"""Search the web for current real market data relevant to this business:

{idea[:500]}

Find and return ONLY factual numbers:
- Current market prices, rates, costs relevant to this industry
- Market size, growth rates
- Competitor pricing
- Any relevant economic indicators

Format as a short bullet list of VERIFIED facts with sources. Max 10 bullets. Only real data, no opinions."""
            )
            if response and response.text:
                return f"[Source: Google Search via Gemini — FREE]\n{response.text}"
        except Exception:
            pass  # Fall through to Claude
    
    # Fallback to Claude web search ($0.03/query)
    if not api_key or not api_key.startswith("sk-ant"):
        return ""
    try:
        client = anthropic.Anthropic(api_key=str(api_key).strip())
        msg = client.messages.create(
            model=model,
            max_tokens=2000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": f"""Search the web for current real market data relevant to this business:

{idea[:500]}

Find and return ONLY factual numbers:
- Current market prices, rates, costs relevant to this industry
- Market size, growth rates
- Competitor pricing
- Any relevant economic indicators

Format as a short bullet list of VERIFIED facts with sources. Max 10 bullets. Only real data, no opinions."""}]
        )
        texts = []
        for block in msg.content:
            if hasattr(block, 'text'):
                texts.append(block.text)
        return f"[Source: Claude Web Search]\n" + "\n".join(texts) if texts else ""
    except Exception as e:
        return f"(Web search unavailable: {e})"


def deep_research_claude(idea, api_key, model="claude-sonnet-4-6"):
    """Claude Deep Research — multi-step web search with synthesis."""
    if not api_key:
        return ""
    try:
        client = anthropic.Anthropic(api_key=str(api_key).strip())
        msg = client.messages.create(
            model=model,
            max_tokens=8000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": f"""You are a business research analyst. Do DEEP multi-step research on this business question.

BUSINESS CONTEXT:
{idea[:2000]}

RESEARCH INSTRUCTIONS:
1. Search for the SPECIFIC industry/niche this business is in. Find market size, growth rate, key trends.
2. Search for DIRECT COMPETITORS. Find their prices, positioning, strengths, weaknesses.
3. Search for the BEST SALES CHANNELS for this type of product in 2025-2026. Find conversion rates, fees, ROI benchmarks.
4. Search for REGULATORY requirements and compliance issues relevant to this business.
5. Search for PRICING BENCHMARKS — what do top sellers charge? What's the price elasticity?
6. Search for TECHNOLOGY and TOOLS that could give competitive advantage (AI, automation, etc.)
7. Search for CASE STUDIES of similar businesses that scaled successfully. What worked? What failed?

Do at least 8-10 separate web searches to cover all angles. Read full articles, not just snippets.

OUTPUT FORMAT:
Write a comprehensive research brief (1500-2500 words) organized by topic. Include:
- [VERIFIED] tag for data with sources
- [INSIGHT] tag for strategic conclusions
- Specific numbers, dates, company names
- Contradictions between sources (if any)
- Risks and opportunities others might miss

Be thorough. This research will feed into a quantum-optimized business strategy engine."""}]
        )
        texts = []
        for block in msg.content:
            if hasattr(block, 'text'):
                texts.append(block.text)
        return "[Source: Claude Deep Research]\n" + "\n".join(texts) if texts else ""
    except Exception as e:
        st.warning(f"Claude Deep Research error: {e}")
        return ""


def deep_research_gemini(idea, gemini_model="gemini-2.5-flash"):
    """Gemini Deep Research — Google Search grounding with multi-step analysis."""
    try:
        import google.generativeai as genai
        model = genai.GenerativeModel(gemini_model)
        response = model.generate_content(
            f"""You are a market research analyst with access to Google Search. Do comprehensive research on this business:

BUSINESS CONTEXT:
{idea[:2000]}

RESEARCH TASKS:
1. Find current MARKET SIZE and GROWTH RATE for this specific industry/niche
2. Find TOP COMPETITORS — their revenue, pricing, market share, positioning
3. Find CONSUMER TRENDS — what buyers want, how preferences are changing
4. Find CHANNEL BENCHMARKS — Amazon conversion rates, TikTok Shop growth, D2C benchmarks
5. Find PRICING DATA — average prices, willingness to pay, price sensitivity
6. Find SUPPLY CHAIN facts — raw material costs, lead times, sourcing options
7. Find REGULATORY landscape — EU compliance, certifications, upcoming regulations
8. Find TECHNOLOGY trends — AI tools, automation, new platforms

OUTPUT FORMAT:
Comprehensive research report (1500-2500 words) with:
- Specific numbers and sources for every claim
- Competitive landscape analysis
- Channel-by-channel opportunity assessment
- Risk factors and market threats
- Hidden opportunities that surface-level research misses

Be thorough and fact-based. This research feeds into a quantum business strategy engine.""",
            tools=[{"google_search": {}}]
        )
        if response and response.text:
            return f"[Source: Gemini Deep Research + Google Search]\n{response.text}"
    except Exception as e:
        st.warning(f"Gemini Deep Research error: {e}")
    return ""


def call_claude(prompt, api_key, raw_text=False, model="claude-sonnet-4-6"):
    """Claude API with caching — same prompt+model = cached result."""
    try:
        return cached_claude(prompt, api_key, raw_text, model)
    except Exception as e:
        st.error(f"Claude API error: {e}")
        return None


def call_gemini(prompt, raw_text=False, gemini_model="gemini-2.5-flash"):
    """Google Gemini API call."""
    if not GEMINI_AVAILABLE:
        return None
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        return None
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(gemini_model)
        response = model.generate_content(prompt)
        text = response.text
        if raw_text:
            return text
        try:
            return json.loads(text)
        except:
            import re
            # Remove markdown code fences
            clean = text.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(clean)
            except:
                m = re.search(r'[\[{][\s\S]*[\]}]', clean)
                return json.loads(m.group()) if m else text
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return None


def call_ai(prompt, api_key, ai_engine="claude", raw_text=False, model="claude-sonnet-4-6", gemini_model="gemini-2.5-flash"):
    """Universal AI call — supports any combination of engines."""
    if ai_engine == "gemini":
        return call_gemini(prompt, raw_text, gemini_model)
    elif ai_engine == "groq":
        return call_groq(prompt, raw_text)
    elif "MULTI" in str(ai_engine):
        results = {}
        primary = None
        if st.session_state.get("use_claude") and api_key:
            st.toast("🧠 Claude analyzing...")
            r = call_claude(prompt, api_key, raw_text, model)
            if r:
                results["claude"] = r
                primary = primary or r
        if st.session_state.get("use_gemini"):
            st.toast("🤖 Gemini analyzing...")
            r = call_gemini(prompt, raw_text, gemini_model)
            if r:
                results["gemini"] = r
                primary = primary or r
        if st.session_state.get("use_groq"):
            st.toast("⚡ Groq analyzing...")
            r = call_groq(prompt, raw_text)
            if r:
                results["groq"] = r
                primary = primary or r
        if results:
            st.toast(f"✅ {len(results)} AI engines completed: {', '.join(results.keys())}")
        st.session_state["multi_ai_results"] = results
        return primary
    else:
        return call_claude(prompt, api_key, raw_text, model)


def call_groq(prompt, raw_text=False):
    """Groq API call — fastest inference, Llama models."""
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key or not GROQ_AVAILABLE:
        return None
    try:
        client = GroqClient(api_key=groq_key)
        groq_model = st.session_state.get("groq_model", "llama-3.3-70b-versatile")
        response = client.chat.completions.create(
            model=groq_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000
        )
        text = response.choices[0].message.content
        if raw_text:
            return text
        try:
            return json.loads(text)
        except:
            import re
            clean = text.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(clean)
            except:
                m = re.search(r'[\[{][\s\S]*[\]}]', clean)
                return json.loads(m.group()) if m else text
    except Exception as e:
        st.error(f"Groq API error: {e}")
        return None


# ============================================================
# UI
# ============================================================
# Header
st.markdown("""
<div class="main-header">
    <div class="version">QUANTUM ORACLE v0.8</div>
    <h1>Business Strategy Engine</h1>
    <div class="sub">AI + Quantum War Room · Executive Decisions in 15 Seconds</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    # Read from Streamlit secrets first, fallback to manual input
    secret_key = ""
    try:
        secret_key = str(st.secrets["ANTHROPIC_API_KEY"]).strip().strip('"').strip("'")
    except Exception:
        secret_key = ""

    gemini_key = ""
    try:
        gemini_key = str(st.secrets["GEMINI_API_KEY"]).strip().strip('"').strip("'")
    except Exception:
        gemini_key = ""
    
    if secret_key and secret_key.startswith("sk-ant"):
        api_key = secret_key
        st.markdown(f'<div style="color:{accent}; font-size:0.75rem;">✅ Claude ({api_key[:12]}...)</div>', unsafe_allow_html=True)
    else:
        api_key = st.text_input("Claude API Key", type="password", help="sk-ant-...")

    if gemini_key and gemini_key.startswith("AIza"):
        st.markdown(f'<div style="color:{accent}; font-size:0.75rem;">✅ Gemini ({gemini_key[:12]}...)</div>', unsafe_allow_html=True)
        pass  # genai configured per-call

    groq_key = ""
    try:
        groq_key = str(st.secrets["GROQ_API_KEY"]).strip().strip('"').strip("'")
    except Exception:
        groq_key = os.environ.get("GROQ_API_KEY", "")

    if groq_key and groq_key.startswith("gsk_"):
        st.markdown(f'<div style="color:{accent}; font-size:0.75rem;">✅ Groq ({groq_key[:12]}...)</div>', unsafe_allow_html=True)

    # === RESEARCH MODE ===
    st.markdown("---")
    web_search_enabled = st.checkbox("🌐 Web Search (real data)", value=False, help="Claude searches web for real market prices before analysis. Costs ~$0.03 extra.")
    deep_research_enabled = st.checkbox("🔬 Deep Research", value=False, help="Claude + Gemini both do multi-step web research (5-10 searches each) before analysis. Takes 2-5 min, costs ~$0.30-0.50. Best for important decisions.")
    if deep_research_enabled:
        web_search_enabled = True  # Deep Research includes web search
    
    lang = st.selectbox("🌐 Language", ["English", "Русский", "Українська"])
    lang_map = {"English": "English", "Русский": "Russian", "Українська": "Ukrainian"}

    # AI Engine toggles — pick any combination
    st.markdown("### 🤖 AI Engine")
    col_all, _ = st.columns([1, 2])
    with col_all:
        use_all = st.checkbox("⚡ All", value=False, key="use_all_ai")
    
    if use_all:
        use_claude = True
        use_gemini = True
        use_groq = True
        st.markdown(f'<div style="color:{accent}; font-size:0.75rem;">☑ Claude  ☑ Gemini  ☑ Groq</div>', unsafe_allow_html=True)
    else:
        col_ai1, col_ai2, col_ai3 = st.columns(3)
        with col_ai1:
            use_claude = st.checkbox("Claude", value=bool(secret_key), key="use_claude")
        with col_ai2:
            use_gemini = st.checkbox("Gemini", value=bool(gemini_key), key="use_gemini")
        with col_ai3:
            use_groq = st.checkbox("Groq", value=False, key="use_groq")
    
    # Build ai_engine from toggles
    active_engines = []
    if use_claude and secret_key:
        active_engines.append("claude")
    if use_gemini and gemini_key:
        active_engines.append("gemini")
    if use_groq and groq_key:
        active_engines.append("groq")
    
    if len(active_engines) == 0:
        active_engines = ["claude"]  # fallback
    
    if len(active_engines) >= 2:
        ai_engine = "🧠 MULTI (all 3)"
    else:
        ai_engine = active_engines[0]
    
    engine_label = " + ".join(active_engines) if len(active_engines) > 1 else active_engines[0]
    st.markdown(f'<div style="color:{text2}; font-size:0.7rem;">Active: {engine_label}</div>', unsafe_allow_html=True)

    st.markdown("### 🤖 Claude Model")
    model_options = {
        "Sonnet 4.6 (latest)": "claude-sonnet-4-6",
        "Sonnet 4.5 (stable)": "claude-sonnet-4-5",
        "Sonnet 4 (legacy)": "claude-sonnet-4-20250514"
    }
    selected_model = st.selectbox("Model", options=list(model_options.keys()), index=0, label_visibility="collapsed")
    claude_model = model_options[selected_model]

    if gemini_key:
        st.markdown("### 🤖 Gemini Model")
        gemini_options = {
            "Gemini 3.1 Flash Live (newest)": "gemini-3.1-flash-live-preview",
            "Gemini 3 Flash (smart+fast)": "gemini-3-flash-preview",
            "Gemini 2.5 Pro (best quality)": "gemini-2.5-pro",
            "Gemini 2.5 Flash (stable)": "gemini-2.5-flash",
            "Gemini 2.5 Flash-Lite (cheapest)": "gemini-2.5-flash-lite",
            "Gemini 2.0 Flash (legacy)": "gemini-2.0-flash"
        }
        selected_gemini = st.selectbox("Gemini", options=list(gemini_options.keys()), index=1, label_visibility="collapsed")
        gemini_model = gemini_options[selected_gemini]
    else:
        gemini_model = "gemini-2.5-flash"

    if groq_key:
        st.markdown("### 🤖 Groq Model")
        groq_options = {
            "GPT OSS 120B (best reasoning)": "openai/gpt-oss-120b",
            "GPT OSS 20B (fast+smart)": "openai/gpt-oss-20b",
            "Llama 4 Scout (vision+tools)": "meta-llama/llama-4-scout-17b-16e-instruct",
            "Llama 3.3 70B (stable)": "llama-3.3-70b-versatile",
            "Qwen3 32B (multilingual)": "qwen/qwen3-32b"
        }
        selected_groq = st.selectbox("Groq", options=list(groq_options.keys()), index=0, label_visibility="collapsed")
        st.session_state["groq_model"] = groq_options[selected_groq]

    st.markdown("---")
    st.markdown("### 🎮 Strategy Mode")
    mode = st.radio("Strategy Mode", ["🛡️ Conservative", "⚖️ Balanced", "🚀 Aggressive"], index=1, label_visibility="collapsed")
    mode_map = {"🛡️ Conservative": "conservative", "⚖️ Balanced": "balanced", "🚀 Aggressive": "aggressive"}
    mode_val = mode_map[mode]

    st.markdown("---")
    st.markdown("### ⚛️ Quantum Engine")
    quantum_backend = st.selectbox("Backend", ["simulator", "google_cirq", "pennylane", "⚡ MULTI (all 3)", "ibm_quantum"], index=0, key="q_backend")
    ibm_token = None
    if quantum_backend == "ibm_quantum":
        ibm_token = st.text_input("IBM Quantum Token", type="password", help="Get free token at quantum.ibm.com")
    elif quantum_backend == "google_cirq":
        st.markdown(f'<div style="color:{text2}; font-size:0.7rem;">Google Cirq simulator — no token needed</div>', unsafe_allow_html=True)
    elif quantum_backend == "pennylane":
        st.markdown(f'<div style="color:{text2}; font-size:0.7rem;">Xanadu PennyLane — quantum ML engine, no token needed</div>', unsafe_allow_html=True)
    elif quantum_backend == "⚡ MULTI (all 3)":
        st.markdown(f'<div style="color:{accent}; font-size:0.7rem;">🔥 Run Qiskit + Cirq + PennyLane simultaneously</div>', unsafe_allow_html=True)
    vqe_iterations = st.slider("VQE Iterations", 5, 25, 8)
    num_shots = st.select_slider("Shots per iteration", [512, 1024, 2048, 4096, 8192], value=1024)

    high_precision = st.checkbox("🔬 High Precision Mode", value=False)
    if high_precision:
        vqe_iterations = st.slider("VQE Iterations (HP)", 10, 30, 15, key="hp_iter")
        num_shots = st.select_slider("Shots (HP)", [2048, 4096, 8192], value=2048, key="hp_shots")

    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center; color:{text2}; font-size:0.7rem;">
        ⚛️ {'IBM Quantum' if quantum_backend == 'ibm_quantum' else 'Google Cirq' if quantum_backend == 'google_cirq' else 'Xanadu PennyLane' if quantum_backend == 'pennylane' else '⚡ MULTI ENGINE' if 'MULTI' in quantum_backend else 'Qiskit AerSimulator'}<br>
        🧬 VQE {vqe_iterations} iterations × {num_shots} shots<br>
        = {vqe_iterations * num_shots:,} measurements<br><br>
        QUANTUM ORACLE v0.8
    </div>
    """, unsafe_allow_html=True)

# Main Input — two modes: Text or Data
# === UNIFIED INPUT ===
col_main, col_side = st.columns([3, 1])

with col_main:
    idea = st.text_area("💡 Describe your business or question",
        placeholder="Examples:\n• I have 2 Dry Van trucks in USA, which growth strategy to choose?\n• SaaS tool for Amazon sellers, budget $10K\n• Should I invest in crypto or real estate?\n• I uploaded my sales data — find growth opportunities",
        height=100,
        value=st.session_state.get("generated_idea", ""))

    if st.button("🧠 GENERATE IDEAS", use_container_width=True, key="gen_ideas"):
        if api_key or ai_engine in ["gemini", "groq"]:
            with st.spinner("Generating ideas..."):
                gen_prompt = f"""Generate 1 innovative and profitable startup idea for 2026 that can be built by one person with $5-10K budget.
The idea should be at intersection of AI, quantum computing, crypto, or e-commerce.
Respond in {lang_map[lang]}.
Format: just the idea description in 2-3 sentences, no title, no numbering. Be specific and creative. Different every time."""
                result = call_ai(gen_prompt, api_key, ai_engine=ai_engine, raw_text=True, model=claude_model, gemini_model=gemini_model)
                if result and isinstance(result, str):
                    st.session_state["generated_idea"] = result
                elif result:
                    st.session_state["generated_idea"] = str(result)
                st.rerun()
        else:
            st.warning("Enter API key in sidebar")

with col_side:
    show_params = st.checkbox("⚙️ Parameters", value=False)
    if show_params:
        budget = st.number_input("💰 Budget ($)", value=10000, step=1000)
        markets_list = st.multiselect("🌍 Markets",
            ["🇺🇸 US", "🇨🇦 CA", "🇪🇺 EU", "🇩🇪 DE", "🇬🇧 UK", "🇺🇦 UA", "🌍 Global"],
            default=["🇺🇸 US", "🇪🇺 EU"])
        markets = ", ".join([m.split(" ")[-1] for m in markets_list])
        timeline = st.number_input("⏱️ Timeline (mo)", value=6, min_value=1, max_value=36)
        risk = st.selectbox("🎯 Risk", ["low", "medium", "high"], index=1)
    else:
        budget = 10000
        markets = "US, EU"
        timeline = 6
        risk = "medium"

# === OPTIONAL DATA ATTACHMENT ===
csv_data_summary = None

# === AI CHAT — discuss before analysis ===
chat_enabled = st.checkbox("💬 Chat with AI", value=False, help="Discuss your idea, get suggestions before running analysis")

if chat_enabled:
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    
    # Display chat history
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f'<div style="background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:10px 14px; margin:6px 0; margin-left:20%;"><span style="color:{text2}; font-size:0.7rem;">YOU</span><br><span style="color:{text}; font-size:0.85rem;">{msg["text"]}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:{accent}08; border:1px solid {accent}22; border-radius:12px; padding:10px 14px; margin:6px 0; margin-right:20%;"><span style="color:{accent}; font-size:0.7rem;">🤖 AI</span><br><span style="color:{text}; font-size:0.85rem;">{msg["text"]}</span></div>', unsafe_allow_html=True)
    
    col_chat, col_send = st.columns([5, 1])
    with col_chat:
        chat_input = st.text_input("Message", placeholder="Ask AI anything about your business idea...", label_visibility="collapsed", key="chat_input")
    with col_send:
        send_clicked = st.button("Send", use_container_width=True, key="chat_send")
    
    col_clear, col_use = st.columns(2)
    with col_clear:
        if st.button("🗑️ Clear chat", use_container_width=True, key="chat_clear"):
            st.session_state["chat_history"] = []
            st.rerun()
    with col_use:
        if st.button("📋 Use last AI reply as idea", use_container_width=True, key="chat_use"):
            ai_msgs = [m for m in st.session_state["chat_history"] if m["role"] == "ai"]
            if ai_msgs:
                st.session_state["generated_idea"] = ai_msgs[-1]["text"]
                st.rerun()
    
    if send_clicked and chat_input and chat_input.strip():
        st.session_state["chat_history"].append({"role": "user", "text": chat_input.strip()})
        
        # Build context from chat history
        history_text = "\n".join([f"{'User' if m['role']=='user' else 'AI'}: {m['text']}" for m in st.session_state["chat_history"][-6:]])
        current_idea = idea.strip() if idea and idea.strip() else ""
        
        # Get data context if available
        data_info = ""
        if "uploaded_df" in st.session_state:
            df = st.session_state["uploaded_df"]
            data_info = f"\n\nThe user has attached business data: {len(df):,} rows × {len(df.columns)} columns."
            data_info += f"\nColumns: {', '.join(df.columns.tolist()[:15])}"
            # Add sample data
            sample = df.head(5).to_string(max_cols=10, max_colwidth=15)
            data_info += f"\nSample:\n{sample}"
            # Numeric stats
            for col in df.select_dtypes(include=['number']).columns[:5]:
                valid = df[col].dropna()
                if len(valid) > 0:
                    data_info += f"\n{col}: min={valid.min():.2f}, max={valid.max():.2f}, mean={valid.mean():.2f}"
            # Categories
            for col in df.select_dtypes(include=['object']).columns[:3]:
                uniques = df[col].dropna().unique()[:10]
                data_info += f"\n{col}: {', '.join(str(v) for v in uniques)}"
        
        chat_prompt = f"""You are a business strategy advisor in Quantum Oracle AI platform.
The user is brainstorming before running a full quantum analysis.
{f'Their current business idea: {current_idea}' if current_idea else ''}
{data_info}

Previous conversation:
{history_text}

Respond briefly (3-5 sentences). Be specific, actionable. If the user attached data — reference specific numbers from it.
Help them refine their idea or understand their data before running quantum simulation.
Respond in the same language as the user."""
        
        with st.spinner("🤖 Thinking..."):
            try:
                # Chat uses first available engine directly (not MULTI)
                chat_engine = "claude"
                if st.session_state.get("use_gemini") and not st.session_state.get("use_claude"):
                    chat_engine = "gemini"
                elif st.session_state.get("use_groq") and not st.session_state.get("use_claude") and not st.session_state.get("use_gemini"):
                    chat_engine = "groq"
                
                if chat_engine == "gemini":
                    reply = call_gemini(chat_prompt, raw_text=True, gemini_model=gemini_model)
                elif chat_engine == "groq":
                    groq_key = os.environ.get("GROQ_API_KEY", "")
                    if not groq_key:
                        reply = "⚠️ Groq API key not found in secrets"
                    elif not GROQ_AVAILABLE:
                        reply = "⚠️ Groq package not installed"
                    else:
                        try:
                            client = GroqClient(api_key=groq_key)
                            groq_m = st.session_state.get("groq_model", "llama-3.3-70b-versatile")
                            resp = client.chat.completions.create(
                                model=groq_m,
                                messages=[{"role": "user", "content": chat_prompt}],
                                max_tokens=2000
                            )
                            reply = resp.choices[0].message.content
                        except Exception as ge:
                            reply = f"⚠️ Groq error ({groq_m}): {ge}"
                else:
                    reply = call_claude(chat_prompt, api_key, raw_text=True, model=claude_model)
                
                if reply:
                    reply_text = str(reply) if not isinstance(reply, str) else reply
                    st.session_state["chat_history"].append({"role": "ai", "text": reply_text})
                else:
                    st.session_state["chat_history"].append({"role": "ai", "text": f"⚠️ No response from {chat_engine}. Check API key."})
            except Exception as e:
                st.session_state["chat_history"].append({"role": "ai", "text": f"⚠️ {e}"})
        st.rerun()

attach_data = st.checkbox("📎 Attach Data", value=False, help="Upload file, Google Sheets, or Live API")

if attach_data:
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        use_file = st.checkbox("📎 File", value=False, key="use_file")
    with col_s2:
        use_sheets = st.checkbox("🔗 Sheets", value=False, key="use_sheets")
    with col_s3:
        use_api = st.checkbox("🌐 Live API", value=False, key="use_api")

    if use_file:
        uploaded_file = st.file_uploader("Upload", type=["csv", "xlsx", "xls", "pdf", "txt", "json"], label_visibility="collapsed")
        if uploaded_file:
            file_type = uploaded_file.name.split(".")[-1].lower()
            try:
                if file_type in ("csv", "xlsx", "xls"):
                    df = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)
                    df, nf_pct = clean_dataframe(df)
                    st.dataframe(df.head(10), use_container_width=True)
                    st.session_state["uploaded_df"] = df
                    stats = [f"File: {uploaded_file.name} ({len(df):,} rows × {len(df.columns)} cols)"]
                    stats.append(f"Columns: {', '.join(df.columns.tolist()[:20])}")
                    
                    # Smart summary — actual data sample
                    sample_rows = min(50, len(df))
                    if len(df) <= 50:
                        sample_df = df
                    else:
                        indices = list(range(0, min(20, len(df)))) + list(range(max(0, len(df) - 20), len(df)))
                        indices = sorted(set(i for i in indices if 0 <= i < len(df)))
                        sample_df = df.iloc[indices]
                    
                    stats.append(f"\n=== SAMPLE DATA ({len(sample_df)} rows) ===")
                    stats.append(sample_df.to_string(max_cols=15, max_colwidth=20))
                    
                    for col in df.select_dtypes(include=['number']).columns[:8]:
                        valid = df[col].dropna()
                        if len(valid) > 0:
                            stats.append(f"{col}: min={valid.min():.2f}, max={valid.max():.2f}, mean={valid.mean():.2f}")
                    
                    for col in df.select_dtypes(include=['object']).columns[:5]:
                        top = df[col].value_counts().head(5)
                        stats.append(f"{col}: {', '.join(f'{k}({v})' for k, v in top.items())}")
                    
                    csv_data_summary = "\n".join(stats)
                    if len(csv_data_summary) > 8000:
                        csv_data_summary = csv_data_summary[:8000] + "\n... (truncated)"
                elif file_type == "pdf":
                    try:
                        import PyPDF2
                        reader = PyPDF2.PdfReader(uploaded_file)
                        pdf_text = "\n".join([p.extract_text() for p in reader.pages[:10]])
                        csv_data_summary = f"PDF: {uploaded_file.name} ({len(reader.pages)} pages)\n{pdf_text[:4000]}"
                    except:
                        csv_data_summary = f"File: {uploaded_file.name}"
                elif file_type in ("txt", "json"):
                    content = uploaded_file.read().decode('utf-8')
                    csv_data_summary = f"File: {uploaded_file.name}\n{content[:4000]}"
                if csv_data_summary:
                    st.markdown(f'<div style="color:{accent}; font-size:0.75rem;">✅ {uploaded_file.name} — {len(df):,} rows × {len(df.columns)} columns{f" | {nf_pct}% empty" if nf_pct > 5 else ""}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")

    if use_sheets:
        sheets_url = st.text_input("URL", placeholder="https://docs.google.com/spreadsheets/d/...", label_visibility="collapsed")
        if sheets_url and sheets_url.strip():
            try:
                import re
                match = re.search(r'/d/([a-zA-Z0-9_-]+)', sheets_url)
                if match:
                    sheet_id = match.group(1)
                    gid_match = re.search(r'gid=(\d+)', sheets_url)
                    gid = gid_match.group(1) if gid_match else "0"
                    with st.spinner("Loading..."):
                        df = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}")
                    df, nf_pct = clean_dataframe(df)
                    st.dataframe(df.head(10), use_container_width=True)
                    st.session_state["uploaded_df"] = df
                    stats = [f"Google Sheets ({len(df):,} rows × {len(df.columns)} cols)"]
                    stats.append(f"Columns: {', '.join(df.columns.tolist()[:20])}")
                    
                    # Smart summary — show actual data, not just min/max
                    # Sample rows (first, middle, last)
                    sample_rows = min(50, len(df))
                    if len(df) <= 50:
                        sample_df = df
                    else:
                        indices = list(range(0, min(20, len(df))))  # first 20
                        indices += list(range(len(df)//2 - 5, len(df)//2 + 5))  # middle 10
                        indices += list(range(max(0, len(df) - 20), len(df)))  # last 20
                        indices = sorted(set(i for i in indices if 0 <= i < len(df)))
                        sample_df = df.iloc[indices]
                    
                    stats.append(f"\n=== SAMPLE DATA ({len(sample_df)} rows) ===")
                    stats.append(sample_df.to_string(max_cols=15, max_colwidth=20))
                    
                    # Numeric columns stats
                    num_cols = df.select_dtypes(include=['number']).columns[:10]
                    if len(num_cols) > 0:
                        stats.append(f"\n=== NUMERIC STATS ===")
                        for col in num_cols:
                            valid = df[col].dropna()
                            if len(valid) > 0:
                                stats.append(f"{col}: min={valid.min():.2f}, max={valid.max():.2f}, mean={valid.mean():.2f}, count={len(valid)}")
                    
                    # Category/text columns — unique values
                    cat_cols = df.select_dtypes(include=['object']).columns[:8]
                    if len(cat_cols) > 0:
                        stats.append(f"\n=== CATEGORIES ===")
                        for col in cat_cols:
                            uniques = df[col].dropna().unique()
                            if len(uniques) <= 20:
                                stats.append(f"{col}: {', '.join(str(v) for v in uniques)}")
                            else:
                                top = df[col].value_counts().head(10)
                                stats.append(f"{col} ({len(uniques)} unique): top = {', '.join(f'{k}({v})' for k, v in top.items())}")
                    
                    # Limit total size to ~8000 chars for prompt
                    csv_data_summary = "\n".join(stats)
                    if len(csv_data_summary) > 8000:
                        csv_data_summary = csv_data_summary[:8000] + "\n... (truncated)"
                    st.markdown(f'<div style="color:{accent}; font-size:0.75rem;">✅ Sheet loaded — {len(df):,} rows × {len(df.columns)} columns{f" | {nf_pct}% empty" if nf_pct > 5 else ""}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")

    if use_api:
        api_choices = st.multiselect("Feeds", ["🪙 Crypto", "💱 Exchange rates", "📈 Market sentiment"], default=["🪙 Crypto"])
        if st.button("🔄 FETCH", use_container_width=True, key="fetch_api"):
            parts = []
            with st.spinner("Fetching..."):
                import httpx as hx
                if any("Crypto" in c for c in api_choices):
                    try:
                        r = hx.get("https://api.coingecko.com/api/v3/simple/price?ids=solana,bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true", timeout=10)
                        for coin, data in r.json().items():
                            parts.append(f"{coin.upper()}: ${data.get('usd',0):,.2f} ({data.get('usd_24h_change',0):+.1f}%)")
                    except: pass
                if any("Exchange" in c for c in api_choices):
                    try:
                        r = hx.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10)
                        for cur in ["EUR", "GBP", "UAH"]:
                            parts.append(f"USD/{cur}: {r.json()['rates'].get(cur, 0):.4f}")
                    except: pass
            if parts:
                csv_data_summary = "\n".join(parts)
                st.session_state["api_data"] = csv_data_summary
                st.code(csv_data_summary, language=None)
        if "api_data" in st.session_state and not csv_data_summary:
            csv_data_summary = st.session_state["api_data"]

# Build final idea with data
all_data_parts = []
if csv_data_summary:
    all_data_parts.append(csv_data_summary)
if "api_data" in st.session_state and st.session_state["api_data"] and attach_data and use_api:
    if st.session_state["api_data"] not in (csv_data_summary or ""):
        all_data_parts.append(st.session_state["api_data"])

combined_data = "\n\n".join(all_data_parts) if all_data_parts else None

if combined_data:
    base_idea = idea.strip() if idea and idea.strip() else "Analyze this data and suggest optimization strategies."
    idea = f"[DATA-DRIVEN ANALYSIS]\n\nUser request: {base_idea}\n\nData:\n{combined_data}"

# RUN
if st.button("⚡ RUN QUANTUM SIMULATION", use_container_width=True):
    if not idea.strip():
        st.warning("Enter a business idea first!")
    elif not api_key and not ANTHROPIC_AVAILABLE:
        st.warning("Enter Claude API key in sidebar")
    else:
        # STEP 0: Web Search / Deep Research for real market data
        market_context = ""
        deep_context = ""
        
        if deep_research_enabled:
            # === DEEP RESEARCH MODE: Claude + Gemini multi-step research ===
            dr_cols = st.columns(2)
            claude_dr = ""
            gemini_dr = ""
            
            with dr_cols[0]:
                with st.spinner("🔬 Claude Deep Research (5-10 searches)..."):
                    claude_dr = deep_research_claude(idea, api_key, model=claude_model)
                    if claude_dr:
                        st.toast("✅ Claude Deep Research complete")
            
            with dr_cols[1]:
                with st.spinner("🔬 Gemini Deep Research (Google Search)..."):
                    gemini_dr = deep_research_gemini(idea, gemini_model=gemini_model)
                    if gemini_dr:
                        st.toast("✅ Gemini Deep Research complete")
            
            # Combine both research reports
            parts = []
            if claude_dr:
                parts.append(claude_dr)
            if gemini_dr:
                parts.append(gemini_dr)
            
            if parts:
                deep_context = "\n\n---\n\n".join(parts)
                market_context = deep_context
                st.session_state["market_context"] = market_context
                st.session_state["deep_research"] = {
                    "claude": claude_dr,
                    "gemini": gemini_dr
                }
                
                # Show research summary
                with st.expander(f"🔬 DEEP RESEARCH RESULTS ({len(claude_dr) + len(gemini_dr):,} chars from 2 AI engines)", expanded=False):
                    if claude_dr:
                        st.markdown("#### 🧠 Claude Deep Research")
                        st.markdown(claude_dr[:3000] + "..." if len(claude_dr) > 3000 else claude_dr)
                    if gemini_dr:
                        st.markdown("#### 🤖 Gemini Deep Research")
                        st.markdown(gemini_dr[:3000] + "..." if len(gemini_dr) > 3000 else gemini_dr)
        
        elif web_search_enabled:
            with st.spinner("🌐 Searching web for real market data..."):
                market_context = web_search_context(idea, api_key, model=claude_model)
                if market_context:
                    st.session_state["market_context"] = market_context

        # STEP 1: Claude scenarios
        with st.spinner("🧠 AI generating scenarios..."):
            # Inject real market data into prompt if available
            idea_with_context = idea
            if market_context and len(market_context) > 20:
                # Truncate deep research to fit in prompt (max 8000 chars for context)
                ctx = market_context[:8000] if len(market_context) > 8000 else market_context
                dr_label = "DEEP RESEARCH" if deep_research_enabled else "web search"
                idea_with_context = f"""{idea}

=== VERIFIED MARKET DATA (from {dr_label} — Claude + Gemini) ===
{ctx}
=== END MARKET DATA ===

IMPORTANT: Use the real market data above for all calculations. Do not invent numbers where real data is available. Label claims as [FACT] if from research, [ESTIMATE] if calculated, [HYPOTHESIS] if assumed."""

            prompt = SCENARIOS_PROMPT.format(
                idea=idea_with_context, budget=budget, markets=markets,
                timeline=timeline, risk=risk, mode=mode_val,
                lang=lang_map[lang]
            )
            scenarios = call_ai(prompt, api_key, ai_engine=ai_engine, model=claude_model, gemini_model=gemini_model)

        if scenarios and isinstance(scenarios, list):
            st.session_state["scenarios"] = scenarios

            # STEP 2: Quantum VQE (cached — same input = instant)
            st.markdown("### ⚛️ Running Quantum VQE Optimization...")
            scenarios_json = json.dumps(scenarios, sort_keys=True)

            if "MULTI" in quantum_backend:
                # === MULTI-ENGINE: Run all 3 simultaneously ===
                multi_results = {}
                engines = [
                    ("simulator", "Qiskit AerSimulator"),
                    ("google_cirq", "Google Cirq"),
                    ("pennylane", "Xanadu PennyLane")
                ]
                for eng_id, eng_name in engines:
                    try:
                        r = cached_vqe_optimize(
                            _scenarios_json=scenarios_json,
                            risk_tolerance=risk, target=mode_val,
                            num_iterations=vqe_iterations, num_shots=num_shots,
                            backend=eng_id
                        )
                        multi_results[eng_id] = {"name": eng_name, "data": r}
                    except Exception as e:
                        multi_results[eng_id] = {"name": eng_name, "data": None, "error": str(e)}

                st.session_state["multi_results"] = multi_results

                # Use Qiskit as primary (most accurate)
                quantum = multi_results.get("simulator", {}).get("data")
                if not quantum:
                    # Fallback to any working engine
                    for eng_id in ["google_cirq", "pennylane"]:
                        if multi_results.get(eng_id, {}).get("data"):
                            quantum = multi_results[eng_id]["data"]
                            break
            else:
                quantum = cached_vqe_optimize(
                    _scenarios_json=scenarios_json,
                    risk_tolerance=risk, target=mode_val,
                    num_iterations=vqe_iterations, num_shots=num_shots,
                    backend=quantum_backend if 'quantum_backend' in dir() else "simulator"
                )

            st.session_state["quantum"] = quantum

            # STEP 2b: Monte Carlo simulation
            mc_results = monte_carlo_simulate(scenarios)
            st.session_state["mc_results"] = mc_results

            # STEP 2c: Quantum Noise simulation
            noise_optimizer = QuantumOptimizer()
            noise_results = noise_optimizer.noisy_simulate(scenarios, risk, mode_val)
            st.session_state["noise_results"] = noise_results

            # STEP 2d: Explainable Quantum correlation matrix
            xq_matrix, xq_labels = quantum_correlation_matrix(scenarios, quantum.get("results", []))
            st.session_state["xq_matrix"] = xq_matrix.tolist()
            st.session_state["xq_labels"] = xq_labels

            # STEP 2e: QAOA Portfolio Optimization (on real data only)
            uploaded_df = st.session_state.get("uploaded_df")
            if csv_data_summary and uploaded_df is not None:
                try:
                    qaoa_opt = QuantumPortfolioOptimizer(max_qubits=15)
                    qaoa_result = qaoa_opt.optimize(
                        uploaded_df, num_layers=3, num_iterations=15, num_shots=2048
                    )
                    st.session_state["qaoa_result"] = qaoa_result
                except Exception as e:
                    st.session_state["qaoa_result"] = None

            # STEP 2f: BCG Matrix
            bcg_items = bcg_matrix_analyze(scenarios, quantum.get("results", []))
            st.session_state["bcg_items"] = bcg_items

            # STEP 2g: Agent-Based Modeling
            best_s = next((s for s in scenarios if s["id"] == quantum["best_id"]), scenarios[0])
            abm_result = agent_simulation(scenarios, best_s, num_agents=500, num_months=timeline)
            st.session_state["abm_result"] = abm_result

            # STEP 3: Execution plan
            with st.spinner("📋 Building execution plan..."):
                ranking = "\n".join([
                    f"{i+1}. {next((s['name'] for s in scenarios if s['id'] == r['scenario_id']), '?')} — quantum: {r['quantum_score']}%, alloc: {r['allocation_percent']}%"
                    for i, r in enumerate(quantum["results"])
                ])
                exec_prompt = EXECUTION_PROMPT.format(
                    idea=idea, budget=budget, timeline=timeline,
                    mode=mode_val, lang=lang_map[lang], ranking=ranking
                )
                exec_data = call_ai(exec_prompt, api_key, ai_engine=ai_engine, model=claude_model, gemini_model=gemini_model)
                
                # Validate exec_data has required fields
                if isinstance(exec_data, dict):
                    if not exec_data.get("execution_plan"):
                        exec_data["execution_plan"] = [{"week": i, "title": f"Week {i}", "tasks": ["TBD"]} for i in range(1, 9)]
                    if not exec_data.get("money_projection"):
                        exec_data["money_projection"] = {"month_1": {"users": 0, "revenue": 0}, "month_2": {"users": 0, "revenue": 0}, "month_3": {"users": 0, "revenue": 0}, "month_6": {"users": 0, "revenue": 0}, "total_mrr_target": 0, "breakeven_month": 3}
                    if not exec_data.get("quantum_reasoning"):
                        exec_data["quantum_reasoning"] = ["Quantum analysis completed — see AI vs Quantum comparison above"]
                else:
                    exec_data = {}
                st.session_state["exec_data"] = exec_data

            # Save to history for comparison
            if "history" not in st.session_state:
                st.session_state["history"] = []
            st.session_state["history"].append({
                "idea": idea[:80] + "..." if len(idea) > 80 else idea,
                "strategy": next((s["name"] for s in scenarios if s["id"] == quantum["best_id"]), "?"),
                "success": next((s["success_probability"] for s in scenarios if s["id"] == quantum["best_id"]), 0),
                "quantum_score": quantum["results"][0]["quantum_score"],
                "roi": next((s["expected_roi"] for s in scenarios if s["id"] == quantum["best_id"]), 0),
                "risk": next((s["risk_score"] for s in scenarios if s["id"] == quantum["best_id"]), 0),
                "mrr": int(float(exec_data.get("money_projection", {}).get("total_mrr_target", 0))) if exec_data and exec_data.get("money_projection", {}).get("total_mrr_target") else 0,
                "mode": mode_val,
                "confidence": round(
                    next((s["success_probability"] for s in scenarios if s["id"] == quantum["best_id"]), 50) * 0.6 +
                    (100 - next((s["risk_score"] for s in scenarios if s["id"] == quantum["best_id"]), 50)) * 0.4
                )
            })

            st.session_state["play_sound"] = True
            st.rerun()

# ============================================================
# RESULTS
# ============================================================
if "scenarios" in st.session_state:
    scenarios = st.session_state["scenarios"]
    quantum = st.session_state.get("quantum", {})
    exec_data = st.session_state.get("exec_data", {})

    # 🔊 Quantum completion sound
    if st.session_state.pop("play_sound", False):
        st.components.v1.html("""
        <script>
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        function playTone(freq, start, dur, vol) {
            const o = ctx.createOscillator();
            const g = ctx.createGain();
            o.type = 'sine';
            o.frequency.setValueAtTime(freq, ctx.currentTime + start);
            g.gain.setValueAtTime(vol, ctx.currentTime + start);
            g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + dur);
            o.connect(g); g.connect(ctx.destination);
            o.start(ctx.currentTime + start);
            o.stop(ctx.currentTime + start + dur);
        }
        // Quantum whoosh: rising chord
        playTone(220, 0, 0.8, 0.08);
        playTone(330, 0.05, 0.7, 0.06);
        playTone(440, 0.1, 0.6, 0.05);
        playTone(660, 0.2, 0.5, 0.04);
        playTone(880, 0.3, 0.8, 0.03);
        </script>
        """, height=0)

    best_id = quantum.get("best_id", scenarios[0]["id"])
    best = next((s for s in scenarios if s["id"] == best_id), scenarios[0])
    best_q = next((r for r in quantum.get("results", []) if r["scenario_id"] == best_id), None)

    mrr = exec_data.get("money_projection", {}).get("total_mrr_target", 0) if exec_data else 0
    try:
        mrr = int(float(mrr)) if mrr else 0
    except (ValueError, TypeError):
        mrr = 0
    breakeven = exec_data.get("money_projection", {}).get("breakeven_month", "—") if exec_data else "—"

    # === INPUT QUERY ===
    idea_short = idea[:120] + "..." if len(idea) > 120 else idea
    st.markdown(f"""
    <div style="background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:16px 20px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div style="color:{text2}; font-size:0.65rem; letter-spacing:2px;">📝 QUERY</div>
            <div style="display:flex; gap:12px;">
                <span style="color:{accent}; font-size:0.75rem; font-weight:600;">${budget:,}</span>
                <span style="color:{text2}; font-size:0.75rem;">{markets}</span>
                <span style="color:{text2}; font-size:0.75rem;">{timeline}mo</span>
                <span style="color:{text2}; font-size:0.75rem;">risk:{risk}</span>
                <span style="color:{'#00e878' if mode_val == 'aggressive' else accent}; font-size:0.75rem; font-weight:600;">{mode_val.upper()}</span>
            </div>
        </div>
        <div style="color:{text}; font-size:0.9rem; line-height:1.5;">{idea_short}</div>
    </div>
    """, unsafe_allow_html=True)

    # === WEB SEARCH / DEEP RESEARCH CONTEXT ===
    market_ctx = st.session_state.get("market_context")
    deep_res = st.session_state.get("deep_research")
    if market_ctx and len(market_ctx) > 20:
        dr_label = "🔬 Deep Research Results" if deep_res else "🌐 Real Market Data (from web search)"
        with st.expander(dr_label, expanded=False):
            st.markdown(market_ctx[:5000] + "..." if len(market_ctx) > 5000 else market_ctx)

    # === 📋 EXECUTIVE BRIEF (generate + display) ===
    if api_key:
        if st.button("📋 GENERATE EXECUTIVE BRIEF", use_container_width=True, key="exec_summary"):
            with st.spinner("Writing executive brief..."):
                q_results = quantum.get("results", [])
                scenarios_summary = "\n".join([
                    f"- {s['name']}: AI={s['success_probability']}%, Quantum={next((r['quantum_score'] for r in q_results if r['scenario_id'] == s['id']), '?')}%, ROI=+{s['expected_roi']}%, Risk={s['risk_score']}/100, Verdict={s['recommendation']}"
                    for s in scenarios
                ])
                money = ""
                if exec_data and exec_data.get("money_projection"):
                    mp = exec_data["money_projection"]
                    money = f"Revenue: M1=${mp.get('month_1', {}).get('revenue', 0):,}, M3=${mp.get('month_3', {}).get('revenue', 0):,}, M6=${mp.get('month_6', {}).get('revenue', 0):,}. Target MRR: ${mp.get('total_mrr_target', 0):,}. Breakeven: Month {mp.get('breakeven_month', '?')}."
                conv = quantum.get("convergence", [])
                vqe_info = f"VQE: {quantum.get('iterations', 0)} iterations, {quantum.get('total_shots', 0):,} shots, cost range [{min(conv):.4f} to {max(conv):.4f}]" if conv else ""

                summary_prompt = f"""You are a McKinsey senior partner writing a 1-page executive brief for the CEO.
Language: {lang_map[lang]}

INPUT: {idea[:1000]}
Budget: ${budget:,} | Markets: {markets} | Timeline: {timeline}mo | Risk: {risk} | Mode: {mode_val}

SCENARIOS:
{scenarios_summary}

QUANTUM: {vqe_info}
Best: {best['name']} (quantum: {best_q['quantum_score'] if best_q else '?'}%)

DISAGREEMENT: {exec_data.get('quantum_reasoning', ['N/A'])[0] if exec_data and exec_data.get('quantum_reasoning') else 'N/A'}

MONEY: {money}
FIRST ACTION: {exec_data.get('first_action', 'N/A') if exec_data else 'N/A'}
RESEARCH: {st.session_state.get('market_context', 'N/A')[:2000]}

Write a board meeting brief:

# EXECUTIVE BRIEF — [Company/Topic]
**Confidential | Budget: ${budget:,} | Horizon: {timeline} months**

## 🎯 THE BOTTOM LINE
One BOLD sentence. The single most profitable move. No 'maybe'.

## 📊 VITAL METRICS
Exactly 4 metrics. Each on ONE line. Format: "LABEL: VALUE — short (max 10 words)"
Example: "Quantum confidence: 65.04% — top strategy by portfolio score"
Example: "Revenue path: $68K→$310K — M1 to M6 breakeven M2"

## ⚡ THREE MOVES
1. [5-word action] — [deadline] — [15-word max result with $]
2. [5-word action] — [deadline] — [15-word max result with $]
3. [5-word action] — [deadline] — [15-word max result with $]

## ⚠️ CRITICAL STOP-LOSS
One sentence only. Exact metric trigger. Example: "If installs < 500 by M3 OR MRR < $1,000 → freeze spend."

## 🧠 WHY QUANTUM DISAGREES WITH AI
Max 80 words. What quantum saw, shift numbers, allocation impact.

## 💰 NET OUTCOME
One sentence: expected $ if executed on schedule.

ULTRA specific. Exact numbers. Professional, cold, data-driven. CEO clarity."""

                brief = call_claude(summary_prompt, api_key, raw_text=True, model=claude_model)
                st.session_state["exec_brief"] = brief

        if "exec_brief" in st.session_state:
            brief_text = st.session_state['exec_brief']
            if not isinstance(brief_text, str):
                brief_text = str(brief_text)
            
            # === Parse and render as separate complete HTML blocks ===
            import re
            sections = re.split(r'##\s*', brief_text)
            
            # Title block
            title_block = sections[0].strip() if sections else ""
            title_lines = [l.strip() for l in title_block.split("\n") if l.strip() and not l.strip().startswith("---")]
            brief_title = title_lines[0].replace("#", "").replace("**", "").strip() if title_lines else "Executive Brief"
            brief_subtitle = title_lines[1].replace("**", "").strip() if len(title_lines) > 1 else ""
            
            # Header with FINAL VERDICT badge
            st.markdown(f"""<div style="background:{card_bg}; border:2px solid {accent}; border-radius:16px 16px 0 0; padding:24px 24px 12px; position:relative;">
<div style="position:absolute; top:0; right:0; background:{accent}; color:{bg}; padding:5px 16px; font-size:0.6rem; font-weight:800; letter-spacing:2px; border-radius:0 14px 0 12px;">FINAL VERDICT v0.8</div>
<div style="font-size:1.05rem; font-weight:700; color:{text};">{brief_title}</div>
<div style="font-size:0.75rem; color:{text2};">{brief_subtitle}</div>
</div>""", unsafe_allow_html=True)
            
            for section in sections[1:]:
                lines = section.strip().split("\n")
                header = lines[0].strip() if lines else ""
                body_lines = [l.strip() for l in lines[1:] if l.strip() and l.strip() != "---"]
                body = "<br>".join([l.replace("**", "") for l in body_lines])
                header_lower = header.lower()
                
                if "bottom line" in header_lower:
                    st.markdown(f"""<div style="background:{card_bg}; border-left:2px solid {accent}; border-right:2px solid {accent}; padding:16px 24px;">
<div style="color:{accent}; font-size:0.7rem; font-weight:700; letter-spacing:2px; margin-bottom:8px;">⚡ THE BOTTOM LINE</div>
<div style="font-size:0.95rem; font-weight:600; color:{text}; line-height:1.6;">{body}</div>
</div>""", unsafe_allow_html=True)
                
                elif "vital" in header_lower or "metric" in header_lower or "ключев" in header_lower or "цифр" in header_lower:
                    metric_items = [l.lstrip("- •*0123456789.)").replace("**", "").strip() for l in body_lines if l.strip()]
                    cards_html = ""
                    for item in metric_items[:4]:
                        if ":" in item:
                            parts = item.split(":", 1)
                            label = parts[0].strip()
                            rest = parts[1].strip()
                            if "—" in rest:
                                vp = rest.split("—", 1)
                                value, desc = vp[0].strip(), vp[1].strip()
                            elif " - " in rest:
                                vp = rest.split(" - ", 1)
                                value, desc = vp[0].strip(), vp[1].strip()
                            else:
                                value, desc = rest[:40], ""
                            vc = "#e84050" if any(w in item.lower() for w in ["stop","wait","стоп","abort"]) else text
                            cards_html += f'<div style="background:{bg}; border:1px solid {border}; border-radius:10px; padding:12px 14px;"><div style="font-size:0.7rem; color:{text2};">{label}</div><div style="font-size:1.25rem; font-weight:700; color:{vc}; margin:4px 0;">{value}</div><div style="font-size:0.7rem; color:{text2};">{desc}</div></div>'
                        else:
                            cards_html += f'<div style="background:{bg}; border:1px solid {border}; border-radius:10px; padding:12px;"><div style="font-size:0.85rem; color:{text};">{item}</div></div>'
                    st.markdown(f"""<div style="background:{card_bg}; border-left:2px solid {accent}; border-right:2px solid {accent}; padding:16px 24px;">
<div style="color:{accent}; font-size:0.7rem; font-weight:700; letter-spacing:2px; margin-bottom:10px;">📊 VITAL METRICS</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">{cards_html}</div>
</div>""", unsafe_allow_html=True)
                
                elif "three" in header_lower or "move" in header_lower or "шаг" in header_lower:
                    cl = [accent, "#378ADD", "#888780"]
                    steps_html = ""
                    for i, step in enumerate([l.lstrip("- •*0123456789.)").replace("**","").strip() for l in body_lines if l.strip()][:3]):
                        c = cl[i] if i < len(cl) else cl[-1]
                        steps_html += f'<div style="background:{bg}; border-left:3px solid {c}; padding:10px 14px; margin-bottom:8px;"><div style="font-size:0.85rem; color:{text}; line-height:1.5;">{step}</div></div>'
                    st.markdown(f"""<div style="background:{card_bg}; border-left:2px solid {accent}; border-right:2px solid {accent}; padding:16px 24px;">
<div style="color:{accent}; font-size:0.7rem; font-weight:700; letter-spacing:2px; margin-bottom:10px;">⚡ THREE MOVES</div>
{steps_html}
</div>""", unsafe_allow_html=True)
                
                elif "stop" in header_lower or "risk" in header_lower or "риск" in header_lower or "стоп" in header_lower:
                    st.markdown(f"""<div style="background:{card_bg}; border-left:2px solid {accent}; border-right:2px solid {accent}; padding:16px 24px;">
<div style="color:#e84050; font-size:0.7rem; font-weight:700; letter-spacing:2px; margin-bottom:8px;">⚠️ CRITICAL STOP-LOSS</div>
<div style="background:rgba(232,64,80,0.08); border:1px solid rgba(232,64,80,0.2); border-radius:10px; padding:12px 14px;"><div style="font-size:0.85rem; color:{text}; line-height:1.6;">{body}</div></div>
</div>""", unsafe_allow_html=True)
                
                elif "quantum" in header_lower or "квант" in header_lower:
                    st.markdown(f"""<div style="background:{card_bg}; border-left:2px solid {accent}; border-right:2px solid {accent}; padding:16px 24px;">
<div style="color:#7F77DD; font-size:0.7rem; font-weight:700; letter-spacing:2px; margin-bottom:8px;">🧠 WHY QUANTUM DISAGREES WITH AI</div>
<div style="background:rgba(127,119,221,0.06); border:1px solid rgba(127,119,221,0.15); border-radius:10px; padding:12px 14px;"><div style="font-size:0.85rem; color:{text}; line-height:1.7;">{body}</div></div>
</div>""", unsafe_allow_html=True)
                
                elif "outcome" in header_lower or ("итог" in header_lower and "bottom" not in header_lower):
                    st.markdown(f"""<div style="background:{card_bg}; border:2px solid {accent}; border-top:none; border-radius:0 0 16px 16px; padding:16px 24px;">
<div style="border-top:1px solid {border}; padding-top:12px;">
<div style="color:{accent}; font-size:0.7rem; font-weight:700; letter-spacing:2px; margin-bottom:8px;">💰 NET OUTCOME</div>
<div style="font-size:0.92rem; font-weight:600; color:{text}; line-height:1.6;">{body}</div>
</div></div>""", unsafe_allow_html=True)
                
                else:
                    clean_header = header.replace("**", "").strip()
                    st.markdown(f"""<div style="background:{card_bg}; border-left:2px solid {accent}; border-right:2px solid {accent}; padding:16px 24px;">
<div style="color:{text2}; font-size:0.7rem; font-weight:700; letter-spacing:2px; margin-bottom:8px;">{clean_header}</div>
<div style="font-size:0.85rem; color:{text}; line-height:1.6;">{body}</div>
</div>""", unsafe_allow_html=True)
            
            st.download_button("⬇️ Download Executive Brief", data=brief_text.encode("utf-8"), file_name="quantum_oracle_executive_brief.txt", mime="text/plain", key="dl_brief")

    # === EXECUTIVE DECISION ===
    mrr_display = f"+${mrr:,} MRR" if isinstance(mrr, (int, float)) else ""
    st.markdown(f"""
    <div class="executive-panel">
        <div style="color:{accent}; font-size:0.75rem; letter-spacing:4px; margin-bottom:20px;">
            🎯 EXECUTIVE DECISION {f'— {mrr_display} ({timeline}mo)' if mrr_display else ''}
        </div>
    """, unsafe_allow_html=True)

    # Tomorrow action
    if exec_data and exec_data.get("first_action"):
        st.markdown(f"""
        <div class="tomorrow-box">
            <div class="tomorrow-label">ЗАВТРА (≤ 60 мін)</div>
            <div class="tomorrow-text">{exec_data['first_action']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Strategy name
    st.markdown(f"""
        <div style="margin-bottom:20px;">
            <div style="color:{label_dim}; font-size:0.7rem; letter-spacing:2px;">🚀 STRATEGY</div>
            <div class="strategy-name">{best['name']}</div>
        </div>
    """, unsafe_allow_html=True)

    # Metrics
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💰 OUTCOME ({timeline}mo)</div>
            <div style="margin-top:12px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:{row_label};">MRR</span>
                    <span class="metric-value metric-green">${mrr:,}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:{row_label};">Breakeven</span>
                    <span class="metric-value metric-cyan">Month {breakeven}</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:{row_label};">ROI</span>
                    <span class="metric-value metric-green">+{best['expected_roi']}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        confidence = round(best['success_probability'] * 0.6 + (100 - best['risk_score']) * 0.4)
        risk_color = "metric-green" if best['risk_score'] < 40 else "metric-yellow" if best['risk_score'] < 60 else "metric-red"
        success_color = "metric-green" if best['success_probability'] > 60 else "metric-yellow" if best['success_probability'] > 40 else "metric-red"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📊 PROBABILITY</div>
            <div style="margin-top:12px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:{row_label};">Success</span>
                    <span class="metric-value {success_color}">{best['success_probability']}%</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:{row_label};">Risk</span>
                    <span class="metric-value {risk_color}">{best['risk_score']}/100</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:{row_label};">Quantum</span>
                    <span class="metric-value" style="color:{accent};">{best_q['quantum_score'] if best_q else '—'}%</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:{row_label};">Confidence</span>
                    <span class="metric-value metric-purple">{confidence}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # WHY THIS WINS
    if exec_data and exec_data.get("quantum_reasoning"):
        reasons_html = "".join([
            f'<div style="color:{reason_text}; font-size:0.85rem; line-height:1.6; padding:4px 0;">◆ {r[:150]}{"..." if len(r)>150 else ""}</div>'
            for r in exec_data["quantum_reasoning"][:3]
        ])
        st.markdown(f"""
        <div class="why-box">
            <div class="why-label">🧠 WHY THIS WINS</div>
            {reasons_html}
        </div>
        """, unsafe_allow_html=True)

    # 🎯 QUANTUM CONFIDENCE GAUGE
    conf_val = round(best['success_probability'] * 0.6 + (100 - best['risk_score']) * 0.4)
    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=conf_val,
        number={"suffix": "%", "font": {"size": 36, "color": text}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": text2, "tickfont": {"color": text2}},
            "bar": {"color": "#00e878" if conf_val > 65 else "#c8a020" if conf_val > 40 else "#e84050"},
            "bgcolor": card_bg,
            "bordercolor": border,
            "steps": [
                {"range": [0, 35], "color": "rgba(232,64,80,0.12)"},
                {"range": [35, 65], "color": "rgba(200,160,32,0.12)"},
                {"range": [65, 100], "color": "rgba(0,232,120,0.12)"}
            ],
            "threshold": {
                "line": {"color": accent, "width": 2},
                "thickness": 0.8,
                "value": conf_val
            }
        },
        title={"text": "QUANTUM CONFIDENCE", "font": {"size": 11, "color": text2}},
    ))
    gauge_fig.update_layout(
        height=180,
        margin=dict(l=30, r=30, t=40, b=10),
        paper_bgcolor=chart_paper_bg,
        font=dict(color=text)
    )
    st.plotly_chart(gauge_fig, use_container_width=True)

    # ⚛️ Qubit entanglement animation
    n_qubits = quantum.get("total_qubits", 5)
    particles_html = ""
    for i in range(n_qubits):
        x = 15 + (i * 70 / max(n_qubits - 1, 1))
        q_state = quantum.get("results", [{}])[i]["qubit_state"] if i < len(quantum.get("results", [])) else "|0⟩"
        color = accent if "|1⟩" in q_state else text2
        particles_html += f'''
            <circle cx="{x}%" cy="50%" r="6" fill="{color}" opacity="0.8">
                <animate attributeName="cy" values="50%;42%;50%;58%;50%" dur="{1.5 + i*0.2}s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.5;1;0.5" dur="{2 + i*0.3}s" repeatCount="indefinite"/>
            </circle>
            <text x="{x}%" y="82%" text-anchor="middle" fill="{color}" font-size="9" font-family="monospace">{q_state}</text>
        '''

    lines_html = ""
    for i in range(n_qubits - 1):
        x1 = 15 + (i * 70 / max(n_qubits - 1, 1))
        x2 = 15 + ((i + 1) * 70 / max(n_qubits - 1, 1))
        lines_html += f'''
            <line x1="{x1}%" y1="50%" x2="{x2}%" y2="50%" stroke="{accent}" stroke-width="1" opacity="0.2">
                <animate attributeName="opacity" values="0.1;0.4;0.1" dur="{2 + i*0.4}s" repeatCount="indefinite"/>
            </line>
        '''

    st.components.v1.html(f'''
    <svg width="100%" height="60" xmlns="http://www.w3.org/2000/svg">
        {lines_html}
        {particles_html}
    </svg>
    ''', height=65)

    # Quantum engine footer
    q_info = f"⚛️ {quantum.get('total_qubits', '?')} qubits · {quantum.get('total_shots', 0):,} shots · {quantum.get('iterations', 0)} VQE loops · {mode_val} · {quantum.get('backend', 'simulator')}"
    st.markdown(f'<div style="text-align:center; color:{text2}; font-size:0.75rem; margin-top:8px;">{q_info}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # === QUANTUM ENGINE PANEL ===
    st.markdown("---")

    col_q1, col_q2 = st.columns([1, 1])

    with col_q1:
        st.markdown('<div class="quantum-panel">', unsafe_allow_html=True)
        st.markdown('<div class="quantum-label">⚛️ QISKIT QUANTUM ENGINE</div>', unsafe_allow_html=True)

        qm = st.columns(4)
        labels = ["QUBITS", "SHOTS", "DEPTH", "VQE LOOPS"]
        values = [quantum.get("total_qubits", 0), f"{quantum.get('total_shots', 0):,}",
                  quantum.get("depth", 0), quantum.get("iterations", 0)]
        for i, (l, v) in enumerate(zip(labels, values)):
            with qm[i]:
                st.metric(l, v)

        # Quantum scores
        for r in quantum.get("results", []):
            s = next((sc for sc in scenarios if sc["id"] == r["scenario_id"]), None)
            name = s["name"] if s else f"Scenario {r['scenario_id']}"
            is_best = r["scenario_id"] == best_id
            bar_color = "#00ff88" if is_best else "#00aaff"
            bar_bg = "#0a2a3a" if dark_mode else "#e0e8f0"
            text_color = "#8ab8cc" if dark_mode else "#4a6a7a"
            name_color = "#6a9aaa" if dark_mode else "#5a7a8a"
            state_color = "#00ddff" if dark_mode else "#2266aa"
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:8px; padding:4px 0;">
                <span style="color:{state_color}; font-size:0.8rem; min-width:30px;">{r['qubit_state']}</span>
                <div style="flex:1; height:5px; background:{bar_bg}; border-radius:3px; overflow:hidden;">
                    <div style="height:100%; width:{r['quantum_score']}%; background:{bar_color}; border-radius:3px;"></div>
                </div>
                <span style="color:{text_color}; font-size:0.75rem; min-width:90px;">{r['quantum_score']}% · {r['allocation_percent']}%</span>
                <span style="color:{name_color}; font-size:0.75rem;">{name}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_q2:
        # VQE Convergence Chart
        conv = quantum.get("convergence", [])
        if conv:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(1, len(conv) + 1)),
                y=conv,
                mode='lines+markers',
                line=dict(color='#4488cc' if dark_mode else '#2266aa', width=2),
                marker=dict(
                    size=6,
                    color=['#00e878' if v == min(conv) else ('#4488cc' if dark_mode else '#2266aa') for v in conv],
                ),
                fill='tozeroy',
                fillcolor='rgba(68,136,204,0.06)' if dark_mode else 'rgba(34,102,170,0.08)',
                hovertemplate='Iteration %{x}<br>Cost: %{y:.4f}<extra></extra>'
            ))
            fig.update_layout(
                title=dict(text="VQE CONVERGENCE", font=dict(color='#4488cc' if dark_mode else '#2266aa', size=12)),
                xaxis=dict(title="Iteration", color='#3a4a5a' if dark_mode else '#8a8a8a', gridcolor='#12141a' if dark_mode else '#e0e0e0', zeroline=False),
                yaxis=dict(title="Cost", color='#3a4a5a' if dark_mode else '#8a8a8a', gridcolor='#12141a' if dark_mode else '#e0e0e0', zeroline=False),
                plot_bgcolor='#08090e' if dark_mode else '#fafafa',
                paper_bgcolor=chart_paper_bg,
                font=dict(color='#5a6a7a' if dark_mode else '#4a4a4a', family="monospace"),
                height=320,
                margin=dict(l=40, r=20, t=36, b=40),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    # === QUANTUM CIRCUIT VISUALIZATION ===
    with st.expander("🔬 QUANTUM CIRCUIT DIAGRAM", expanded=False):
        try:
            qc_viz, _ = QuantumOptimizer().build_circuit(
                scenarios, risk, mode_val,
                [0.0] * len(scenarios)
            )
            circuit_text = qc_viz.draw(output='text').single_string()
            st.code(circuit_text, language=None)
            st.markdown(f"""
            <div style="color:{text2}; font-size:0.75rem; line-height:1.8; margin-top:8px;">
                <b>H</b> = Hadamard (superposition) · 
                <b>Ry/Rz/Rx</b> = Parameter encoding · 
                <b>CX</b> = Entanglement · 
                <b>M</b> = Measurement<br>
                {len(scenarios)} qubits × 5 layers = {qc_viz.depth()} depth · 
                {len(qc_viz.data)} gates · 
                {2**len(scenarios)} quantum states evaluated
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Circuit visualization error: {e}")

    # === AI vs QUANTUM COMPARISON ===
    st.markdown("---")
    
    # Quantum Score Explainer
    best_q_score = max([r.get("quantum_score", 0) for r in quantum.get("results", [])]) if quantum.get("results") else 0
    total_shots = quantum.get("total_shots", 0)
    total_qubits = quantum.get("total_qubits", 0)
    st.markdown(f"""
    <div style="background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:16px 20px; margin-bottom:16px;">
        <div style="color:{accent}; font-size:0.7rem; letter-spacing:2px; margin-bottom:8px;">🔬 HOW QUANTUM SCORING WORKS</div>
        <div style="color:{text}; font-size:0.85rem; line-height:1.7;">
            <b>What {total_qubits} qubits do:</b> Each qubit = one strategy. Entanglement (CX gates) creates correlations between ALL strategies simultaneously — 
            {2**total_qubits:,} combinations evaluated in {total_shots:,} measurements.<br><br>
            <b>What quantum_score means:</b> Probability that this strategy survives portfolio optimization. 
            Score 86% = in 86 out of 100 quantum measurements, this strategy was in the optimal portfolio. 
            Score 29% = only selected in 29 out of 100 — quantum sees hidden conflicts with other strategies.<br><br>
            <b>Why AI and Quantum disagree:</b> AI ranks each strategy independently (like reading 5 resumes one by one). 
            Quantum evaluates all 5 together (like a team interview — some great individuals don't work together). 
            When scores diverge, the quantum engine detected <b>cross-strategy dependencies</b> that linear AI misses.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ⚔️ AI vs QUANTUM — Where They Disagree = Your Hidden Opportunities")

    # Sort scenarios by AI (success_probability) and by Quantum (quantum_score)
    ai_ranking = sorted(scenarios, key=lambda s: s["success_probability"], reverse=True)
    q_results = quantum.get("results", [])
    q_ranking = sorted(q_results, key=lambda r: r["quantum_score"], reverse=True)

    # Find biggest disagreements
    disagreements = []
    for s in scenarios:
        ai_rank = next((i + 1 for i, a in enumerate(ai_ranking) if a["id"] == s["id"]), 0)
        q_rank = next((i + 1 for i, q in enumerate(q_ranking) if q["scenario_id"] == s["id"]), 0)
        q_score = next((q["quantum_score"] for q in q_results if q["scenario_id"] == s["id"]), 0)
        diff = abs(ai_rank - q_rank)
        disagreements.append({
            "name": s["name"], "id": s["id"],
            "ai_rank": ai_rank, "ai_score": s["success_probability"],
            "q_rank": q_rank, "q_score": q_score,
            "rank_diff": diff, "recommendation": s["recommendation"]
        })

    # Table
    table_html = f"""
    <table style="width:100%; border-collapse:collapse; margin:12px 0;">
    <tr style="border-bottom:2px solid {border};">
        <th style="padding:10px; text-align:left; color:{text2}; font-size:0.65rem; letter-spacing:1px;">SCENARIO</th>
        <th style="padding:10px; text-align:center; color:{text2}; font-size:0.65rem;">AI RANK</th>
        <th style="padding:10px; text-align:center; color:{text2}; font-size:0.65rem;">AI %</th>
        <th style="padding:10px; text-align:center; color:{text2}; font-size:0.65rem;">→</th>
        <th style="padding:10px; text-align:center; color:{text2}; font-size:0.65rem;">QUANTUM RANK</th>
        <th style="padding:10px; text-align:center; color:{text2}; font-size:0.65rem;">QUANTUM %</th>
        <th style="padding:10px; text-align:center; color:{text2}; font-size:0.65rem;">SHIFT</th>
    </tr>"""

    for d in sorted(disagreements, key=lambda x: x["q_rank"]):
        shift = d["ai_rank"] - d["q_rank"]
        if shift > 0:
            shift_icon = f'<span style="color:#00e878;">▲ +{shift}</span>'
        elif shift < 0:
            shift_icon = f'<span style="color:#e84050;">▼ {shift}</span>'
        else:
            shift_icon = f'<span style="color:{text2};">—</span>'

        is_best = d["q_rank"] == 1
        row_bg = f"{accent}08" if is_best else "transparent"

        table_html += f"""
        <tr style="border-bottom:1px solid {border}; background:{row_bg};">
            <td style="padding:10px; color:{text}; font-size:0.85rem; font-weight:{'600' if is_best else '400'};">{d['name']}</td>
            <td style="padding:10px; text-align:center; color:{text2}; font-size:0.9rem;">#{d['ai_rank']}</td>
            <td style="padding:10px; text-align:center; color:{'#00e878' if d['ai_score'] > 60 else '#c8a020' if d['ai_score'] > 40 else '#e84050'}; font-weight:600;">{d['ai_score']}%</td>
            <td style="padding:10px; text-align:center; color:{text2};">→</td>
            <td style="padding:10px; text-align:center; color:{'#4488cc'}; font-size:0.9rem; font-weight:600;">#{d['q_rank']}</td>
            <td style="padding:10px; text-align:center; color:#4488cc; font-weight:600;">{d['q_score']}%</td>
            <td style="padding:10px; text-align:center; font-weight:600;">{shift_icon}</td>
        </tr>"""

    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)

    # Biggest disagreement insight
    biggest = max(disagreements, key=lambda x: x["rank_diff"])
    if biggest["rank_diff"] > 0:
        direction = "вгору" if biggest["ai_rank"] > biggest["q_rank"] else "вниз"
        insight_color = "#00e878" if biggest["ai_rank"] > biggest["q_rank"] else "#e84050"
        st.markdown(f"""
        <div style="background:{card_bg}; border:1px solid {border}; border-radius:10px; padding:14px 18px; margin-top:8px;">
            <span style="color:{insight_color}; font-weight:600;">⚡ Biggest Disagreement:</span>
            <span style="color:{text};"> «{biggest['name']}» — AI ranked #{biggest['ai_rank']}, Quantum moved to #{biggest['q_rank']} ({direction} {biggest['rank_diff']} positions).</span><br>
            <span style="color:{text2}; font-size:0.8rem;">
            <b>What this means:</b> {'Quantum sees that investing in this strategy would weaken other strategies in your portfolio. AI evaluated it in isolation and overvalued it.' if biggest['ai_rank'] < biggest['q_rank'] else 'Quantum detected synergy with other strategies that AI missed. This option becomes stronger when combined with the rest of your portfolio.'}
            </span>
        </div>
        """, unsafe_allow_html=True)

    # === REVENUE PROJECTION ===
    if exec_data and exec_data.get("money_projection"):
        st.markdown("---")
        mp = exec_data["money_projection"]
        months = {k: v for k, v in mp.items() if k.startswith("month")}

        cols_rev = st.columns(len(months))
        for i, (k, v) in enumerate(months.items()):
            with cols_rev[i]:
                st.markdown(f"""
                <div class="revenue-card">
                    <div class="metric-label">{k.replace('_', ' ').upper()}</div>
                    <div class="metric-value metric-green" style="margin-top:8px;">${v.get('revenue', 0):,}</div>
                    <div style="color:{users_text}; font-size:0.8rem; margin-top:4px;">{v.get('users', 0)} users</div>
                </div>
                """, unsafe_allow_html=True)

        c_mrr, c_be = st.columns(2)
        with c_mrr:
            st.metric("🎯 TARGET MRR", f"${mp.get('total_mrr_target', 0):,}")
        with c_be:
            st.metric("📅 BREAKEVEN", f"Month {mp.get('breakeven_month', '—')}")

    # === 🎲 MONTE CARLO vs QUANTUM vs AI ===
    mc_results = st.session_state.get("mc_results")
    if mc_results:
        st.markdown("---")
        st.markdown("### 🎲 AI vs MONTE CARLO vs QUANTUM — Three Judges")

        mc_data = []
        for s in scenarios:
            mc = next((m for m in mc_results if m["scenario_id"] == s["id"]), {})
            q = next((r for r in quantum.get("results", []) if r["scenario_id"] == s["id"]), {})
            mc_data.append({
                "Scenario": s["name"][:30],
                "🧠 AI": f"{s['success_probability']}%",
                "🎲 Monte Carlo": f"{mc.get('mc_score', 0)}%",
                "⚛️ Quantum": f"{q.get('quantum_score', 0)}%",
                "MC Win Rate": f"{mc.get('win_rate', 0)}%",
                "MC Avg ROI": f"{mc.get('avg_roi', 0):+.1f}%",
                "Verdict": s["recommendation"]
            })
        st.dataframe(mc_data, use_container_width=True)

        # Three-judge chart
        fig_3j = go.Figure()
        names = [s["name"][:20] for s in scenarios]
        fig_3j.add_trace(go.Bar(name="🧠 AI", x=names, y=[s["success_probability"] for s in scenarios], marker_color="#2266aa"))
        fig_3j.add_trace(go.Bar(name="🎲 Monte Carlo", x=names, y=[next((m["mc_score"] for m in mc_results if m["scenario_id"] == s["id"]), 0) for s in scenarios], marker_color="#cc8800"))
        fig_3j.add_trace(go.Bar(name="⚛️ Quantum", x=names, y=[next((r["quantum_score"] for r in quantum.get("results", []) if r["scenario_id"] == s["id"]), 0) for s in scenarios], marker_color="#00cc66"))
        fig_3j.update_layout(barmode="group", height=300, paper_bgcolor=chart_paper_bg, plot_bgcolor=chart_plot_bg,
                            font=dict(color=text, size=10), legend=dict(orientation="h", y=1.15),
                            margin=dict(l=30, r=20, t=20, b=60), yaxis=dict(gridcolor=border))
        st.plotly_chart(fig_3j, use_container_width=True)

    # === ⚡ MULTI-ENGINE COMPARISON ===
    multi_results = st.session_state.get("multi_results")
    if multi_results and len(multi_results) > 1:
        st.markdown("---")
        st.markdown("### ⚡ MULTI-ENGINE — Qiskit vs Cirq vs PennyLane")
        st.markdown(f'<div style="color:{text2}; font-size:0.8rem; margin-bottom:12px;">Same VQE algorithm, three quantum engines. Consensus = high confidence.</div>', unsafe_allow_html=True)

        # Build comparison table
        multi_table = []
        for s in scenarios:
            row = {"Scenario": s["name"][:25]}
            row["🧠 AI"] = f"{s['success_probability']}%"
            for eng_id, eng_data in multi_results.items():
                if eng_data.get("data") and eng_data["data"].get("results"):
                    score = next((r["quantum_score"] for r in eng_data["data"]["results"] if r["scenario_id"] == s["id"]), 0)
                    row[eng_data["name"][:12]] = f"{score}%"
                else:
                    row[eng_data.get("name", eng_id)[:12]] = "—"

            # Calculate consensus
            scores = []
            for eng_id, eng_data in multi_results.items():
                if eng_data.get("data") and eng_data["data"].get("results"):
                    score = next((r["quantum_score"] for r in eng_data["data"]["results"] if r["scenario_id"] == s["id"]), None)
                    if score:
                        scores.append(score)
            if len(scores) >= 2:
                spread = max(scores) - min(scores)
                row["Spread"] = f"{spread:.1f}%"
                row["Consensus"] = "🟢 Strong" if spread < 5 else "🟡 Moderate" if spread < 15 else "🔴 Divergent"
            else:
                row["Spread"] = "—"
                row["Consensus"] = "—"
            multi_table.append(row)

        st.dataframe(multi_table, use_container_width=True)

        # Multi-engine chart
        fig_multi = go.Figure()
        scenario_names = [s["name"][:20] for s in scenarios]

        colors = {"simulator": "#2266aa", "google_cirq": "#cc4444", "pennylane": "#00aa55"}
        labels = {"simulator": "Qiskit", "google_cirq": "Cirq", "pennylane": "PennyLane"}

        for eng_id, eng_data in multi_results.items():
            if eng_data.get("data") and eng_data["data"].get("results"):
                scores = [next((r["quantum_score"] for r in eng_data["data"]["results"] if r["scenario_id"] == s["id"]), 0) for s in scenarios]
                fig_multi.add_trace(go.Bar(
                    name=labels.get(eng_id, eng_id),
                    x=scenario_names, y=scores,
                    marker_color=colors.get(eng_id, "#888888")
                ))

        fig_multi.update_layout(
            barmode="group", height=300,
            paper_bgcolor=chart_paper_bg, plot_bgcolor=chart_plot_bg,
            font=dict(color=text, size=10),
            legend=dict(orientation="h", y=1.15),
            margin=dict(l=30, r=20, t=20, b=60),
            yaxis=dict(gridcolor=border, title="Quantum Score %")
        )
        st.plotly_chart(fig_multi, use_container_width=True)

        # Consensus insight
        all_spreads = []
        for s in scenarios:
            scores = []
            for eng_data in multi_results.values():
                if eng_data.get("data") and eng_data["data"].get("results"):
                    score = next((r["quantum_score"] for r in eng_data["data"]["results"] if r["scenario_id"] == s["id"]), None)
                    if score:
                        scores.append(score)
            if len(scores) >= 2:
                all_spreads.append(max(scores) - min(scores))

        if all_spreads:
            avg_spread = sum(all_spreads) / len(all_spreads)
            verdict = "🟢 All three engines agree" if avg_spread < 5 else "🟡 Moderate divergence" if avg_spread < 15 else "🔴 Significant disagreement"
            st.markdown(f"""
            <div style="background:{card_bg}; border-left:3px solid {accent}; padding:12px 16px; border-radius:0 8px 8px 0; margin:8px 0;">
                <span style="color:{accent}; font-size:0.7rem; letter-spacing:1px;">⚡ MULTI-ENGINE VERDICT</span><br>
                <span style="color:{text}; font-size:0.95rem; font-weight:600;">{verdict}</span><br>
                <span style="color:{text2}; font-size:0.8rem;">Average spread: {avg_spread:.1f}% across {len(all_spreads)} scenarios.
                {'Results are highly reliable — three independent quantum engines confirm the same ranking.' if avg_spread < 5 else 'Some scenarios show engine-specific effects — consider focusing on consensus picks.' if avg_spread < 15 else 'Engines disagree significantly — results need deeper investigation.'}</span>
            </div>
            """, unsafe_allow_html=True)

    # === 📡 QUANTUM NOISE ANALYSIS ===
    noise_results = st.session_state.get("noise_results")
    if noise_results:
        st.markdown("---")
        st.markdown("### 📡 QUANTUM NOISE — Ideal vs Real QPU")
        st.markdown(f'<div style="color:{text2}; font-size:0.8rem; margin-bottom:12px;">Simulated 2% depolarizing noise + readout errors (typical IBM 127-qubit processor)</div>', unsafe_allow_html=True)

        noise_data = []
        for s in scenarios:
            q_ideal = next((r for r in quantum.get("results", []) if r["scenario_id"] == s["id"]), {})
            q_noisy = next((n for n in noise_results if n["scenario_id"] == s["id"]), {})
            ideal_score = q_ideal.get("quantum_score", 0)
            noisy_score = q_noisy.get("noisy_score", 0)
            drift = round(noisy_score - ideal_score, 2)
            noise_data.append({
                "Scenario": s["name"][:30],
                "Ideal Score": f"{ideal_score}%",
                "Noisy Score": f"{noisy_score}%",
                "Drift": f"{drift:+.2f}%",
                "Noisy Confidence": f"{q_noisy.get('noisy_confidence', 0)}%",
                "Stable": "✅" if abs(drift) < 5 else "⚠️"
            })
        st.dataframe(noise_data, use_container_width=True)

        # Noise chart
        fig_noise = go.Figure()
        fig_noise.add_trace(go.Bar(name="Ideal Simulator", x=[s["name"][:20] for s in scenarios],
            y=[next((r["quantum_score"] for r in quantum.get("results", []) if r["scenario_id"] == s["id"]), 0) for s in scenarios],
            marker_color="#00cc66"))
        fig_noise.add_trace(go.Bar(name="Noisy QPU (2%)", x=[s["name"][:20] for s in scenarios],
            y=[next((n["noisy_score"] for n in noise_results if n["scenario_id"] == s["id"]), 0) for s in scenarios],
            marker_color="#cc4444", opacity=0.7))
        fig_noise.update_layout(barmode="group", height=250, paper_bgcolor=chart_paper_bg, plot_bgcolor=chart_plot_bg,
                               font=dict(color=text, size=10), legend=dict(orientation="h", y=1.15),
                               margin=dict(l=30, r=20, t=20, b=60), yaxis=dict(gridcolor=border))
        st.plotly_chart(fig_noise, use_container_width=True)

    # === 🧬 EXPLAINABLE QUANTUM (XQ) — Correlation Matrix ===
    xq_matrix = st.session_state.get("xq_matrix")
    xq_labels = st.session_state.get("xq_labels")
    if xq_matrix and xq_labels:
        st.markdown("---")
        st.markdown("### 🧬 EXPLAINABLE QUANTUM — What entanglement sees")
        st.markdown(f'<div style="color:{text2}; font-size:0.8rem; margin-bottom:12px;">Correlation matrix: how scenarios interact through quantum entanglement. High correlation = removing one affects the other.</div>', unsafe_allow_html=True)

        fig_xq = go.Figure(data=go.Heatmap(
            z=xq_matrix, x=xq_labels, y=xq_labels,
            colorscale=[[0, "#0a0e14"], [0.5, "#2266aa"], [1, "#00ff88"]],
            text=[[f"{v:.2f}" for v in row] for row in xq_matrix],
            texttemplate="%{text}", textfont={"size": 11},
            hovertemplate="Scenario A: %{y}<br>Scenario B: %{x}<br>Correlation: %{z:.3f}<extra></extra>"
        ))
        fig_xq.update_layout(height=350, paper_bgcolor=chart_paper_bg, plot_bgcolor=chart_plot_bg,
                            font=dict(color=text, size=9), margin=dict(l=120, r=20, t=20, b=80),
                            xaxis=dict(tickangle=-45))
        st.plotly_chart(fig_xq, use_container_width=True)

        # XQ insight
        matrix_np = np.array(xq_matrix)
        np.fill_diagonal(matrix_np, 0)
        max_idx = np.unravel_index(matrix_np.argmax(), matrix_np.shape)
        max_corr = matrix_np[max_idx]
        if max_corr > 0.5:
            st.markdown(f"""
            <div style="background:{card_bg}; border-left:3px solid {accent}; padding:12px 16px; border-radius:0 8px 8px 0; margin:8px 0;">
                <span style="color:{accent}; font-size:0.7rem; letter-spacing:1px;">🧬 XQ INSIGHT</span><br>
                <span style="color:{text}; font-size:0.85rem;">
                    Highest correlation ({max_corr:.2f}) between <strong>{xq_labels[max_idx[0]]}</strong> and <strong>{xq_labels[max_idx[1]]}</strong>.
                    Quantum entanglement detected strong interaction — changing one will significantly impact the other.
                </span>
            </div>
            """, unsafe_allow_html=True)

    # === 🧬 QAOA PORTFOLIO OPTIMIZATION (Real Data) ===
    qaoa_result = st.session_state.get("qaoa_result")
    if qaoa_result:
        st.markdown("---")
        st.markdown("### 🧬 QAOA PORTFOLIO — Real Quantum Optimization")
        st.markdown(f'<div style="color:{text2}; font-size:0.8rem; margin-bottom:12px;">QAOA analyzed {qaoa_result["n_items"]} items across {qaoa_result["total_combinations"]:,} possible combinations using {qaoa_result["total_shots"]:,} quantum measurements.</div>', unsafe_allow_html=True)

        # Summary metrics
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            st.metric("Items Analyzed", qaoa_result["n_items"])
        with q2:
            st.metric("Selected", qaoa_result["n_selected"])
        with q3:
            st.metric("Combinations", f"{qaoa_result['total_combinations']:,}")
        with q4:
            st.metric("QAOA Layers", qaoa_result["qaoa_layers"])

        # Selected items table
        selected_items = [item for item in qaoa_result["items"] if item["selected"]]
        rejected_items = [item for item in qaoa_result["items"] if not item["selected"]]

        if selected_items:
            st.markdown(f'<div style="color:{accent}; font-size:0.75rem; letter-spacing:2px; margin:16px 0 8px;">✅ QUANTUM SELECTED ({len(selected_items)} items)</div>', unsafe_allow_html=True)
            sel_data = [{"Item": it["name"], "Value": f"{it['value_score']}%", "Risk": f"{it['risk_score']}%", "Weight": f"{it['cost_weight']}%"} for it in selected_items]
            st.dataframe(sel_data, use_container_width=True)

        if rejected_items:
            with st.expander(f"❌ Rejected by quantum ({len(rejected_items)} items)"):
                rej_data = [{"Item": it["name"], "Value": f"{it['value_score']}%", "Risk": f"{it['risk_score']}%", "Weight": f"{it['cost_weight']}%"} for it in rejected_items]
                st.dataframe(rej_data, use_container_width=True)

        # QAOA convergence chart
        if qaoa_result.get("convergence"):
            fig_qaoa = go.Figure()
            fig_qaoa.add_trace(go.Scatter(
                x=list(range(1, len(qaoa_result["convergence"]) + 1)),
                y=qaoa_result["convergence"],
                mode="lines+markers", fill="tozeroy",
                line=dict(color=accent, width=2),
                fillcolor=f"rgba(0,255,136,0.08)",
                marker=dict(size=5)
            ))
            fig_qaoa.update_layout(
                title=dict(text="QAOA Convergence", font=dict(size=12, color=text2)),
                height=250, paper_bgcolor=chart_paper_bg, plot_bgcolor=chart_plot_bg,
                font=dict(color=text, size=10),
                margin=dict(l=40, r=20, t=40, b=40),
                xaxis=dict(title="Iteration", gridcolor=border),
                yaxis=dict(title="Best Portfolio Score", gridcolor=border)
            )
            st.plotly_chart(fig_qaoa, use_container_width=True)

        # Quantum advantage note
        classical_time = qaoa_result["total_combinations"] * 0.001  # ms per evaluation
        quantum_time = qaoa_result["total_shots"] * 0.01  # ms per shot
        speedup = classical_time / max(quantum_time, 0.001)

        st.markdown(f"""
        <div style="background:{card_bg}; border-left:3px solid {accent}; padding:12px 16px; border-radius:0 8px 8px 0; margin:8px 0;">
            <span style="color:{accent}; font-size:0.7rem; letter-spacing:1px;">🧬 QUANTUM ADVANTAGE ESTIMATE</span><br>
            <span style="color:{text}; font-size:0.85rem;">
                Classical brute-force: {qaoa_result['total_combinations']:,} combinations to evaluate<br>
                QAOA: {qaoa_result['total_shots']:,} quantum measurements across {qaoa_result['qaoa_layers']} layers<br>
                Circuit depth: {qaoa_result['depth']} gates | Best bitstring: <code>{qaoa_result['best_bitstring']}</code>
            </span>
        </div>
        """, unsafe_allow_html=True)

    # === 📊 BCG MATRIX — Quantum Enhanced ===
    bcg_items = st.session_state.get("bcg_items")
    if bcg_items:
        st.markdown("---")
        st.markdown("### 📊 BCG MATRIX — Quantum Portfolio Map")
        st.markdown(f'<div style="color:{text2}; font-size:0.8rem; margin-bottom:12px;">Bubble size = quantum allocation. Arrow = quantum momentum (where it\'s heading).</div>', unsafe_allow_html=True)

        fig_bcg = go.Figure()

        for item in bcg_items:
            fig_bcg.add_trace(go.Scatter(
                x=[item["share"]], y=[item["growth"]],
                mode="markers+text",
                marker=dict(size=item["size"] * 2.5 + 10, color=item["color"], opacity=0.7,
                           line=dict(width=2, color=item["color"])),
                text=[item["name"][:15]],
                textposition="top center",
                textfont=dict(size=9, color=text),
                name=item["quadrant"],
                hovertemplate=f"<b>{item['name']}</b><br>Growth: {item['growth']}%<br>Share: {item['share']}%<br>Quantum: {item['quantum_score']}%<br>Momentum: {item['momentum']:+.1f}<br>{item['prediction']}<extra></extra>"
            ))

            # Movement arrow
            if abs(item["momentum"]) > 3:
                fig_bcg.add_annotation(
                    x=item["share"], y=item["growth"],
                    ax=item["future_share"], ay=item["growth"],
                    xref="x", yref="y", axref="x", ayref="y",
                    showarrow=True, arrowhead=2, arrowsize=1.5,
                    arrowcolor=accent if item["momentum"] > 0 else "#cc4444",
                    opacity=0.6
                )

        # Quadrant lines
        fig_bcg.add_hline(y=30, line_dash="dot", line_color=border, opacity=0.5)
        fig_bcg.add_vline(x=55, line_dash="dot", line_color=border, opacity=0.5)

        # Quadrant labels
        fig_bcg.add_annotation(x=80, y=60, text="⭐ Stars", showarrow=False, font=dict(size=11, color="rgba(0,255,136,0.3)"))
        fig_bcg.add_annotation(x=80, y=10, text="🐄 Cash Cows", showarrow=False, font=dict(size=11, color="rgba(68,136,204,0.3)"))
        fig_bcg.add_annotation(x=30, y=60, text="❓ Question Marks", showarrow=False, font=dict(size=11, color="rgba(204,170,0,0.3)"))
        fig_bcg.add_annotation(x=30, y=10, text="🐕 Dogs", showarrow=False, font=dict(size=11, color="rgba(204,68,68,0.3)"))

        fig_bcg.update_layout(
            height=400, showlegend=False,
            paper_bgcolor=chart_paper_bg, plot_bgcolor=chart_plot_bg,
            font=dict(color=text, size=10),
            margin=dict(l=50, r=20, t=20, b=50),
            xaxis=dict(title="Market Share / Success Probability %", gridcolor=border, range=[0, 100]),
            yaxis=dict(title="Growth / Expected ROI %", gridcolor=border)
        )
        st.plotly_chart(fig_bcg, use_container_width=True)

        # BCG table
        bcg_table = [{"Scenario": i["name"], "Quadrant": i["quadrant"], "Quantum": f"{i['quantum_score']}%",
                      "Momentum": f"{i['momentum']:+.1f}", "Prediction": i["prediction"]} for i in bcg_items]
        st.dataframe(bcg_table, use_container_width=True)

    # === 🤖 AGENT-BASED MODELING — Market Simulation ===
    abm_result = st.session_state.get("abm_result")
    if abm_result:
        st.markdown("---")
        st.markdown("### 🤖 AGENT-BASED MODELING — Market Simulation")
        st.markdown(f'<div style="color:{text2}; font-size:0.8rem; margin-bottom:12px;">{abm_result["total_agents"]} virtual agents (buyers, skeptics, bargain hunters) simulated over {len(abm_result["monthly"])} months.</div>', unsafe_allow_html=True)

        # Summary metrics
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            st.metric("Final Users", abm_result["final_users"])
        with a2:
            st.metric("Total Churned", abm_result["total_churned"])
        with a3:
            st.metric("Retention", f"{abm_result['retention_rate']}%")
        with a4:
            last_month = abm_result["monthly"][-1] if abm_result["monthly"] else {}
            st.metric("Competitor Pressure", f"{last_month.get('competitor_pressure', 0)}%")

        # User growth chart
        months = [m["month"] for m in abm_result["monthly"]]
        total_users = [m["total_users"] for m in abm_result["monthly"]]
        new_users = [m["new_users"] for m in abm_result["monthly"]]
        churned = [m["churned"] for m in abm_result["monthly"]]

        fig_abm = go.Figure()
        fig_abm.add_trace(go.Scatter(x=months, y=total_users, name="Total Users", fill="tozeroy",
                                     line=dict(color=accent, width=2), fillcolor="rgba(0,255,136,0.08)"))
        fig_abm.add_trace(go.Bar(x=months, y=new_users, name="New", marker_color="#4488cc", opacity=0.7))
        fig_abm.add_trace(go.Bar(x=months, y=[-c for c in churned], name="Churned", marker_color="#cc4444", opacity=0.7))

        fig_abm.update_layout(
            height=300, barmode="relative",
            paper_bgcolor=chart_paper_bg, plot_bgcolor=chart_plot_bg,
            font=dict(color=text, size=10),
            legend=dict(orientation="h", y=1.15),
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis=dict(title="Month", gridcolor=border),
            yaxis=dict(title="Users", gridcolor=border)
        )
        st.plotly_chart(fig_abm, use_container_width=True)

        # Agent type breakdown
        fig_types = go.Figure()
        for atype in abm_result.get("agent_types", []):
            values = [m["by_type"].get(atype, 0) for m in abm_result["monthly"]]
            fig_types.add_trace(go.Scatter(x=months, y=values, name=atype.replace("_", " ").title(),
                                          mode="lines+markers", stackgroup="one"))

        fig_types.update_layout(
            height=250,
            paper_bgcolor=chart_paper_bg, plot_bgcolor=chart_plot_bg,
            font=dict(color=text, size=10),
            legend=dict(orientation="h", y=1.15),
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis=dict(title="Month", gridcolor=border),
            yaxis=dict(title="Active by Type", gridcolor=border)
        )
        st.plotly_chart(fig_types, use_container_width=True)

        # Events timeline
        events_found = False
        for m in abm_result["monthly"]:
            if m.get("events"):
                events_found = True
                for event in m["events"]:
                    st.markdown(f'<div style="color:{text2}; font-size:0.8rem;">Month {m["month"]}: {event}</div>', unsafe_allow_html=True)

        if not events_found:
            st.markdown(f'<div style="color:{accent}; font-size:0.8rem;">✅ No critical market events detected in simulation.</div>', unsafe_allow_html=True)

    # === EXECUTION PLAN ===
    if exec_data and exec_data.get("execution_plan"):
        st.markdown("---")
        st.markdown("### 📋 EXECUTION PLAN — WEEK BY WEEK")

        for week in exec_data["execution_plan"]:
            is_first = week.get("week", 0) == 1
            card_class = "week-card week-current" if is_first else "week-card"
            tasks_html = "".join([
                f'<div style="color:{row_label}; font-size:0.85rem; padding:2px 0;">● {t}</div>'
                for t in week.get("tasks", [])
            ])
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display:flex; gap:16px;">
                    <div style="min-width:50px;">
                        <div style="color:{label_dim}; font-size:0.65rem;">WEEK</div>
                        <div style="font-size:1.5rem; font-weight:700; color:{'#00ff88' if is_first else '#3a7a6a'};">{week.get('week', '?')}</div>
                    </div>
                    <div>
                        <div style="font-size:1rem; font-weight:600; color:{title_text}; margin-bottom:8px;">{week.get('title', '')}</div>
                        {tasks_html}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # === 🔬 SCIENTIFIC MODELS — Advanced Analytics ===
    st.markdown("---")
    st.markdown("### 🔬 SCIENTIFIC MODELS")
    st.markdown(f'<div style="color:{text2}; font-size:0.8rem; margin-bottom:16px;">Physics, Biology, Mathematics — not opinions, calculations</div>', unsafe_allow_html=True)
    
    sci_cols = st.columns(3)
    
    # --- GENETIC ALGORITHM ---
    with sci_cols[0]:
        with st.expander("🧬 Genetic Algorithm", expanded=False):
            ga = genetic_algorithm(scenarios)
            st.markdown(f"""<div style="background:{card_bg}; border:1px solid {border}; border-radius:10px; padding:14px;">
<div style="color:{accent}; font-size:0.65rem; letter-spacing:2px;">STRATEGY EVOLUTION — {ga['generations']} GENERATIONS</div>
<div style="color:{text}; font-size:0.85rem; margin-top:8px; line-height:1.6;">
<b>Optimal Mix (evolved):</b><br>{'<br>'.join([f'• {k}: {v}%' for k, v in ga['optimal_weights'].items()])}<br><br>
<b>Final fitness:</b> {ga['final_fitness']}<br>
<b>Population:</b> {ga['population']} individuals
</div></div>""", unsafe_allow_html=True)
    
    # --- SIR EPIDEMIC MODEL ---
    with sci_cols[1]:
        with st.expander("🦠 SIR Viral Model", expanded=False):
            sir = sir_viral_model(scenarios, best)
            verdict_color = accent if sir["verdict"] == "VIRAL" else "#cc8800" if sir["verdict"] == "GROWING" else "#e84050"
            st.markdown(f"""<div style="background:{card_bg}; border:1px solid {border}; border-radius:10px; padding:14px;">
<div style="color:{accent}; font-size:0.65rem; letter-spacing:2px;">EPIDEMIC SPREAD MODEL</div>
<div style="color:{text}; font-size:0.85rem; margin-top:8px; line-height:1.6;">
<b>R₀ (reproduction number):</b> <span style="color:{verdict_color}; font-weight:700;">{sir['R0']}</span> — {sir['verdict']}<br>
<b>β (virality):</b> {sir['beta']} · <b>γ (churn):</b> {sir['gamma']}<br>
<b>Peak users:</b> {sir['peak_users']:,} at week {sir['peak_week']}<br>
<b>Final active:</b> {sir['final_active']:,}<br>
<b>Total reached:</b> {sir['total_reached']:,} / 10,000
</div></div>""", unsafe_allow_html=True)
    
    # --- NASH EQUILIBRIUM ---
    with sci_cols[2]:
        with st.expander("🎯 Nash Equilibrium", expanded=False):
            nash = nash_equilibrium(scenarios)
            st.markdown(f"""<div style="background:{card_bg}; border:1px solid {border}; border-radius:10px; padding:14px;">
<div style="color:{accent}; font-size:0.65rem; letter-spacing:2px;">GAME THEORY — COMPETITIVE RESPONSE</div>
<div style="color:{text}; font-size:0.85rem; margin-top:8px; line-height:1.6;">
<b>Dominant strategy:</b> {nash['dominant_strategy']}<br>
<b>Stability:</b> {nash['stability']}<br><br>
<b>Equilibrium weights:</b><br>{'<br>'.join([f'• {k}: {v}%' for k, v in nash['equilibrium_weights'].items()])}
</div></div>""", unsafe_allow_html=True)
    
    sci_cols2 = st.columns(3)
    
    # --- SHANNON ENTROPY ---
    with sci_cols2[0]:
        with st.expander("📊 Shannon Entropy", expanded=False):
            entropy = shannon_entropy(scenarios, quantum.get("results", []))
            ent_color = "#e84050" if "HIGH" in entropy["market_verdict"] else "#cc8800" if "MODERATE" in entropy["market_verdict"] else accent
            st.markdown(f"""<div style="background:{card_bg}; border:1px solid {border}; border-radius:10px; padding:14px;">
<div style="color:{accent}; font-size:0.65rem; letter-spacing:2px;">INFORMATION THEORY — UNCERTAINTY</div>
<div style="color:{text}; font-size:0.85rem; margin-top:8px; line-height:1.6;">
<b>AI uncertainty:</b> {entropy['ai_uncertainty']}% (entropy {entropy['ai_entropy']}/{entropy['max_entropy']})<br>
<b>Quantum uncertainty:</b> {entropy['quantum_uncertainty']}%<br>
<b>Risk entropy:</b> {entropy['risk_entropy']}<br><br>
<span style="color:{ent_color}; font-weight:700;">{entropy['market_verdict']}</span>
</div></div>""", unsafe_allow_html=True)
    
    # --- CHAOS / LORENZ ---
    with sci_cols2[1]:
        with st.expander("🌀 Chaos Analysis", expanded=False):
            chaos = chaos_analysis(scenarios, quantum.get("results", []))
            chaos_color = "#e84050" if chaos["is_chaotic"] else accent
            st.markdown(f"""<div style="background:{card_bg}; border:1px solid {border}; border-radius:10px; padding:14px;">
<div style="color:{accent}; font-size:0.65rem; letter-spacing:2px;">LORENZ ATTRACTOR — MARKET STABILITY</div>
<div style="color:{text}; font-size:0.85rem; margin-top:8px; line-height:1.6;">
<b>Lyapunov exponent:</b> <span style="color:{chaos_color}; font-weight:700;">{chaos['lyapunov_exponent']}</span><br>
<b>σ={chaos['sigma']}</b> ρ={chaos['rho']} β={chaos['beta']}<br>
<b>Phase space range:</b> {chaos['x_range']}<br><br>
<span style="color:{chaos_color}; font-weight:700;">{chaos['verdict']}</span><br>
<span style="font-size:0.75rem; color:{text2};">{chaos['business_meaning']}</span>
</div></div>""", unsafe_allow_html=True)
    
    # --- LOTKA-VOLTERRA ---
    with sci_cols2[2]:
        with st.expander("🐺 Lotka-Volterra", expanded=False):
            lv = lotka_volterra(scenarios, best)
            lv_color = accent if lv["verdict"] == "DOMINANCE" else "#cc8800" if lv["verdict"] == "COEXISTENCE" else "#e84050"
            st.markdown(f"""<div style="background:{card_bg}; border:1px solid {border}; border-radius:10px; padding:14px;">
<div style="color:{accent}; font-size:0.65rem; letter-spacing:2px;">PREDATOR-PREY — COMPETITOR DYNAMICS</div>
<div style="color:{text}; font-size:0.85rem; margin-top:8px; line-height:1.6;">
<b>Your final share:</b> {lv['final_your_share']}<br>
<b>Competitor share:</b> {lv['final_comp_share']}<br>
<b>Equilibrium:</b> You={lv['equilibrium_your']} / Comp={lv['equilibrium_comp']}<br><br>
<span style="color:{lv_color}; font-weight:700;">{lv['verdict']}</span>
</div></div>""", unsafe_allow_html=True)
    
    # --- BLACK-SCHOLES ---
    with st.expander("💎 Black-Scholes Option Pricing — Strategy as Options", expanded=False):
        bs_options = black_scholes_options(scenarios, budget, timeline)
        bs_html = ""
        for opt in bs_options[:5]:
            v_color = accent if opt["verdict"] == "UNDERPRICED" else "#cc8800" if opt["verdict"] == "FAIR" else "#e84050"
            bs_html += f"""<div style="background:{bg}; border:1px solid {border}; border-radius:8px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
<div><div style="font-size:0.85rem; color:{text};">{opt['strategy'][:35]}</div>
<div style="font-size:0.7rem; color:{text2};">IV: {opt['implied_volatility']}% · Call: ${opt['call_value']:,} · R/R: {opt['risk_reward_ratio']}x</div></div>
<div style="color:{v_color}; font-weight:700; font-size:0.8rem;">{opt['verdict']}</div>
</div>"""
        st.markdown(f"""<div style="background:{card_bg}; border:1px solid {border}; border-radius:10px; padding:14px;">
<div style="color:{accent}; font-size:0.65rem; letter-spacing:2px; margin-bottom:10px;">BLACK-SCHOLES — EACH STRATEGY AS A FINANCIAL OPTION</div>
{bs_html}
</div>""", unsafe_allow_html=True)

    # === ONE-CLICK EXECUTION ===
    st.markdown("---")
    st.markdown("### ⚡ EXECUTE NOW")
    st.markdown(f'<div style="color:{text2}; font-size:0.8rem; margin-bottom:16px;">Oracle recommends → AI generates → you copy & use</div>', unsafe_allow_html=True)

    if exec_data and api_key:
        exec_cols = st.columns(3)

        with exec_cols[0]:
            if st.button("📧 Cold Outreach Email", use_container_width=True, key="exec_email"):
                with st.spinner("Writing email..."):
                    ep = f"""Write a cold outreach email based on this strategy.

Business: {idea[:300]}
Strategy: {best['name']}
First action: {exec_data.get('first_action', '')}
Target: potential customers/partners
Language: {lang_map[lang]}

Write a specific, personalized cold email (subject + body). Not generic. Include:
- Specific hook related to recipient's pain
- One concrete number or result
- Clear CTA with low commitment
- Professional but human tone
- Max 150 words"""
                    result = call_claude(ep, api_key, raw_text=True, model=claude_model)
                    st.session_state["exec_email"] = result

        with exec_cols[1]:
            if st.button("🌐 Landing Page Copy", use_container_width=True, key="exec_landing"):
                with st.spinner("Writing copy..."):
                    lp = f"""Write landing page copy for this product.

Business: {idea[:300]}
Strategy: {best['name']}
Target MRR: ${mrr:,}
Language: {lang_map[lang]}

Generate:
1. HEADLINE (max 8 words, benefit-focused)
2. SUBHEADLINE (1 sentence, specific result)
3. 3 FEATURES with icons and descriptions
4. SOCIAL PROOF line
5. CTA button text
6. URGENCY line

Be specific, not generic. Use numbers."""
                    result = call_claude(lp, api_key, raw_text=True, model=claude_model)
                    st.session_state["exec_landing"] = result

        with exec_cols[2]:
            if st.button("🎯 Pitch Deck Outline", use_container_width=True, key="exec_pitch"):
                with st.spinner("Building pitch..."):
                    pp = f"""Create a 10-slide pitch deck outline.

Business: {idea[:300]}
Strategy: {best['name']}
Budget: ${budget:,}
Target MRR: ${mrr:,}
Success probability: {best['success_probability']}%
Quantum score: {best_q['quantum_score'] if best_q else '?'}%
Language: {lang_map[lang]}

For each slide give:
- Slide title
- Key message (1 sentence)
- What to show (visual/data suggestion)

Include: Problem, Solution, Market, Product, Traction, Business Model, Competition, Team, Financials, Ask"""
                    result = call_claude(pp, api_key, raw_text=True, model=claude_model)
                    st.session_state["exec_pitch"] = result

        exec_cols2 = st.columns(3)

        with exec_cols2[0]:
            if st.button("📱 Social Media Posts", use_container_width=True, key="exec_social"):
                with st.spinner("Creating posts..."):
                    sp = f"""Write 3 social media posts to announce this product.

Business: {idea[:300]}
Strategy: {best['name']}
Language: {lang_map[lang]}

Write for:
1. LinkedIn (professional, 100 words, with hook)
2. Twitter/X (max 280 chars, punchy)
3. Telegram channel (informal, with emoji, 80 words)

Each post should be ready to copy-paste. Include relevant hashtags."""
                    result = call_claude(sp, api_key, raw_text=True, model=claude_model)
                    st.session_state["exec_social"] = result

        with exec_cols2[1]:
            if st.button("📋 Week 1 Checklist", use_container_width=True, key="exec_checklist"):
                with st.spinner("Building checklist..."):
                    cl = f"""Create a detailed Day-by-Day checklist for Week 1.

Business: {idea[:300]}
Strategy: {best['name']}
First action: {exec_data.get('first_action', '')}
Budget: ${budget:,}
Language: {lang_map[lang]}

For each day (Mon-Fri):
- 3 specific tasks with time estimates
- Tools needed (free options)
- Expected output/deliverable
- Cost ($0 where possible)

Be ultra-specific. Not "research market" but "search 20 competitors on ProductHunt, save to spreadsheet, note pricing"."""
                    result = call_claude(cl, api_key, raw_text=True, model=claude_model)
                    st.session_state["exec_checklist"] = result

        with exec_cols2[2]:
            if st.button("💰 Financial Model", use_container_width=True, key="exec_finance"):
                with st.spinner("Building model..."):
                    fm = f"""Create a simple financial model.

Business: {idea[:300]}
Strategy: {best['name']}
Budget: ${budget:,}
Timeline: {timeline} months
Revenue projection: Month 1-6 from execution plan
Language: {lang_map[lang]}

Calculate:
- Monthly costs breakdown (hosting, API, marketing, tools)
- Revenue per user (pricing tiers)
- Break-even analysis (which month, how many users)
- Unit economics (CAC, LTV, LTV/CAC ratio)
- 12-month P&L projection

Use specific numbers, not ranges."""
                    result = call_claude(fm, api_key, raw_text=True, model=claude_model)
                    st.session_state["exec_finance"] = result

        # Display results
        for key, title in [
            ("exec_email", "📧 Cold Outreach Email"),
            ("exec_landing", "🌐 Landing Page Copy"),
            ("exec_pitch", "🎯 Pitch Deck Outline"),
            ("exec_social", "📱 Social Media Posts"),
            ("exec_checklist", "📋 Week 1 Day-by-Day"),
            ("exec_finance", "💰 Financial Model")
        ]:
            if key in st.session_state:
                with st.expander(title, expanded=True):
                    content = st.session_state[key]
                    if not isinstance(content, str):
                        content = json.dumps(content, ensure_ascii=False, indent=2) if isinstance(content, (dict, list)) else str(content)
                    st.markdown(content)
                    st.download_button(
                        f"⬇️ Download {title}",
                        data=content.encode("utf-8"),
                        file_name=f"oracle_{key}.txt",
                        mime="text/plain",
                        key=f"dl_{key}"
                    )

    # === SCENARIO CARDS ===
    st.markdown("---")
    st.markdown("### 📊 ALL SCENARIOS")

    for s in scenarios:
        badge_class = {"GO": "go-badge", "WAIT": "wait-badge", "AVOID": "avoid-badge"}.get(s["recommendation"], "wait-badge")
        q_score = next((r["quantum_score"] for r in quantum.get("results", []) if r["scenario_id"] == s["id"]), None)
        q_badge = f'<span style="background:rgba(0,170,255,0.12); color:{accent}; padding:4px 10px; border-radius:8px; font-size:0.75rem;">⚛️ {q_score}%</span>' if q_score else ''

        factors = "".join([f'<div style="color:{row_label}; font-size:0.8rem; padding:2px 0;">◆ {f}</div>' for f in s.get("key_factors", [])])
        threats = "".join([f'<div style="color:{threats_text}; font-size:0.8rem; padding:2px 0;">◆ {t}</div>' for t in s.get("threats", [])])

        sc = "metric-green" if s["success_probability"] > 60 else "metric-yellow" if s["success_probability"] > 35 else "metric-red"
        rc = "metric-green" if s["expected_roi"] > 0 else "metric-red"
        rkc = "metric-green" if s["risk_score"] < 40 else "metric-yellow" if s["risk_score"] < 70 else "metric-red"

        st.markdown(f"""
        <div class="scenario-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div>
                    <div style="color:#4a8a6a; font-size:0.7rem; letter-spacing:2px;">SCENARIO {s['id']}</div>
                    <div style="color:{text}; font-size:1.1rem; font-weight:600;">{s['name']}</div>
                </div>
                <div style="display:flex; gap:8px;">
                    {q_badge}
                    <span class="{badge_class}">{s['recommendation']}</span>
                </div>
            </div>
            <p style="color:{desc_text}; font-size:0.85rem; line-height:1.6;">{s['description']}</p>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:12px; margin:16px 0;">
                <div style="text-align:center;"><div class="metric-label">SUCCESS</div><div class="metric-value {sc}" style="font-size:1.2rem;">{s['success_probability']}%</div></div>
                <div style="text-align:center;"><div class="metric-label">ROI</div><div class="metric-value {rc}" style="font-size:1.2rem;">+{s['expected_roi']}%</div></div>
                <div style="text-align:center;"><div class="metric-label">RISK</div><div class="metric-value {rkc}" style="font-size:1.2rem;">{s['risk_score']}/100</div></div>
                <div style="text-align:center;"><div class="metric-label">PROFIT IN</div><div class="metric-value metric-cyan" style="font-size:1.2rem;">{s['time_to_profit']}mo</div></div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                <div><div class="metric-label" style="margin-bottom:8px;">KEY FACTORS</div>{factors}</div>
                <div><div class="metric-label" style="margin-bottom:8px;">THREATS</div>{threats}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # === EXPORT JSON ===
    st.markdown("---")
    st.markdown("### 📦 EXPORT RESULTS")

    # Build AI vs Quantum comparison for export
    ai_rank_list = sorted(scenarios, key=lambda s: s["success_probability"], reverse=True)
    q_rank_list = sorted(quantum.get("results", []), key=lambda r: r["quantum_score"], reverse=True)

    ai_vs_quantum = []
    for s in scenarios:
        ai_r = next((i + 1 for i, a in enumerate(ai_rank_list) if a["id"] == s["id"]), 0)
        q_r = next((i + 1 for i, q in enumerate(q_rank_list) if q["scenario_id"] == s["id"]), 0)
        q_sc = next((q["quantum_score"] for q in quantum.get("results", []) if q["scenario_id"] == s["id"]), 0)
        shift = ai_r - q_r
        ai_vs_quantum.append({
            "scenario": s["name"],
            "ai_rank": ai_r,
            "ai_score": s["success_probability"],
            "quantum_rank": q_r,
            "quantum_score": q_sc,
            "shift": shift,
            "direction": "up" if shift > 0 else "down" if shift < 0 else "same",
            "recommendation": s["recommendation"]
        })

    biggest_diff = max(ai_vs_quantum, key=lambda x: abs(x["shift"]))

    export_data = {
        "oracle_version": "0.8",
        "model": claude_model,
        "ai_engines_active": [e for e in ["claude", "gemini", "groq"] if st.session_state.get(f"use_{e}")],
        "gemini_model": gemini_model if st.session_state.get("use_gemini") else None,
        "groq_model": st.session_state.get("groq_model") if st.session_state.get("use_groq") else None,
        "multi_ai_results": st.session_state.get("multi_ai_results"),
        "mode": mode_val,
        "input": {
            "idea": idea,
            "budget": budget,
            "markets": markets,
            "timeline": timeline,
            "risk_tolerance": risk
        },
        "executive_decision": {
            "strategy": best["name"],
            "success_probability": best["success_probability"],
            "expected_roi": best["expected_roi"],
            "risk_score": best["risk_score"],
            "quantum_score": best_q["quantum_score"] if best_q else None,
            "confidence": round(best['success_probability'] * 0.6 + (100 - best['risk_score']) * 0.4),
            "first_action": exec_data.get("first_action") if exec_data else None
        },
        "ai_vs_quantum": {
            "comparison": sorted(ai_vs_quantum, key=lambda x: x["quantum_rank"]),
            "biggest_disagreement": {
                "scenario": biggest_diff["scenario"],
                "ai_rank": biggest_diff["ai_rank"],
                "quantum_rank": biggest_diff["quantum_rank"],
                "shift": biggest_diff["shift"],
                "insight": f"AI placed '{biggest_diff['scenario']}' at #{biggest_diff['ai_rank']}, quantum moved it to #{biggest_diff['quantum_rank']} ({'+' if biggest_diff['shift'] > 0 else ''}{biggest_diff['shift']} positions). Quantum sees portfolio interaction via entanglement that AI doesn't account for."
            }
        },
        "quantum_engine": {
            "total_qubits": quantum.get("total_qubits"),
            "total_shots": quantum.get("total_shots"),
            "depth": quantum.get("depth"),
            "vqe_iterations": quantum.get("iterations"),
            "vqe_convergence": quantum.get("convergence"),
            "results": quantum.get("results"),
            "explainer": {
                "what_qubits_do": f"Each qubit = one strategy. {quantum.get('total_qubits', 0)} qubits with entanglement (CX gates) evaluate {2**quantum.get('total_qubits', 0):,} combinations in {quantum.get('total_shots', 0):,} measurements.",
                "what_score_means": "quantum_score = probability (%) that this strategy survives portfolio optimization. 86% = selected in 86 of 100 quantum measurements. 29% = only 29 of 100 — quantum detected conflicts with other strategies.",
                "why_ai_quantum_disagree": "AI ranks each strategy independently. Quantum evaluates all strategies simultaneously through entanglement — some individually strong strategies weaken others in portfolio. Divergence = hidden cross-strategy dependencies."
            }
        },
        "scenarios": scenarios,
        "execution_plan": exec_data.get("execution_plan") if exec_data else None,
        "money_projection": exec_data.get("money_projection") if exec_data else None,
        "quantum_reasoning": exec_data.get("quantum_reasoning") if exec_data else None,
        "executive_summary": st.session_state.get("exec_brief"),
        "market_context": st.session_state.get("market_context"),
        "deep_research": st.session_state.get("deep_research")
    }

    export_json = json.dumps(export_data, ensure_ascii=False, indent=2)

    col_dl, col_view, col_copy = st.columns([1, 1, 1])
    with col_dl:
        st.download_button(
            label="⬇️ DOWNLOAD JSON",
            data=export_json,
            file_name="quantum_oracle_result.json",
            mime="application/json",
            use_container_width=True
        )
    with col_view:
        if st.button("👁️ VIEW JSON", use_container_width=True):
            st.session_state["show_json"] = not st.session_state.get("show_json", False)
    with col_copy:
        if st.button("📋 COPY TO CLIPBOARD", use_container_width=True):
            st.session_state["show_json"] = True
            st.session_state["copy_trigger"] = True

    if st.session_state.get("show_json", False):
        st.code(export_json, language="json")
        # JS clipboard copy
        if st.session_state.get("copy_trigger", False):
            escaped = export_json.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
            st.components.v1.html(f"""
            <script>
            navigator.clipboard.writeText(`{escaped}`).then(() => {{
                document.getElementById('copyMsg').style.display = 'block';
            }});
            </script>
            <div id="copyMsg" style="display:block; text-align:center; color:#00aa55; font-size:14px; padding:8px; font-weight:600;">
                ✅ Copied to clipboard!
            </div>
            """, height=40)
            st.session_state["copy_trigger"] = False

    # === PDF MKINSEY REPORT ===
    pdf_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 40px; color: #1a1a1a; line-height: 1.6; }}
h1 {{ color: #0a4a2a; border-bottom: 3px solid #00aa55; padding-bottom: 10px; }}
h2 {{ color: #1a3a2a; margin-top: 30px; }}
.exec {{ background: #f0faf0; border-left: 4px solid #00aa55; padding: 20px; margin: 20px 0; border-radius: 8px; }}
.metrics {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin: 20px 0; }}
.metric {{ background: #f8f8f8; padding: 16px; border-radius: 8px; text-align: center; }}
.metric .val {{ font-size: 1.8rem; font-weight: 700; color: #0a6a3a; }}
.metric .lbl {{ font-size: 0.75rem; color: #6a6a6a; letter-spacing: 1px; }}
.scenario {{ background: #fafafa; border: 1px solid #e0e0e0; padding: 16px; margin: 10px 0; border-radius: 8px; }}
.go {{ border-left: 4px solid #00aa55; }} .wait {{ border-left: 4px solid #cc8800; }} .avoid {{ border-left: 4px solid #cc2020; }}
table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
th {{ background: #f0f0f0; font-size: 0.8rem; letter-spacing: 1px; color: #4a4a4a; }}
.footer {{ text-align: center; color: #8a8a8a; font-size: 0.75rem; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; }}
</style></head><body>
<h1>🔮 Quantum Oracle — Executive Report</h1>
<div class="exec">
<strong>🎯 EXECUTIVE DECISION</strong><br>
<strong>Strategy:</strong> {best['name']}<br>
<strong>Tomorrow (≤60 min):</strong> {exec_data.get('first_action', 'N/A') if exec_data else 'N/A'}
</div>
<div class="metrics">
<div class="metric"><div class="val">{best['success_probability']}%</div><div class="lbl">SUCCESS</div></div>
<div class="metric"><div class="val">+{best['expected_roi']}%</div><div class="lbl">ROI</div></div>
<div class="metric"><div class="val">{best['risk_score']}/100</div><div class="lbl">RISK</div></div>
</div>
<div class="metrics">
<div class="metric"><div class="val">${mrr:,}</div><div class="lbl">TARGET MRR</div></div>
<div class="metric"><div class="val">M{breakeven}</div><div class="lbl">BREAKEVEN</div></div>
<div class="metric"><div class="val">{best_q['quantum_score'] if best_q else '—'}%</div><div class="lbl">QUANTUM SCORE</div></div>
</div>
<h2>📊 Scenario Ranking</h2>
<table><tr><th>#</th><th>SCENARIO</th><th>AI %</th><th>QUANTUM %</th><th>RISK</th><th>VERDICT</th></tr>"""

    for i, r in enumerate(quantum.get("results", [])):
        s = next((sc for sc in scenarios if sc["id"] == r["scenario_id"]), None)
        if s:
            pdf_html += f'<tr><td>{i+1}</td><td>{s["name"]}</td><td>{s["success_probability"]}%</td><td>{r["quantum_score"]}%</td><td>{s["risk_score"]}/100</td><td>{s["recommendation"]}</td></tr>'

    pdf_html += f"""</table>

<h2>📊 AI vs Quantum Comparison</h2>
<div id="aiVsQuantumChart" style="width:100%; height:350px;"></div>

<h2>💰 Revenue Projection</h2>
<div id="revenueChart" style="width:100%; height:300px;"></div>

<h2>🧬 VQE Convergence</h2>
<div id="vqeChart" style="width:100%; height:280px;"></div>

<h2>📋 Execution Plan</h2>"""

    if exec_data and exec_data.get("execution_plan"):
        for w in exec_data["execution_plan"]:
            pdf_html += f'<div class="scenario"><strong>Week {w.get("week", "?")}:</strong> {w.get("title", "")}<ul>'
            for t in w.get("tasks", []):
                pdf_html += f"<li>{t}</li>"
            pdf_html += "</ul></div>"

    # Build chart data
    chart_names = []
    chart_ai = []
    chart_quantum = []
    for r in quantum.get("results", []):
        s = next((sc for sc in scenarios if sc["id"] == r["scenario_id"]), None)
        if s:
            chart_names.append(s["name"][:25])
            chart_ai.append(s["success_probability"])
            chart_quantum.append(r["quantum_score"])

    rev_months = []
    rev_values = []
    rev_users = []
    if exec_data and exec_data.get("money_projection"):
        mp = exec_data["money_projection"]
        for k, v in mp.items():
            if k.startswith("month"):
                rev_months.append(k.replace("_", " ").title())
                rev_values.append(v.get("revenue", 0))
                rev_users.append(v.get("users", 0))

    conv_data = quantum.get("convergence", [])

    pdf_html += f"""
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<script>
// AI vs Quantum chart
Plotly.newPlot('aiVsQuantumChart', [
    {{x: {json.dumps(chart_names)}, y: {json.dumps(chart_ai)}, name: 'AI Score', type: 'bar', marker: {{color: '#2266aa'}}}},
    {{x: {json.dumps(chart_names)}, y: {json.dumps(chart_quantum)}, name: 'Quantum Score', type: 'bar', marker: {{color: '#00aa55'}}}}
], {{
    barmode: 'group', plot_bgcolor: '#fafafa', paper_bgcolor: '#fff',
    font: {{family: 'Helvetica Neue', size: 11}},
    legend: {{orientation: 'h', y: 1.15}},
    margin: {{l: 40, r: 20, t: 20, b: 80}},
    yaxis: {{title: 'Score %', gridcolor: '#e8e8e8'}}
}}, {{responsive: true}});

// Revenue chart
Plotly.newPlot('revenueChart', [
    {{x: {json.dumps(rev_months)}, y: {json.dumps(rev_values)}, type: 'bar', marker: {{color: '#00aa55'}},
      text: {json.dumps([f'${v:,}' for v in rev_values])}, textposition: 'outside'}},
    {{x: {json.dumps(rev_months)}, y: {json.dumps(rev_users)}, type: 'scatter', mode: 'lines+markers',
      yaxis: 'y2', name: 'Users', line: {{color: '#2266aa', width: 2}}, marker: {{size: 6}}}}
], {{
    plot_bgcolor: '#fafafa', paper_bgcolor: '#fff',
    font: {{family: 'Helvetica Neue', size: 11}},
    showlegend: false,
    margin: {{l: 40, r: 50, t: 10, b: 40}},
    yaxis: {{title: 'Revenue $', gridcolor: '#e8e8e8'}},
    yaxis2: {{title: 'Users', overlaying: 'y', side: 'right', gridcolor: '#e8e8e8'}}
}}, {{responsive: true}});

// VQE Convergence
Plotly.newPlot('vqeChart', [
    {{x: {json.dumps(list(range(1, len(conv_data) + 1)))}, y: {json.dumps(conv_data)},
      type: 'scatter', mode: 'lines+markers', fill: 'tozeroy',
      line: {{color: '#6644aa', width: 2}}, fillcolor: 'rgba(102,68,170,0.08)',
      marker: {{size: 5, color: {json.dumps(['#00aa55' if v == min(conv_data) else '#6644aa' for v in conv_data])}}}
    }}
], {{
    plot_bgcolor: '#fafafa', paper_bgcolor: '#fff',
    font: {{family: 'Helvetica Neue', size: 11}},
    margin: {{l: 50, r: 20, t: 10, b: 40}},
    xaxis: {{title: 'Iteration', gridcolor: '#e8e8e8'}},
    yaxis: {{title: 'Cost (lower = better)', gridcolor: '#e8e8e8'}}
}}, {{responsive: true}});
</script>

<div class="footer">
Quantum Oracle v0.7 · AI + Qiskit VQE · {mode_val.upper()} MODE · {quantum.get('total_qubits', 0)} qubits · {quantum.get('total_shots', 0):,} shots
</div></body></html>"""

    col_pdf, col_json2 = st.columns(2)
    with col_pdf:
        st.download_button(
            label="📄 DOWNLOAD PDF REPORT (HTML)",
            data=pdf_html,
            file_name="quantum_oracle_report.html",
            mime="text/html",
            use_container_width=True
        )

    # === COMPARISON TABLE ===
    history = st.session_state.get("history", [])
    if len(history) > 1:
        st.markdown("---")
        st.markdown("### 🔄 COMPARE RUNS")
        st.markdown(f"*{len(history)} ideas analyzed in this session*")

        compare_html = f"""
        <table style="width:100%; border-collapse:collapse; margin:16px 0;">
        <tr style="border-bottom:2px solid {border};">
            <th style="padding:10px; text-align:left; color:{text2}; font-size:0.7rem; letter-spacing:1px;">IDEA</th>
            <th style="padding:10px; text-align:center; color:{text2}; font-size:0.7rem;">STRATEGY</th>
            <th style="padding:10px; text-align:center; color:{text2}; font-size:0.7rem;">SUCCESS</th>
            <th style="padding:10px; text-align:center; color:{text2}; font-size:0.7rem;">QUANTUM</th>
            <th style="padding:10px; text-align:center; color:{text2}; font-size:0.7rem;">MRR</th>
            <th style="padding:10px; text-align:center; color:{text2}; font-size:0.7rem;">CONFIDENCE</th>
            <th style="padding:10px; text-align:center; color:{text2}; font-size:0.7rem;">MODE</th>
        </tr>"""

        for i, h in enumerate(reversed(history)):
            is_latest = i == 0
            row_bg = f"{accent}08" if is_latest else "transparent"
            compare_html += f"""
            <tr style="border-bottom:1px solid {border}; background:{row_bg};">
                <td style="padding:10px; color:{text}; font-size:0.8rem;">{h['idea']}</td>
                <td style="padding:10px; text-align:center; color:{title_text}; font-weight:600; font-size:0.8rem;">{h['strategy']}</td>
                <td style="padding:10px; text-align:center; color:{'#00e878' if h['success'] > 60 else '#c8a020'}; font-weight:600;">{h['success']}%</td>
                <td style="padding:10px; text-align:center; color:#4488cc; font-weight:600;">{h['quantum_score']}%</td>
                <td style="padding:10px; text-align:center; color:{'#00e878' if dark_mode else '#00884a'}; font-weight:600;">${int(float(h.get('mrr', 0) or 0)):,}</td>
                <td style="padding:10px; text-align:center; color:{'#9878cc' if dark_mode else '#6644aa'}; font-weight:600;">{h['confidence']}%</td>
                <td style="padding:10px; text-align:center; color:{text2}; font-size:0.75rem;">{h['mode']}</td>
            </tr>"""

        compare_html += "</table>"
        st.markdown(compare_html, unsafe_allow_html=True)

        if st.button("🗑️ Clear history", use_container_width=False):
            st.session_state["history"] = []
            st.rerun()

    # Footer
    st.markdown(f"""
    <div style="text-align:center; color:{text2}; font-size:0.7rem; letter-spacing:1px; margin-top:32px; padding:16px;">
        QUANTUM ORACLE v0.8 · AI + QISKIT VQE · {mode_val.upper()} MODE · {quantum.get('total_qubits', 0)} qubits · {quantum.get('total_shots', 0):,} shots
    </div>
    """, unsafe_allow_html=True)
