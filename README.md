# 🔥 EdgeFire: AI-Powered Wildfire Detection & Prevention System

<p align="center">
  <b>Real-Time IoT Monitoring | AI Risk Prediction | Cloud-Based Alert System</b>
</p>

<p align="center">
  🌍 Protecting Forests | 🏭 Reducing Industrial Risk | ⚡ Enabling Smart Disaster Prevention
</p>

---

## 📌 Table of Contents

* [Overview](#-overview)
* [Live Deployment](#-live-deployment)
* [Problem Statement](#-problem-statement)
* [Solution Overview](#-solution-overview)
* [System Architecture](#-system-architecture)
* [Dashboard & Visualization](#-dashboard--visualization)
* [AI Model & Hugging Face Integration](#-ai-model--hugging-face-integration)
* [Tech Stack](#-tech-stack)
* [Hardware Components](#-hardware-components)
* [Working Pipeline](#-working-pipeline)
* [CSR & Industry Relevance](#-csr--industry-relevance)
* [Installation & Setup](#-installation--setup)
* [Project Structure](#-project-structure)
* [Results & Impact](#-results--impact)
* [Future Enhancements](#-future-enhancements)
* [Author](#-author)

---

## 🌍 Overview

**EdgeFire** is an intelligent wildfire detection and prevention system that integrates **IoT sensors, cloud computing, and machine learning** to detect and predict fire risks in real time.

The system continuously monitors:

* Temperature 🌡️
* Humidity 💧
* Gas/Smoke levels 🔥

It processes this data using AI models and generates **instant alerts and risk predictions**, enabling proactive intervention.

---

## 🚀 Live Deployment

* 🌐 **Streamlit Dashboard:**
  [https://your-streamlit-link.streamlit.app](https://hack-o-verse-wildfire-detection-system-mvp.streamlit.app/#incident-map)

* 🤗 **Hugging Face Model/API:**
  [https://huggingface.co/your-model-link](https://huggingface.co/spaces/shreyyans/hack-o-verse-wildfire-detection-mvp)

---

## 🚨 Problem Statement

Wildfires pose a significant threat globally:

* 🌲 Environmental destruction
* 🐾 Wildlife loss
* 💰 Economic damage
* ⚖️ Legal liability for industries

### Limitations of Existing Systems:

* Reactive (detect after fire spreads)
* Expensive infrastructure
* Lack of real-time intelligence

---

## 💡 Solution Overview

EdgeFire provides a **proactive and scalable solution**:

* 📡 IoT-based environmental sensing
* ☁️ Real-time cloud data storage
* 🤖 AI-driven fire risk prediction
* 🚨 Instant alert system
* 📊 Interactive dashboard

---

## 🏗️ System Architecture

```
[Sensors] → [ESP32] → [Firebase Cloud] → [AI Model (Hugging Face)] → [Dashboard + Alerts]
```

---

## 📊 Dashboard & Visualization

### 🔹 Real-Time Monitoring Dashboard

http://127.0.0.1:5500/index.html 


### Features:

* Live sensor readings
* Fire risk probability
* Alert indicators
* Historical trends

---

## 🤖 AI Model & Hugging Face Integration

The system integrates a machine learning model deployed on **Hugging Face** for scalable inference.

### 🔹 Model Inputs:

* Temperature
* Humidity
* Gas concentration

### 🔹 Model Output:

* Fire Risk Score (Low / Medium / High)

### 🔹 Example API Flow:

```
Sensor Data → Firebase → API Call → Hugging Face Model → Risk Prediction
```

## ⚙️ Tech Stack

### 🔹 Hardware

* ESP32 Microcontroller
* DHT11/DHT22 Sensor
* MQ Gas Sensor

### 🔹 Software

* Arduino IDE
* Firebase Realtime Database
* Streamlit (Dashboard)
* HTML, CSS, JavaScript

### 🔹 AI/ML

* Logistic Regression / Decision Tree
* Python (Model Training)
* Hugging Face Deployment

---

## 🔌 Hardware Components

| Component    | Description            |
| ------------ | ---------------------- |
| ESP32        | Microcontroller        |
| DHT Sensor   | Temperature & Humidity |
| MQ Sensor    | Gas/Smoke Detection    |
| Breadboard   | Circuit Assembly       |
| Jumper Wires | Connections            |

---

## 🔄 Working Pipeline

1. Sensors collect environmental data
2. ESP32 processes and sends data to Firebase
3. Firebase stores real-time data
4. Data is sent to AI model (Hugging Face API)
5. Model predicts fire risk
6. Dashboard displays results
7. Alerts are triggered if risk is high

---

## 🏢 CSR & Industry Relevance

Industries near forests (mining, timber, plantations) face:

* ⚖️ Legal liability
* 💰 Financial losses
* 📉 Reputation risks

### EdgeFire Enables:

* Early fire detection
* Risk reduction
* Compliance with environmental regulations
* Strong CSR positioning

---

## 🛠️ Installation & Setup

### 🔹 1. Hardware Setup

* Connect DHT → ESP32 (3.3V, GND, GPIO)
* Connect MQ Sensor → ESP32

---

### 🔹 2. ESP32 Setup

* Install Arduino IDE
* Add ESP32 board
* Upload firmware

---

### 🔹 3. Firebase Setup

* Create project
* Enable Realtime Database
* Add credentials

---

### 🔹 4. AI Model Setup

* Train model using Python
* Upload to Hugging Face
* Generate API endpoint

---

### 🔹 5. Streamlit Dashboard

```bash
pip install streamlit
streamlit run app.py
```

---

## 📁 Project Structure

```
EdgeFire/
│
├── assets/
│   └── dashboard.png
│
├── firmware/
│   └── esp32_code.ino
│
├── ml_model/
│   └── model.py
│
├── dashboard/
│   └── app.py
│
├── backend/
│   └── server.js
│
└── README.md
```

---

## 📈 Results & Impact

* ⏱️ Early fire detection
* 🔥 Reduced wildfire spread
* 💰 Cost-efficient solution
* 🌍 Environmental protection
* 🏭 Industry risk mitigation

---

## 🔮 Future Enhancements

* 🚁 Drone integration
* 🛰️ Satellite monitoring
* 📱 Mobile app
* 🤖 Deep learning models
* 🌐 Large-scale deployment

---

## 👩‍💻 Author

**Tanvi Dumbre**
B.Tech Computer Science Engineering

---

## ⭐ Contribution

Contributions are welcome!
Feel free to fork and improve this project.

---

## 📜 License

This project is intended for academic, research, and innovation purposes.
